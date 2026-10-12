"""Write evals/thresholds.json: each case's bar for the eval gate.

For every case directory, takes the most recent `--json` result in
`evals/results/` that ran it (with the plugin) and records:
- `score`: that run's aggregate score (mean over runs of the share of
  graders passed), the bar `eval_gate.py` compares against;
- `graders`: the share of that result's runs each scored grader passed,
  so the gate can tell a grader that always passed from one that was
  already flaky;
- `mode`: `gate` when the result came from `eval_gate.py` (`--ablation
  none`, every grader scored), `calibration` otherwise (`--ablation
  with-without`, where skill-invoked graders are unscored indicators).
  Bars should come from gate-mode runs, because that is the mode the gate
  scores in; a calibration bar is warned about, not refused;
- `runs`, `claude_version` and `source` (the result file) for context;
- `skills_invoked`: every `kad-dev-team` skill seen called in any kept
  trace of the case, which `affected_cases.py` uses to catch consults.

Re-run it after a deliberate change moves a case's score, and commit the
file with that change, so the gate measures against the new bar.

Usage: python3 -I evals/tools/record_thresholds.py [--exclude GLOB ...] [--gate-only] [case ...]
  With case names, updates only those entries. --exclude skips result files
  whose name matches (for runs of a skill version that was reverted).
  --gate-only ignores results that didn't come from eval_gate.py.
"""
import argparse
import fnmatch
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import affected_cases  # noqa: E402

EVALS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(EVALS, "thresholds.json")


def results(exclude):
    for path in glob.glob(os.path.join(EVALS, "results", "*.json")):
        if any(fnmatch.fnmatch(os.path.basename(path), g) for g in exclude):
            continue
        try:
            data = json.load(open(path))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and data.get("cases") and not data.get("partial"):
            yield path, data


def mode_of(path):
    return "gate" if os.path.basename(path).startswith("gate-") else "calibration"


def grader_rates(case):
    """Share of the case's with-arm runs each scored grader passed."""
    passed, seen = {}, {}
    for run in case["arms"]["with"]:
        for g in run.get("graders", []):
            if g.get("scored") is False:
                continue
            seen[g["name"]] = seen.get(g["name"], 0) + 1
            passed[g["name"]] = passed.get(g["name"], 0) + (1 if g.get("passed") else 0)
    return {name: round(passed[name] / seen[name], 3) for name in sorted(seen)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--exclude", action="append", default=[])
    p.add_argument("--gate-only", action="store_true")
    p.add_argument("cases", nargs="*")
    a = p.parse_args()
    cases = list(affected_cases.case_dirs())
    only = set(a.cases) or set(cases)
    latest, invoked = {}, {}
    for path, data in results(a.exclude):
        if a.gate_only and mode_of(path) != "gate":
            continue
        started = data.get("startedAt", "")
        for c in data["cases"]:
            runs = c.get("arms", {}).get("with") or []
            if c["name"] not in only or not runs:
                continue
            if all(r.get("error") for r in runs):
                # A run that never started is scored as all-fail by the
                # CLI; it is not a bar.
                continue
            seen = invoked.setdefault(c["name"], set())
            for r in runs:
                trace = r.get("tracePath") or ""
                if os.path.isfile(trace):
                    seen.update(re.findall(r'"skill": ?"kad-dev-team:([a-z-]+)"', open(trace).read()))
            if started > latest.get(c["name"], ("",))[0]:
                latest[c["name"]] = (started, path, data, c)
    table = json.load(open(OUT)) if os.path.isfile(OUT) else {}
    for name in cases:
        if name not in only:
            continue
        if name not in latest:
            print(f"no result for {name}; left as it was", file=sys.stderr)
            continue
        _, path, data, c = latest[name]
        mode = mode_of(path)
        if mode != "gate":
            print(f"{name}: bar recorded from a calibration run, not a gate run; "
                  f"skill-invoked graders are scored differently there", file=sys.stderr)
        entry = {
            "score": round(c["aggregates"]["score"], 3),
            "runs": len(c["arms"]["with"]),
            "mode": mode,
            "claude_version": data.get("claudeVersion"),
            "source": os.path.relpath(path, EVALS).replace(os.sep, "/"),
            "graders": grader_rates(c),
        }
        skills = sorted(invoked.get(name, set()) | set(table.get(name, {}).get("skills_invoked", [])))
        if skills:
            entry["skills_invoked"] = skills
        table[name] = entry
    table = {k: table[k] for k in sorted(table) if k in cases}
    with open(OUT, "w") as f:
        json.dump(table, f, indent=2)
        f.write("\n")
    print(f"wrote {len(table)} cases to {os.path.relpath(OUT, os.getcwd())}")


if __name__ == "__main__":
    main()
