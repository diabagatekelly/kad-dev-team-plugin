#!/usr/bin/env python3
"""Rule deletions on a skill, and the known-bad references kept from them.

A case shows it guards a rule when the skill with that rule removed fails
it. `TODO.md`'s E2 deletes one rule at a time from a skill and runs the
cases the skill reaches; a deletion a case catches is kept beside the case
as `evals/<case>/known-bad/<rule>.json`, so "fails without the rule" is a
property the suite keeps and can check again. The skill on the branch is
never edited: every run is on a scratch copy of the working tree.

A reference (one JSON object):

    {"skill": "chunk-runner",
     "rule": "the rule in words",
     "edits": [{"file": "skills/chunk-runner/SKILL.md", "old": "...", "new": ""}],
     "also": ["orchestrator"],          (optional: other skills whose SKILL.md the edits may touch)
     "fails": ["grader-name", ...],
     "observed": {"date": "2026-11-13", "runs": 3, "claude_version": "...",
                  "rates": {"grader-name": 0.0}}}

`old` is the exact text removed and must occur exactly once in `file`;
`fails` are the case's graders that must fail on the copy. A case that
resumes a `history.jsonl` runs the skill text frozen in it, so the copy's
histories get the same edit.

A mutants file (`--mutants`, a JSON list) is the working form of a pass:
the same `rule` and `edits`, an `id`, and `cases`, the cases to run it on.

    check [--mutants FILE]
        No model. Every reference (or mutant) still applies: each `old`
        occurs exactly once, each grader in `fails` is a grader of its
        case. A skill edit that touches a guarded rule fails here, and
        the reference is then re-written and re-run. Exit 1 on any miss.
    apply (<reference.json> | --mutants FILE --id ID) <out-dir>
        The scratch copy with the edits applied, to look at.
    run [--case CASE ...] [--rule ID ...] [--mutants FILE] [--runs 3]
        [--parallel 9] [--out DIR] [--resume] [--keep]
        Model time. Each reference (or each mutant on each of its cases):
        copy, apply, run the case `--runs` times with the gate's own
        arguments, read the result per grader. A run that errored and a
        grader that threw are set aside, as the gate does. For a
        reference, exit 1 unless every grader in `fails` failed (passed
        in at most a third of the clean runs). Results and traces go to
        `--out` (default: a `kad-skill-mutation` folder in the temp
        directory), never to `evals/results/`: a run on a broken skill
        is not part of a case's history. `--resume` skips a pair whose
        result already holds `--runs` clean runs of the same deletion on
        the same case file. One invocation per `--out` folder at a time:
        two would write the same result files. With `--mutants` a pair is
        CAUGHT when a grader that passes every run at its bar fails, and
        INCOMPLETE when a run errored: read the failure before counting it.

Usage: python3 -I evals/tools/skill_mutation.py check
"""
import argparse
import concurrent.futures
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

TOOLS = os.path.dirname(os.path.abspath(__file__))
EVALS = os.path.dirname(TOOLS)
ROOT = os.path.dirname(EVALS)
FAIL_AT = 1 / 3  # a grader "fails" when it passed in at most this share of the clean runs


def references(cases=None, rules=None):
    """(id, case, reference) for every known-bad file, in path order."""
    out = []
    for path in sorted(glob.glob(os.path.join(EVALS, "*", "known-bad", "*.json"))):
        case = os.path.basename(os.path.dirname(os.path.dirname(path)))
        ident = os.path.basename(path)[:-5]
        if (cases and case not in cases) or (rules and ident not in rules):
            continue
        out.append((ident, case, json.load(open(path, encoding="utf-8"))))
    return out


def mutants(path, cases=None, rules=None):
    out = []
    for m in json.load(open(path, encoding="utf-8")):
        if rules and m["id"] not in rules:
            continue
        for case in m.get("cases", []):
            if not cases or case in cases:
                out.append((m["id"], case, m))
    return out


def skill_file(ref):
    return f"skills/{ref.get('skill')}/SKILL.md"


def editable(ref, file):
    """The files a reference may edit: its own skill's, and the `SKILL.md`
    of each skill it names under `also` (a rule two skills state, such as
    the screens check in `delivery` and in the orchestrator's E step, is
    only removed when both places go)."""
    return file in [skill_file(ref)] + [f"skills/{name}/SKILL.md" for name in ref.get("also", [])
                                        if re.fullmatch(r"[a-z0-9-]+", str(name))]


def grader_names(case):
    """The names of a case's graders, read from its case.yaml as text (the
    tools here carry no YAML parser)."""
    text = open(os.path.join(EVALS, case, "case.yaml"), encoding="utf-8").read()
    body = text.split("\ngraders:", 1)[1] if "\ngraders:" in text else ""
    return set(re.findall(r"^\s+name:\s*(\S+)\s*$", body, re.M))


def problems(ident, case, ref, root=None):
    """Why this reference or mutant no longer applies; empty when it does."""
    root = root or ROOT
    found = []
    if not ref.get("edits"):
        found.append("no edits")
    if "fails" in ref and not ref["fails"]:
        found.append("no grader named in `fails`: nothing would show the deletion is caught")
    for e in ref.get("edits", []):
        if not editable(ref, e.get("file")):
            # the one file a reference may edit: a path elsewhere would guard
            # nothing of the skill, and one outside the tree would be written to
            found.append(f"edits {e.get('file')}, not {skill_file(ref)}")
            continue
        path = os.path.join(root, e["file"])
        if not os.path.isfile(path):
            found.append(f"{e['file']} does not exist")
            continue
        n = open(path, encoding="utf-8").read().count(e["old"])
        if n != 1:
            found.append(f"removed text occurs {n} times in {e['file']} (must be once): {e['old'][:60]!r}")
        if e["old"] == e.get("new", ""):
            found.append("an edit that changes nothing")
    if not os.path.isfile(os.path.join(EVALS, case, "case.yaml")):
        found.append(f"no case {case}")
    else:
        unknown = sorted(set(ref.get("fails", [])) - grader_names(case))
        if unknown:
            found.append(f"not graders of {case}: {', '.join(unknown)}")
    return found


def repo_files(root=None):
    root = root or ROOT
    args = ["git", "-C", root, "ls-files", "--cached", "--others", "--exclude-standard"]
    # a fixed git command on the tree's own root; no shell, nothing from a reference
    listed = subprocess.check_output(args, text=True).splitlines()  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
    return [f for f in listed if f and os.path.isfile(os.path.join(root, f))]


def apply(ref, dest, root=None):
    """A copy of the working tree at `dest` with the reference's edits made.
    The tree itself is not written to."""
    root = root or ROOT
    for f in repo_files(root):
        target = os.path.join(dest, f)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(os.path.join(root, f), target)
    marker = json.dumps(f"Base directory for this skill: <plugin-root>/skills/{ref.get('skill')}")[1:-1]
    for e in ref["edits"]:
        if not editable(ref, e.get("file")):
            raise SystemExit(f"edits {e.get('file')}, not {skill_file(ref)}")
        path = os.path.join(dest, e["file"])
        text = open(path, encoding="utf-8").read()
        if text.count(e["old"]) != 1:
            raise SystemExit(f"{e['file']}: removed text occurs {text.count(e['old'])} times, must be once")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text.replace(e["old"], e.get("new", "")))
        # A replay or phase history carries the skill's text as it was
        # loaded in the frozen turns (a JSON string in history.jsonl): the
        # resumed run reads that, not the file, so the rule goes from there
        # too. An edit to the frontmatter is in no history.
        was, now = json.dumps(e["old"])[1:-1], json.dumps(e.get("new", ""))[1:-1]
        for history in glob.glob(os.path.join(dest, "evals", "*", "history.jsonl")):
            lines = open(history, encoding="utf-8").read().split("\n")
            # only the entry that loaded this skill: the same words in a
            # prompt or another turn are the case's input and stay
            edited = [line.replace(was, now) if marker in line else line for line in lines]
            if edited != lines:
                with open(history, "w", encoding="utf-8") as fh:
                    fh.write("\n".join(edited))


def run_env():
    """The gate's environment (gate.sh): on macOS, Homebrew's Node 24 first."""
    env = dict(os.environ)
    if sys.platform == "darwin":
        try:
            prefix = subprocess.check_output(["brew", "--prefix"], text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            prefix = "/opt/homebrew"
        node = os.path.join(prefix, "opt", "node@24", "bin")
        if os.path.isdir(node):
            env["PATH"] = node + os.pathsep + env.get("PATH", "")
    return env


_start = threading.Lock()


def key_of(case, ref):
    """What a result was run on: the deletion's edits and the case's own
    file. A result kept from another deletion or an older case is not this
    pair's (`--resume`)."""
    h = hashlib.sha256(json.dumps(ref["edits"], sort_keys=True).encode())
    h.update(open(os.path.join(EVALS, case, "case.yaml"), "rb").read())
    return h.hexdigest()[:16]


def run_pair(ident, case, ref, runs, out_dir, keep, parallel=8):
    """One reference on one case: the per-grader pass rates over the clean
    runs, how many runs errored, and the result file."""
    sys.path.insert(0, TOOLS)
    import eval_gate  # the gate's own argument list, trace keeping and rates
    out = os.path.join(out_dir, f"{ident}--{case}.json")
    copy = tempfile.mkdtemp(prefix=f"kad-mut-{ident[:24]}-")
    try:
        if os.path.exists(out):
            os.remove(out)  # a run that fails to write must not be read as the last one's result
        apply(ref, copy)
        with _start:
            time.sleep(1.1)  # the CLI names its report folder by the second
        args = ["claude", "plugin", "eval", ".", "--case", case, "--runs", str(runs),
                "--ablation", "none", "--scaffold", "--judge-model", "sonnet", "--no-publish",
                "--trust-plugin", "--concurrency", str(max(1, min(runs, parallel, 8))), "--keep-temp", "--json", out]
        grant = eval_gate.case_tool_grant(case)
        if grant:
            args += ["--allow-tools", *grant]
        with open(out[:-5] + ".log", "w") as log:
            # a fixed argument list plus a case name; no shell
            code = subprocess.run(args, cwd=copy, stdout=log, stderr=subprocess.STDOUT,  # nosemgrep
                                  env=run_env()).returncode
        try:
            data = json.load(open(out, encoding="utf-8"))
            c = data["cases"][0]
            results = c["arms"]["with"]
        except (OSError, ValueError, KeyError, IndexError):
            return {"id": ident, "case": case, "error": f"no result (exit {code})", "source": out}
        for r in results:
            threw = [g["name"] for g in r.get("graders", [])
                     if str(g.get("explanation", "")).startswith("grader threw")]
            if threw and not r.get("error"):
                r["error"] = f"{len(threw)} grader(s) threw"
        eval_gate.keep_traces(c, out)
        data = json.load(open(out, encoding="utf-8"))
        for kept, r in zip(data["cases"][0]["arms"]["with"], results):
            if r.get("error"):
                kept["error"] = r["error"]
        data["mutation"] = key_of(case, ref)
        json.dump(data, open(out, "w", encoding="utf-8"), indent=2)
        clean = [r for r in results if not r.get("error")]
        return {"id": ident, "case": case, "runs": len(clean), "errored": len(results) - len(clean),
                "rates": eval_gate.grader_rates(clean), "version": data.get("claudeVersion"),
                "source": out, "error": None if clean else "every run errored"}
    finally:
        if not keep:
            shutil.rmtree(copy, ignore_errors=True)


def done_already(ident, case, ref, runs, out_dir):
    try:
        data = json.load(open(os.path.join(out_dir, f"{ident}--{case}.json"), encoding="utf-8"))
        if data.get("mutation") != key_of(case, ref):
            return False
        return sum(1 for r in data["cases"][0]["arms"]["with"] if not r.get("error")) >= runs
    except (OSError, ValueError, KeyError, IndexError):
        return False


def failed_graders(rates):
    return sorted(name for name, rate in rates.items() if rate <= FAIL_AT + 1e-9)


def cmd_check(a):
    pairs = mutants(a.mutants) if a.mutants else references()
    bad = 0
    for ident, case, ref in pairs:
        found = problems(ident, case, ref)
        bad += bool(found)
        print(f"{'FAIL' if found else 'PASS'}  {case} / {ident}" + "".join(f"\n      {p}" for p in found))
    print(f"{len(pairs)} checked, {bad} no longer apply")
    return 1 if bad else 0


def cmd_apply(a):
    if a.mutants:
        chosen = [m for m in json.load(open(a.mutants, encoding="utf-8")) if m["id"] == a.id]
        if len(chosen) != 1:
            raise SystemExit(f"no single mutant with id {a.id}")
        ref, dest = chosen[0], a.paths[0]
    else:
        ref, dest = json.load(open(a.paths[0], encoding="utf-8")), a.paths[1]
    apply(ref, dest)
    print(dest)
    return 0


def cmd_run(a):
    pairs = mutants(a.mutants, a.case, a.rule) if a.mutants else references(a.case, a.rule)
    for ident, case, ref in pairs:
        found = problems(ident, case, ref)
        if found:
            raise SystemExit(f"{case} / {ident} does not apply: {'; '.join(found)} (run `check`)")
    # absolute: the CLI runs in the scratch copy and writes its result there otherwise
    out_dir = os.path.abspath(a.out or os.path.join(tempfile.gettempdir(), "kad-skill-mutation"))
    os.makedirs(out_dir, exist_ok=True)
    if a.resume:
        pairs = [p for p in pairs if not done_already(p[0], p[1], p[2], a.runs, out_dir)]
    print(f"{len(pairs)} to run, {a.runs} runs each, results in {out_dir}", flush=True)
    exit_code = 0
    try:
        bars = json.load(open(os.path.join(EVALS, "thresholds.json"), encoding="utf-8"))
    except (OSError, ValueError):
        bars = {}
    workers = max(1, a.parallel // max(1, a.runs))
    with concurrent.futures.ThreadPoolExecutor(workers) as pool:
        futures = {pool.submit(run_pair, i, c, r, a.runs, out_dir, a.keep, a.parallel): (i, c, r) for i, c, r in pairs}
        for fut in concurrent.futures.as_completed(futures):
            ident, case, ref = futures[fut]
            res = fut.result()
            if res.get("error"):
                print(f"ERROR     {case} / {ident}: {res['error']}", flush=True)
                exit_code = 1
                continue
            # a grader the bar does not record as passing every run cannot
            # show a deletion: it fails with the rule in place too
            bar = bars.get(case, {}).get("graders", {})
            below = sorted(n for n in failed_graders(res["rates"]) if bar.get(n, 1) < 1)
            failed = [n for n in failed_graders(res["rates"]) if n not in below]
            partial = sorted(n for n, r in res["rates"].items() if FAIL_AT + 1e-9 < r < 1)
            line = (f"{case} / {ident}: {res['runs']} clean"
                    + (f", {res['errored']} errored" if res["errored"] else "")
                    + (f"; failed: {', '.join(failed)}" if failed else "")
                    + ("; partly: " + ", ".join("%s %.2f" % (n, res["rates"][n]) for n in partial) if partial else ""))
            if below:
                line += f"; failing at the bar already, not counted: {', '.join(below)}"
            if a.mutants and res["runs"] < a.runs:
                print(f"INCOMPLETE  {line}; too few clean runs to say", flush=True)
                exit_code = 1
            elif a.mutants:
                print(f"{'CAUGHT  ' if failed else 'SURVIVED'}  {line}", flush=True)
            else:
                missing = sorted(set(ref.get("fails", [])) - set(failed))
                short = res["runs"] < a.runs
                ok = not missing and not short
                print(f"{'PASS' if ok else 'FAIL'}      {line}"
                      + (f"; expected to fail and did not: {', '.join(missing)}" if missing else "")
                      + ("; too few clean runs" if short else ""), flush=True)
                exit_code = exit_code or (0 if ok else 1)
    return exit_code


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--mutants")
    ap = sub.add_parser("apply")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--mutants")
    ap.add_argument("--id")
    r = sub.add_parser("run")
    r.add_argument("--case", nargs="*")
    r.add_argument("--rule", nargs="*")
    r.add_argument("--mutants")
    r.add_argument("--runs", type=int, default=3)
    r.add_argument("--parallel", type=int, default=9, help="agent runs in flight (9)")
    r.add_argument("--out")
    r.add_argument("--resume", action="store_true")
    r.add_argument("--keep", action="store_true", help="leave each scratch copy in place")
    a = p.parse_args()
    return {"check": cmd_check, "apply": cmd_apply, "run": cmd_run}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
