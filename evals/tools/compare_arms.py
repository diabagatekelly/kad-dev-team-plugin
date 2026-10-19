#!/usr/bin/env python3
"""Blind judge between two arms of the same tdd case: heavy against lite (G2).

Takes two gate results of the same slice built by different skills (say
`gate-<ts>-tdd-implementation-cancel-hold.json` and
`gate-<ts>-tdd-implementation-lite-cancel-hold.json`), each run kept whole
with `eval_gate.py --keep-scaffold` so the run's working tree is still on
disk under its `scaffoldDir`, and asks the plugin's pairwise judge which
build is the better basis for the slice: every run of one arm against
every run of the other (or run i against run i with `--paired`), in both
presentation orders, every reason kept. The judge is the one the
orchestrator's Combine step uses (`skills/orchestrator/scripts/
pairwise_judge.py`, its implementation rubric, through `claude -p`); this
file supplies the change sets and the brief. The CLI's own graders score
each arm against fixed criteria and never compare the two, and G1 showed
the bars sit at the ceiling, so this comparison is G2's measurement.

What the judge sees per side: every file the run added or changed against
the case's pristine scaffold (the case's `scaffold.sh` run into a fresh
temporary directory), minus the run's report under `docs/reports/`
(a self-description is not the code), `node_modules`, coverage output and
anything binary; a deleted file is listed by name; a symlink is shown as a
link to its target and never followed, so nothing outside the run's tree
reaches the prompt. Each side's view is capped at `--max-bytes` of UTF-8,
lock files cut first, and the judge is told when something was cut. The
brief is the case's prompt with the one clause that names the lite skill
removed and the case's own name (its report path) replaced by `<case>`,
plus each `--task` file read from the pristine scaffold (the design doc,
say). The judge's prompt labels the sides `implementation_1`
and `implementation_2`; the case names are keys in the record only.

What is checked before anything is judged: the two results are different
cases whose `scaffold.sh` files are byte-identical and whose prompts are
identical once the lite clause is removed (two arms of one slice, not two
slices); each case directory is an `evals/<name>` directory of this
repository; each kept run directory is a `claude-eval-*` directory under
the temp root the gate used (`$TMPDIR`, the platform temp directory or
`~/.cache/kad-eval-tmp`) holding the run's trace. A result file is data:
nothing in it chooses what is executed or read outside those bounds.

Usage: python3 -I evals/tools/compare_arms.py <result-a.json> <result-b.json>
           [--task docs/cancel-hold/design.md ...] [--model sonnet]
           [--paired] [--max-bytes 200000] [-j 4] [--out FILE]
  Writes the record (default: next to result-a, as
  `<result-a stem>-vs-<result-b stem>-<UTC timestamp>.pairwise.json`, a new
  file per run, never over an existing one), updated after every judged
  pair so an interrupted run leaves what it had, and prints the tally.
  Exit 2 when no pair could be judged.
"""
import argparse
import datetime
import itertools
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVALS = (ROOT / "evals").resolve()
sys.path.insert(0, str(ROOT / "skills" / "orchestrator" / "scripts"))
from pairwise_judge import IMPLEMENTATION_RUBRIC, compare  # noqa: E402

SKIP_DIRS = {".git", "node_modules", "coverage", ".nyc_output", ".claude", "dist"}
SKIP_PREFIXES = ("docs/reports/",)
LOCK_FILES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "Cargo.lock",
              "poetry.lock", "uv.lock", "Gemfile.lock", "composer.lock"}
LITE_CLAUSE = re.compile(r"(?:,\s*telling it to build)?\s*with the `kad-dev-team:tdd-implementation-lite` skill")
CHANGED, DELETED, SYMLINK = "changed", "deleted", "symlink"


def temp_roots():
    """Where the gate keeps run directories: $TMPDIR as wsl-gate.sh sets it,
    the platform's temp directory, and the WSL fallback."""
    roots = [os.environ.get("TMPDIR"), tempfile.gettempdir(), Path.home() / ".cache" / "kad-eval-tmp"]
    return {Path(r).resolve() for r in roots if r}


def case_dir(case):
    """The case's directory, required to be `evals/<name>` in this repository."""
    path = (ROOT / case["dir"]).resolve()
    if path.parent != EVALS or path.name != case["name"] or not (path / "scaffold.sh").is_file():
        sys.exit(f"refusing case directory {case['dir']!r}: not evals/{case['name']}/ with a scaffold.sh")
    return path


def load_runs(result_path):
    """(case dict, {run index: cwd path}) for every clean, kept run."""
    data = json.loads(Path(result_path).read_text(encoding="utf-8"))
    case = data["cases"][0]
    case_dir(case)
    runs = {}
    for i, run in enumerate(case["arms"]["with"]):
        if run.get("error"):
            print(f"skipping run {i} of {case['name']}: {run['error']}", file=sys.stderr)
            continue
        kept = run.get("scaffoldDir")
        if not kept:
            print(f"skipping run {i} of {case['name']}: not kept (run the gate with --keep-scaffold)",
                  file=sys.stderr)
            continue
        kept = Path(kept).resolve()
        if (kept.parent not in temp_roots() or not kept.name.startswith("claude-eval-")
                or not (kept / "out" / "trace.jsonl").is_file()):
            print(f"skipping run {i} of {case['name']}: {kept} is not a kept eval run directory",
                  file=sys.stderr)
            continue
        cwd = next((kept / rel for rel in ("sealed/home/cwd", "home/cwd") if (kept / rel).is_dir()), None)
        if cwd is None:
            print(f"skipping run {i} of {case['name']}: no working tree under {kept}", file=sys.stderr)
            continue
        runs[i] = cwd
    return case, runs


def pristine(case):
    """The case's scaffold run into a fresh directory: what every run started from."""
    scaffold = case_dir(case) / "scaffold.sh"
    tmp = Path(tempfile.mkdtemp(prefix="kad-pristine-"))
    subprocess.run(["bash", str(scaffold)], cwd=tmp, check=True,  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
                   stdout=subprocess.DEVNULL)
    return tmp


def walk(base):
    """(relpath, is_symlink) for every file under base worth comparing.
    os.walk does not descend into symlinked directories; a symlinked file is
    reported, never read."""
    for root, dirs, files in os.walk(base):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not Path(root, d).is_symlink())
        for name in sorted(files):
            full = Path(root, name)
            rel = full.relative_to(base).as_posix()
            if rel.startswith(SKIP_PREFIXES) or rel.endswith(".log"):
                continue
            yield rel, full.is_symlink()


def change_set(cwd, base):
    """[(relpath, kind, text)] of what differs from the pristine tree: kind is
    CHANGED (text is the content), DELETED (None) or SYMLINK (the target)."""
    before = {rel: (None if link else (base / rel).read_bytes()) for rel, link in walk(base)}
    changed, seen = [], set()
    for rel, link in walk(cwd):
        seen.add(rel)
        if link:
            changed.append((rel, SYMLINK, os.readlink(cwd / rel)))
            continue
        data = (cwd / rel).read_bytes()
        if before.get(rel) == data or b"\0" in data:
            continue
        changed.append((rel, CHANGED, data.decode("utf-8", errors="replace")))
    changed += [(rel, DELETED, None) for rel in before if rel not in seen]
    # Lock files last, so a cap cuts them before the code.
    changed.sort(key=lambda item: (Path(item[0]).name in LOCK_FILES, item[0]))
    return changed


def render(changed, max_bytes):
    parts, used, cut = [], 0, []
    for rel, kind, text in changed:
        if kind == DELETED:
            block = f"### {rel} (deleted)\n"
        elif kind == SYMLINK:
            block = f"### {rel} (symlink to {text}; not followed)\n"
        else:
            block = f"### {rel}\n```\n{text}\n```\n"
        size = len(block.encode("utf-8"))
        if used + size > max_bytes:
            cut.append(rel)
            continue
        parts.append(block)
        used += size
    if cut:
        parts.append("### [view truncated: " + ", ".join(cut) + " not shown]\n")
    if not parts:
        parts.append("### [no files changed]\n")
    return "".join(parts)


def neutral_prompt(case):
    """The case's prompt with the clause naming the lite skill removed and the
    case's own name (its report path) replaced by `<case>`, so the brief reads
    the same for both arms and names neither."""
    return LITE_CLAUSE.sub("", case["promptMarkdown"]).replace(case["name"], "<case>").strip()


def same_slice(case_a, case_b):
    """Exit unless the two cases are two arms of one slice."""
    if case_a["name"] == case_b["name"]:
        sys.exit("the two results are of the same case; pass one result per arm")
    scaffold_a = (case_dir(case_a) / "scaffold.sh").read_bytes()
    scaffold_b = (case_dir(case_b) / "scaffold.sh").read_bytes()
    if scaffold_a != scaffold_b:
        sys.exit(f"{case_a['name']} and {case_b['name']} scaffold different trees; not two arms of one slice")
    if neutral_prompt(case_a) != neutral_prompt(case_b):
        sys.exit(f"{case_a['name']} and {case_b['name']} have different prompts beyond the lite clause; "
                 "not two arms of one slice")


def judge(job):
    name_a, name_b, i, j, brief, view_a, view_b, model = job
    # The names key the sides so the winner comes back by name; the judge's
    # prompt labels them implementation_1 and implementation_2 (pairwise_judge).
    result = compare(brief, {name_a: view_a, name_b: view_b}, IMPLEMENTATION_RUBRIC, model)
    return {"a_run": i, "b_run": j, "orders": result["orders"],
            "verdict": result["verdict"], "cost_usd": result["cost_usd"]}


def write_record(out, record):
    """Whole file or nothing: a temp file beside it, then one rename."""
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps(record, indent=2), encoding="utf-8")
    os.replace(tmp, out)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("result_a", type=Path)
    parser.add_argument("result_b", type=Path)
    parser.add_argument("--task", action="append", default=[],
                        help="a brief file, relative to the project (read from the pristine scaffold)")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--paired", action="store_true", help="run i against run i only")
    parser.add_argument("--max-bytes", type=int, default=200_000)
    parser.add_argument("-j", "--concurrency", type=int, default=4)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    case_a, runs_a = load_runs(args.result_a)
    case_b, runs_b = load_runs(args.result_b)
    same_slice(case_a, case_b)
    name_a, name_b = case_a["name"], case_b["name"]
    base = pristine(case_a)
    brief = neutral_prompt(case_a)
    for task in args.task:
        task_path = (base / task).resolve()
        if base.resolve() not in task_path.parents:
            sys.exit(f"--task {task!r} is outside the scaffold")
        brief += f"\n\n### {task}\n" + task_path.read_text(encoding="utf-8")

    changes_a = {i: change_set(cwd, base) for i, cwd in runs_a.items()}
    changes_b = {j: change_set(cwd, base) for j, cwd in runs_b.items()}
    views_a = {i: render(changed, args.max_bytes) for i, changed in changes_a.items()}
    views_b = {j: render(changed, args.max_bytes) for j, changed in changes_b.items()}

    def files(changes):
        return {i: [rel + {CHANGED: "", DELETED: " (deleted)", SYMLINK: " (symlink)"}[kind]
                    for rel, kind, _ in changed] for i, changed in changes.items()}

    if args.paired:
        pairs = [(i, i) for i in sorted(views_a) if i in views_b]
        for i in sorted(set(views_a) ^ set(views_b)):
            print(f"run {i} has no counterpart in the other arm; left out of the paired comparison",
                  file=sys.stderr)
    else:
        pairs = list(itertools.product(sorted(views_a), sorted(views_b)))
    if not pairs:
        sys.exit("no pair to judge: both results need kept, clean runs")

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = args.out or args.result_a.with_name(
        f"{args.result_a.stem}-vs-{args.result_b.stem}-{stamp}.pairwise.json")
    if out.exists():
        sys.exit(f"refusing to overwrite {out}; pass --out with a new name")

    record = {"status": "partial",
              "a": {"case": name_a, "source": str(args.result_a), "runs": sorted(views_a), "files": files(changes_a)},
              "b": {"case": name_b, "source": str(args.result_b), "runs": sorted(views_b), "files": files(changes_b)},
              "tasks": args.task, "model": args.model, "paired": args.paired,
              "pairs": [], "tally": {}, "cost_usd": 0.0}
    results = []
    jobs = [(name_a, name_b, i, j, brief, views_a[i], views_b[j], args.model) for i, j in pairs]
    with ThreadPoolExecutor(args.concurrency) as pool:
        futures = [pool.submit(judge, job) for job in jobs]
        try:
            for future in as_completed(futures):
                results.append(future.result())
                results.sort(key=lambda r: (r["a_run"], r["b_run"]))
                record["pairs"] = results
                record["cost_usd"] = round(sum(r["cost_usd"] for r in results), 4)
                write_record(out, record)  # every judged pair is on disk before the next
        except BaseException:
            for future in futures:
                future.cancel()
            print(f"interrupted after {len(results)} of {len(jobs)} pairs; partial record: {out}",
                  file=sys.stderr)
            raise

    tally = {name_a: 0, name_b: 0, "tie": 0, "split": 0, "no verdict": 0}
    for r in results:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    record.update(status="complete", tally=tally)
    write_record(out, record)

    for r in results:
        print(f"run {r['a_run']} vs run {r['b_run']}: {r['verdict']}")
        for o in r["orders"]:
            if "winner" in o:
                print(f"  {o['first']} first -> {o['winner']}: {o['reasoning']}")
            else:
                print(f"  {o['first']} first -> error: {o['error']}")
    print(f"\n{name_a}: {tally[name_a]}  {name_b}: {tally[name_b]}  tie: {tally['tie']}  "
          f"split: {tally['split']}  no verdict: {tally['no verdict']}  (${record['cost_usd']})")
    print(f"record: {out}")
    sys.exit(0 if any(r["verdict"] != "no verdict" for r in results) else 2)


if __name__ == "__main__":
    main()
