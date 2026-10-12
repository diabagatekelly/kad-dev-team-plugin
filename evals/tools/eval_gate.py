"""Run the eval cases a change affects and pass or fail it against the bar.

1. Picks the cases with `affected_cases.py` (or takes `--cases`).
2. Runs each once, plugin arm only, up to `--jobs` cases at a time.
3. Any case scoring below its bar in `thresholds.json` (minus
   `--tolerance`) is re-run at its own `runs:` count, since one run of a
   noisy judge proves little; the re-run's score is the one that counts.
4. Prints a markdown table (also to `$GITHUB_STEP_SUMMARY` when set) and
   exits 1 if any case is still below its bar.

A case with no recorded bar is reported as new and doesn't fail the gate;
record one with `record_thresholds.py` once it has a result you accept.

Usage: python3 -I evals/tools/eval_gate.py [--base origin/main] [--cases a b ... | --all]
           [--jobs 6] [--tolerance 0.1] [--dry-run]
"""
import argparse
import concurrent.futures
import datetime
import json
import os
import subprocess
import sys
import threading
import time

TOOLS = os.path.dirname(os.path.abspath(__file__))
EVALS = os.path.dirname(TOOLS)
ROOT = os.path.dirname(EVALS)
sys.path.insert(0, TOOLS)
import affected_cases  # noqa: E402


_start_lock = threading.Lock()


def run_case(case, runs, tag):
    # The CLI names its HTML report folder by the second a run starts, and
    # refuses to reuse one, so keep launches at least a second apart.
    with _start_lock:
        time.sleep(1.1)
    out = os.path.join(EVALS, "results", f"{tag}-{case}.json")
    args = ["claude", "plugin", "eval", ".", "--case", case, "--ablation", "none",
            "--scaffold", "--judge-model", "sonnet", "--no-publish", "--trust-plugin",
            "--allow-tools", "Write", "Edit", "Bash", "--json", out]
    if runs:
        args[args.index("--ablation"):args.index("--ablation")] = ["--runs", str(runs)]
    log = open(out[:-5] + ".log", "w")
    code = subprocess.run(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT).returncode
    try:
        c = json.load(open(out))["cases"][0]
        return c["aggregates"]["score"], len(c["arms"]["with"]), None
    except (OSError, ValueError, KeyError, IndexError):
        return None, 0, f"no result (exit {code}; see {os.path.relpath(out[:-5] + '.log', ROOT)})"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="origin/main")
    p.add_argument("--cases", nargs="*")
    p.add_argument("--all", action="store_true", help="every case, not just the affected ones")
    p.add_argument("--jobs", type=int, default=6)
    p.add_argument("--tolerance", type=float, default=0.1)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    if a.all:
        cases = list(affected_cases.case_dirs())
    else:
        cases = a.cases or affected_cases.affected(affected_cases.changed_files(a.base))
    bars = json.load(open(os.path.join(EVALS, "thresholds.json")))
    if not cases:
        print("No eval case is affected by this change.")
        return 0
    print(f"{len(cases)} affected case(s): {' '.join(cases)}", flush=True)
    if a.dry_run:
        return 0
    os.makedirs(os.path.join(EVALS, "results"), exist_ok=True)
    tag = "gate-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S")

    rows = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:
        first = {pool.submit(run_case, c, 1, tag): c for c in cases}
        retry = {}
        for f in concurrent.futures.as_completed(first):
            case = first[f]
            score, runs, err = f.result()
            bar = bars.get(case, {}).get("score")
            rows[case] = {"bar": bar, "score": score, "runs": runs, "error": err, "rerun": False}
            if score is not None and bar is not None and score < bar - a.tolerance:
                retry[pool.submit(run_case, case, None, tag + "-rerun")] = case
        for f in concurrent.futures.as_completed(retry):
            case = retry[f]
            score, runs, err = f.result()
            rows[case].update(score=score, runs=runs, error=err, rerun=True)

    failed = []
    lines = ["| Case | Bar | Score | Runs | Result |", "|---|---|---|---|---|"]
    for case in sorted(rows):
        r = rows[case]
        if r["error"]:
            verdict = "error: " + r["error"]
            failed.append(case)
        elif r["bar"] is None:
            verdict = "new (no bar yet)"
        elif r["score"] < r["bar"] - a.tolerance:
            verdict = "**below bar**"
            failed.append(case)
        else:
            verdict = "pass"
        bar = "—" if r["bar"] is None else f"{r['bar']:.2f}"
        score = "—" if r["score"] is None else f"{r['score']:.2f}"
        runs = f"{r['runs']}" + (" (re-run)" if r["rerun"] else "")
        lines.append(f"| `{case}` | {bar} | {score} | {runs} | {verdict} |")
    head = (f"**Eval gate: {'FAIL' if failed else 'PASS'}** — {len(rows) - len(failed)}/{len(rows)} "
            f"cases at or above their bar (tolerance {a.tolerance}).")
    report = head + "\n\n" + "\n".join(lines) + "\n"
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        open(summary, "a").write(report)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
