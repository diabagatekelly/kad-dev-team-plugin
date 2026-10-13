"""Run the eval cases a change affects and pass or fail it against the bar.

1. Picks the cases with `affected_cases.py` (or takes `--cases`).
2. Runs each once, plugin arm only, up to `--jobs` cases at a time.
3. A case is suspect when its score lands below its bar in
   `thresholds.json` (minus `--tolerance`), or when any grader the bar
   recorded as passing in every run fails. A suspect case is re-run at its
   own `runs:` count, since one run of a noisy judge proves little; the
   re-run is what counts.
4. Prints a markdown table (also to `$GITHUB_STEP_SUMMARY` when set) and
   exits 1 if any case is still below its bar, or any always-passing
   grader failed in every re-run. The aggregate tolerance absorbs judge
   noise; the per-grader check is what stops one grader regressing for
   good inside a case with many graders.

A case with no recorded bar is reported as new and doesn't fail the gate;
record one with `record_thresholds.py` once it has a result you accept.
Bars recorded before per-grader rates existed get the aggregate check only.

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
        c = json.load(open(out, encoding="utf-8"))["cases"][0]
        runs = c["arms"]["with"]
        clean = [r for r in runs if not r.get("error")]
        if runs and not clean:
            # The CLI still scores a run that never started: every grader
            # fails, or a "called 0 times" grader passes vacuously. Either
            # reads as a verdict instead of a broken machine (a Bash-granting
            # case on a host with no sandbox, say), so it is an error here.
            first = " ".join(str(runs[0]["error"]).split())[:160]
            return None, len(runs), {}, f"every run errored: {first}"
        # Errored runs (timeouts, refused starts) say nothing about the skill;
        # the score and the per-grader rates come from the clean runs only.
        score = sum(r["score"] for r in clean) / len(clean)
        return score, len(clean), grader_rates(clean), None
    except (OSError, ValueError, KeyError, IndexError):
        return None, 0, {}, f"no result (exit {code}; see {os.path.relpath(out[:-5] + '.log', ROOT)})"


def grader_rates(runs):
    """Share of the given runs each scored grader passed."""
    passed, seen = {}, {}
    for run in runs:
        for g in run.get("graders", []):
            if g.get("scored") is False:
                continue
            seen[g["name"]] = seen.get(g["name"], 0) + 1
            passed[g["name"]] = passed.get(g["name"], 0) + (1 if g.get("passed") else 0)
    return {name: passed[name] / seen[name] for name in seen}


def regressed(bar_rates, rates):
    """Graders the bar recorded as passing every run that failed every run here."""
    return sorted(name for name, rate in rates.items()
                  if bar_rates.get(name) == 1 and rate == 0)


def main():
    # The table uses em-dashes; a Windows console in a legacy code page
    # would otherwise print them as replacement characters.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
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
            score, runs, rates, err = f.result()
            bar = bars.get(case, {}).get("score")
            bar_rates = bars.get(case, {}).get("graders", {})
            lost = regressed(bar_rates, rates)
            rows[case] = {"bar": bar, "score": score, "runs": runs, "error": err,
                          "rerun": False, "lost": lost}
            if score is not None and bar is not None and (score < bar - a.tolerance or lost):
                retry[pool.submit(run_case, case, None, tag + "-rerun")] = case
        for f in concurrent.futures.as_completed(retry):
            case = retry[f]
            score, runs, rates, err = f.result()
            lost = regressed(bars.get(case, {}).get("graders", {}), rates)
            rows[case].update(score=score, runs=runs, error=err, rerun=True, lost=lost)

    failed = []
    lines = ["| Case | Bar | Score | Runs | Graders lost | Result |", "|---|---|---|---|---|---|"]
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
        elif r["lost"]:
            verdict = "**grader regressed**"
            failed.append(case)
        else:
            verdict = "pass"
        bar = "—" if r["bar"] is None else f"{r['bar']:.2f}"
        score = "—" if r["score"] is None else f"{r['score']:.2f}"
        runs = f"{r['runs']}" + (" (re-run)" if r["rerun"] else "")
        lost = ", ".join(f"`{g}`" for g in r["lost"]) or "—"
        lines.append(f"| `{case}` | {bar} | {score} | {runs} | {lost} | {verdict} |")
    head = (f"**Eval gate: {'FAIL' if failed else 'PASS'}** — {len(rows) - len(failed)}/{len(rows)} "
            f"cases at or above their bar (tolerance {a.tolerance}) with no always-passing "
            f"grader lost.")
    report = head + "\n\n" + "\n".join(lines) + "\n"
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        open(summary, "a").write(report)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
