#!/usr/bin/env python3
"""The per-case table of a with/without pass (TODO.md, E6), as markdown.

Reads `<out>/aggregate-result.json` written by `ablation_run.py` and, when
it is there, `<out>/pairwise.json` written by `pairwise_judge.py`. Per case:
the mean score of each arm over its clean runs, every scored grader whose
pass count differs between the arms, the graders both arms fail, the
pairwise tally, and the mean cost of one run of each arm, errored runs
included (agent and judge apart; a run's `costUsd` includes its
`judgeCostUsd`). The with-only
graders (`tool_used: Skill`, `arm: with-only`) are indicators, not scored,
and are left out of the comparison.

Usage: python3 -I evals/tools/ablation_report.py ~/kad-eval-ablation/<name>
"""
import json
import os
import sys

ARMS = ("with", "without")


def errored(run):
    return bool(run.get("error")) or any(
        str(g.get("explanation", "")).startswith("grader threw") for g in run.get("graders", []))


def main():
    out = os.path.expanduser(sys.argv[1])
    data = json.load(open(os.path.join(out, "aggregate-result.json"), encoding="utf-8"))
    try:
        pairwise = json.load(open(os.path.join(out, "pairwise.json"), encoding="utf-8"))
    except OSError:
        pairwise = {"summary": {}, "cost_usd": 0.0}
    print("| Case | With | Without | Graders that differ (with, without) | Both arms fail | Pairwise (with / without / tie / split) | One run: with, without (of which judge) |")
    print("|---|---|---|---|---|---|---|")
    total = {arm: [0.0, 0.0, 0] for arm in ARMS}
    for case in sorted(data["cases"], key=lambda c: c["name"]):
        clean = {arm: [r for r in case["arms"].get(arm) or [] if not errored(r)] for arm in ARMS}
        rates, cost = {}, {}
        for arm in ARMS:
            for run in clean[arm]:
                for g in run["graders"]:
                    if g.get("scored") is False:
                        continue
                    rates.setdefault(g["name"], {a: 0 for a in ARMS})[arm] += 1 if g.get("passed") else 0
            ran = case["arms"].get(arm) or []  # errored runs were paid for too
            cost[arm] = (sum(r.get("costUsd") or 0 for r in ran) / (len(ran) or 1),
                         sum(r.get("judgeCostUsd") or 0 for r in ran) / (len(ran) or 1))
            total[arm][0] += sum(r.get("costUsd") or 0 for r in case["arms"].get(arm) or [])
            total[arm][1] += sum(r.get("judgeCostUsd") or 0 for r in case["arms"].get(arm) or [])
            total[arm][2] += len(case["arms"].get(arm) or [])
        n = {arm: len(clean[arm]) for arm in ARMS}
        score = {arm: (sum(r["score"] for r in clean[arm]) / n[arm]) if n[arm] else float("nan") for arm in ARMS}
        differ = [f"`{name}` {r['with']}/{n['with']}, {r['without']}/{n['without']}"
                  for name, r in rates.items() if n["with"] and n["without"] and r["with"] * n["without"] != r["without"] * n["with"]]
        both = [f"`{name}` {r['with']}/{n['with']}, {r['without']}/{n['without']}" for name, r in rates.items()
                if n["with"] and n["without"] and r["with"] * n["without"] == r["without"] * n["with"] and r["with"] < n["with"]]
        t = pairwise["summary"].get(case["name"])
        pw = f"{t['with']} / {t['without']} / {t['tie']} / {t['split']}" if t else "not run"
        if t and t.get("no verdict"):
            pw += f" ({t['no verdict']} with no verdict: a judge call failed)"
        shown = {arm: f"{score[arm]:.2f}" if n[arm] else "no clean run" for arm in ARMS}
        print(f"| `{case['name']}` | {shown['with']} | {shown['without']} | {'; '.join(differ) or 'none'} | "
              f"{'; '.join(both) or 'none'} | {pw} | ${cost['with'][0]:.2f} (${cost['with'][1]:.2f}), "
              f"${cost['without'][0]:.2f} (${cost['without'][1]:.2f}) |")
    print()
    for arm in ARMS:
        c, j, runs = total[arm]
        print(f"{arm}: {runs} runs, ${c:.2f} (judges ${j:.2f})")
    print(f"pairwise judge: ${pairwise.get('cost_usd', 0):.2f}")
    print(f"CLI total: ${data.get('costUsd', 0):.2f}")


if __name__ == "__main__":
    main()
