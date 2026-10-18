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
anything binary; a deleted file is listed by name. Each side's view is
capped at `--max-bytes` of UTF-8, lock files cut first, and the judge is
told when something was cut. The brief is the case's prompt plus each
`--task` file read from the pristine scaffold (the design doc, say).
Nothing in either view names the arm or the skill.

Usage: python3 -I evals/tools/compare_arms.py <result-a.json> <result-b.json>
           [--task docs/cancel-hold/design.md ...] [--model sonnet]
           [--paired] [--max-bytes 200000] [-j 4] [--out FILE]
  Writes the record (default: next to result-a, as
  `<result-a stem>-vs-<result-b stem>.pairwise.json`) and prints the tally.
  Exit 2 when no pair could be judged.
"""
import argparse
import itertools
import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills" / "orchestrator" / "scripts"))
from pairwise_judge import IMPLEMENTATION_RUBRIC, compare  # noqa: E402

SKIP_DIRS = {".git", "node_modules", "coverage", ".nyc_output", ".claude", "dist"}
SKIP_PREFIXES = ("docs/reports/",)
LOCK_FILES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "Cargo.lock",
              "poetry.lock", "uv.lock", "Gemfile.lock", "composer.lock"}


def load_runs(result_path):
    """(case dict, [(run index, cwd path)]) for every clean, kept run."""
    data = json.loads(Path(result_path).read_text(encoding="utf-8"))
    case = data["cases"][0]
    runs = []
    for i, run in enumerate(case["arms"]["with"]):
        if run.get("error"):
            print(f"skipping run {i} of {case['name']}: {run['error']}", file=sys.stderr)
            continue
        kept = run.get("scaffoldDir")
        if not kept:
            print(f"skipping run {i} of {case['name']}: not kept (run the gate with --keep-scaffold)",
                  file=sys.stderr)
            continue
        cwd = next((Path(kept) / rel for rel in ("sealed/home/cwd", "home/cwd")
                    if (Path(kept) / rel).is_dir()), None)
        if cwd is None:
            print(f"skipping run {i} of {case['name']}: no working tree under {kept}", file=sys.stderr)
            continue
        runs.append((i, cwd))
    return case, runs


def pristine(case):
    """The case's scaffold run into a fresh directory: what every run started from."""
    scaffold = ROOT / case["dir"] / "scaffold.sh"
    tmp = Path(tempfile.mkdtemp(prefix="kad-pristine-"))
    subprocess.run(["bash", str(scaffold)], cwd=tmp, check=True,  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
                   stdout=subprocess.DEVNULL)
    return tmp


def walk(base):
    for root, dirs, files in os.walk(base):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            rel = Path(root, name).relative_to(base).as_posix()
            if rel.startswith(SKIP_PREFIXES) or rel.endswith(".log"):
                continue
            yield rel


def change_set(cwd, base):
    """[(relpath, text or None for deleted)] of what differs from the pristine tree."""
    before = {rel: (base / rel).read_bytes() for rel in walk(base)}
    changed = []
    for rel in walk(cwd):
        data = (cwd / rel).read_bytes()
        if before.get(rel) == data:
            continue
        if b"\0" in data:
            continue
        changed.append((rel, data.decode("utf-8", errors="replace")))
    seen = {rel for rel, _ in changed} | {rel for rel in walk(cwd)}
    changed += [(rel, None) for rel in before if rel not in seen]
    # Lock files last, so a cap cuts them before the code.
    changed.sort(key=lambda item: (Path(item[0]).name in LOCK_FILES, item[0]))
    return changed


def render(changed, max_bytes):
    parts, used, cut = [], 0, []
    for rel, text in changed:
        block = f"### {rel} (deleted)\n" if text is None else f"### {rel}\n```\n{text}\n```\n"
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


def judge(job):
    name_a, name_b, i, j, brief, view_a, view_b, model = job
    result = compare(brief, {name_a: view_a, name_b: view_b}, IMPLEMENTATION_RUBRIC, model)
    return {"a_run": i, "b_run": j, "orders": result["orders"],
            "verdict": result["verdict"], "cost_usd": result["cost_usd"]}


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
    name_a, name_b = case_a["name"], case_b["name"]
    if name_a == name_b:
        sys.exit("the two results are of the same case; pass one result per arm")
    base = pristine(case_a)
    brief = case_a["promptMarkdown"].strip()
    if case_b["promptMarkdown"].strip() != brief:
        # The prompts differ only in which skill they name; the judge sees
        # neither name, so the brief is the heavy case's with the skill line
        # left as it is: a prompt line naming a skill is not a criterion.
        pass
    for task in args.task:
        brief += f"\n\n### {task}\n" + (base / task).read_text(encoding="utf-8")

    changes_a = {i: change_set(cwd, base) for i, cwd in runs_a}
    changes_b = {j: change_set(cwd, base) for j, cwd in runs_b}
    views_a = {i: render(changed, args.max_bytes) for i, changed in changes_a.items()}
    views_b = {j: render(changed, args.max_bytes) for j, changed in changes_b.items()}
    files = lambda changes: {i: [p + (" (deleted)" if t is None else "") for p, t in changed]  # noqa: E731
                             for i, changed in changes.items()}
    pairs = list(zip(views_a, views_b)) if args.paired else list(itertools.product(views_a, views_b))
    if not pairs:
        sys.exit("no pair to judge: both results need kept, clean runs")
    jobs = [(name_a, name_b, i, j, brief, views_a[i], views_b[j], args.model) for i, j in pairs]
    with ThreadPoolExecutor(args.concurrency) as pool:
        results = list(pool.map(judge, jobs))

    tally = {name_a: 0, name_b: 0, "tie": 0, "split": 0, "no verdict": 0}
    for r in results:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    record = {"a": {"case": name_a, "source": str(args.result_a), "runs": sorted(views_a), "files": files(changes_a)},
              "b": {"case": name_b, "source": str(args.result_b), "runs": sorted(views_b), "files": files(changes_b)},
              "tasks": args.task, "model": args.model, "paired": args.paired,
              "pairs": results, "tally": tally,
              "cost_usd": round(sum(r["cost_usd"] for r in results), 4)}
    out = args.out or args.result_a.with_name(f"{args.result_a.stem}-vs-{args.result_b.stem}.pairwise.json")
    out.write_text(json.dumps(record, indent=2), encoding="utf-8")

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
