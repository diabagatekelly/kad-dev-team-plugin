"""Write evals/thresholds.json: each case's bar for the eval gate.

For every case directory, takes the most recent `--json` result in
`evals/results/` that ran it (with the plugin) and records:
- `score`: that run's aggregate score (mean over runs of the share of
  graders passed), the bar `eval_gate.py` compares against;
- `runs`, `claude_version` and `source` (the result file) for context;
- `skills_invoked`: every `kad-dev-team` skill seen called in any kept
  trace of the case, which `affected_cases.py` uses to catch consults.

Re-run it after a deliberate change moves a case's score, and commit the
file with that change, so the gate measures against the new bar.

Usage: python3 -I evals/tools/record_thresholds.py [--exclude GLOB ...] [case ...]
  With case names, updates only those entries. --exclude skips result files
  whose name matches (for runs of a skill version that was reverted).
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


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--exclude", action="append", default=[])
    p.add_argument("cases", nargs="*")
    a = p.parse_args()
    cases = list(affected_cases.case_dirs())
    only = set(a.cases) or set(cases)
    latest, invoked = {}, {}
    for path, data in results(a.exclude):
        started = data.get("startedAt", "")
        for c in data["cases"]:
            runs = c.get("arms", {}).get("with") or []
            if c["name"] not in only or not runs:
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
        entry = {
            "score": round(c["aggregates"]["score"], 3),
            "runs": len(c["arms"]["with"]),
            "claude_version": data.get("claudeVersion"),
            "source": os.path.relpath(path, EVALS),
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
