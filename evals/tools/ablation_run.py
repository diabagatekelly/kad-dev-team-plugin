#!/usr/bin/env python3
"""With and without the plugin, for the cases named (TODO.md, E6).

Runs each case with `claude plugin eval --ablation with-without` and puts
everything outside `evals/results/`: a calibration run scores skill-invoked
graders as indicators, so it must never become a case's bar
(`record_thresholds.py` reads `evals/results/*.json`), a run of its history
(`case_history.py`, `case_sort.py` read `evals/results/*/aggregate-result.json`)
or its evidence (only `eval_gate.py` writes `evidence.json`; this tool does
not touch it). The output directory is refused when it is inside the
repository.

Per case it writes `<out>/<case>.json` and `.log`, copies each run's trace
to `<out>/<case>-<arm>-run<i>.trace.jsonl` (both arms; a failure is read
from the trace) and removes the kept scaffold. At the end the cases are
merged into `<out>/aggregate-result.json`, the file `pairwise_judge.py`
takes. A case whose result is already in `<out>` with every run clean, at
the same run count and against the same inputs (the fingerprint
`eval_evidence.py` uses: the case, its skills, agents and fixtures), is
skipped, so a pass cut by the usage window is resumed by the same command.
When any case is run, an earlier `pairwise.json` is removed: its votes were
on other reviews. Exit 1 when a case ends without its clean runs in both
arms (a case that cannot run bare, like one that names the plugin's agent,
ends so every time).

Usage (on macOS put Homebrew's Node 24 first on PATH, as gate.sh does):
  python3 -I evals/tools/ablation_run.py --out ~/kad-eval-ablation/<name> [--runs 3]
      [--jobs 2] [--concurrency 4] case [case ...]
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

TOOLS = os.path.dirname(os.path.abspath(__file__))
EVALS = os.path.dirname(TOOLS)
ROOT = os.path.dirname(EVALS)
sys.path.insert(0, TOOLS)
from eval_evidence import fingerprint  # noqa: E402
from eval_gate import case_tool_grant  # noqa: E402

ARMS = ("with", "without")
CASE_NAME = re.compile(r"[a-z0-9][a-z0-9-]*$")
TIMEOUT = 3600  # seconds for one case's CLI process; a case's own runs time out at 600 to 900
_launch = threading.Lock()


def runs_of(case):
    return [(arm, i, r) for arm in ARMS for i, r in enumerate((case.get("arms") or {}).get(arm) or [])]


def errored(run):
    """A run that never ran, or whose grader could not run: no verdict."""
    if run.get("error"):
        return True
    return any(str(g.get("explanation", "")).startswith("grader threw") for g in run.get("graders", []))


def done(path, want, inputs):
    """The result at `path` holds `want` clean runs per arm, made at this run
    count against these inputs."""
    try:
        data = json.load(open(path, encoding="utf-8"))
        case = data["cases"][0]
    except (OSError, ValueError, KeyError, IndexError):
        return False
    if data.get("ablation") != {"runs": want, "inputs": inputs}:
        return False
    return all(len([r for r in (case["arms"].get(arm) or []) if not errored(r)]) >= want for arm in ARMS)


def keep_traces(case, base):
    for arm, i, run in runs_of(case):
        src = run.get("tracePath")
        if not src or not os.path.isfile(src):
            continue
        dst = f"{base}-{arm}-run{i}.trace.jsonl"
        shutil.copyfile(src, dst)
        run["tracePath"] = dst
        scaffold = os.path.dirname(os.path.dirname(src))
        if os.path.basename(os.path.dirname(src)) == "out" and re.match(r"(claude-eval-|e-)\w+$", os.path.basename(scaffold)):
            # --keep-temp leaves the kept directory read-only (see eval_gate.keep_traces)
            for root, dirs, _ in os.walk(scaffold):
                os.chmod(root, 0o700)
                for d in dirs:
                    os.chmod(os.path.join(root, d), 0o700)
            shutil.rmtree(scaffold, ignore_errors=True)


def run_case(job):
    case, out, runs, concurrency = job
    base = os.path.join(out, case)
    inputs = fingerprint(case)
    for old in (base + ".json", os.path.join(out, "pairwise.json")):
        if os.path.isfile(old):
            os.remove(old)  # never read back a result this run did not write
    # The CLI names its report folder by the second a run starts and refuses
    # to reuse one, so launches are at least a second apart (as in eval_gate).
    with _launch:
        time.sleep(1.1)
    args = ["claude", "plugin", "eval", ".", "--case", case, "--runs", str(runs),
            "--ablation", "with-without", "--scaffold", "--judge-model", "sonnet",
            "--no-publish", "--trust-plugin", "--concurrency", str(concurrency),
            "--keep-temp", "--output-dir", os.path.join(out, "cli", case), "--json", base + ".json"]
    grant = case_tool_grant(case)
    if grant:
        args += ["--allow-tools", *grant]
    with open(base + ".log", "w") as log:
        # a fixed list plus the case's directory name; no shell is involved
        try:
            # The exit code is not a verdict: the CLI exits 1 whenever the
            # plugin arm is below its threshold. The result file is.
            code = subprocess.run(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,  # nosemgrep
                                  timeout=TIMEOUT).returncode
        except subprocess.TimeoutExpired:
            return case, False, f"no result (the CLI ran over {TIMEOUT} s; see {base}.log)"
    try:
        data = json.load(open(base + ".json", encoding="utf-8"))
        keep_traces(data["cases"][0], base)
        data["ablation"] = {"runs": runs, "inputs": inputs}
        json.dump(data, open(base + ".json", "w", encoding="utf-8"), indent=2)
    except (OSError, ValueError, KeyError, IndexError):
        return case, False, f"no result (exit {code}; see {base}.log)"
    c = data["cases"][0]
    bad = [f"{arm}{i}" for arm, i, r in runs_of(c) if errored(r)]
    scores = {arm: [round(r["score"], 2) for r in c["arms"].get(arm) or []
                    if not errored(r) and isinstance(r.get("score"), (int, float))] for arm in ARMS}
    line = f"with {scores['with']} without {scores['without']} ${data.get('costUsd') or 0:.2f}" + (
        f"  ERRORED: {' '.join(bad)}" if bad else "")
    return case, done(base + ".json", runs, inputs), line


def inside_repository(path):
    """True when `path` (which may not exist yet) is the repository or under
    it. Compared by file identity, ancestor by ancestor, so another spelling
    of the same directory on a case-insensitive filesystem is still inside."""
    while True:
        if os.path.exists(path) and os.path.samefile(path, ROOT):
            return True
        parent = os.path.dirname(path)
        if parent == path:
            return False
        path = parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--jobs", type=int, default=2)
    p.add_argument("--concurrency", type=int, default=4)
    p.add_argument("cases", nargs="+")
    a = p.parse_args()
    if min(a.runs, a.jobs, a.concurrency) < 1:
        sys.exit("--runs, --jobs and --concurrency are 1 or more")
    out = os.path.realpath(os.path.expanduser(a.out))
    if inside_repository(out):
        sys.exit("ablation results go outside the repository (see this file's header)")
    cases = list(dict.fromkeys(a.cases))  # a case named twice is run once
    for case in cases:
        # a name, never a path: it is joined to the output directory below
        if not CASE_NAME.match(case) or not os.path.isdir(os.path.join(EVALS, case)):
            sys.exit(f"no such case: {case}")
    os.makedirs(os.path.join(out, "cli"), exist_ok=True)
    todo = [c for c in cases if not done(os.path.join(out, c + ".json"), a.runs, fingerprint(c))]
    for c in cases:
        if c not in todo:
            print(f"{c}: already complete, skipped", flush=True)
    short = []
    with ThreadPoolExecutor(a.jobs) as pool:
        for case, ok, line in pool.map(run_case, [(c, out, a.runs, a.concurrency) for c in todo]):
            print(f"{case}: {line}", flush=True)
            if not ok:
                short.append(case)
    merged = None
    for name in sorted(f for f in os.listdir(out) if f.endswith(".json") and f not in ("aggregate-result.json", "pairwise.json")):
        data = json.load(open(os.path.join(out, name), encoding="utf-8"))
        if merged is None:
            merged = {k: v for k, v in data.items() if k not in ("cases", "aggregates", "costUsd", "ablation")}
            merged["cases"], merged["costUsd"] = [], 0.0
        merged["cases"] += data["cases"]
        merged["costUsd"] += data.get("costUsd") or 0.0
    if merged:
        json.dump(merged, open(os.path.join(out, "aggregate-result.json"), "w", encoding="utf-8"), indent=2)
        print(f"{len(merged['cases'])} cases, ${merged['costUsd']:.2f} -> {os.path.join(out, 'aggregate-result.json')}")
    if short:
        sys.exit(f"without {a.runs} clean runs in both arms: {' '.join(short)}")


if __name__ == "__main__":
    main()
