"""Summarise gate result files (a results dir or a downloaded eval-results artifact):

usage: python -I summarize_results.py <results-dir> [thresholds.json]
"""
import glob, json, os, sys

d = sys.argv[1]
bars = json.load(open(sys.argv[2], encoding="utf-8")) if len(sys.argv) > 2 else {}
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

files = sorted(glob.glob(os.path.join(d, "gate-*.json")))
print(len(files), "result files")
totals = {"cases": 0, "below": 0, "errored": 0}
for f in files:
    try:
        data = json.load(open(f, encoding="utf-8"))
    except Exception as e:
        print("UNREADABLE", f, e); continue
    for c in data["cases"]:
        runs = c["arms"]["with"]
        name = c["name"]
        bar = bars.get(name, {})
        scores = [r.get("score") for r in runs]
        errs = [r.get("error") for r in runs if r.get("error")]
        avg = sum(s or 0 for s in scores) / max(len(scores), 1)
        flag = ""
        if errs and len(errs) == len(runs):
            flag = "ALL ERRORED"; totals["errored"] += 1
        elif bar and avg < bar.get("score", 0) - 1e-9:
            flag = f"BELOW BAR {bar.get('score')}"; totals["below"] += 1
        totals["cases"] += 1
        print(f"\n=== {name}  score={avg:.2f} runs={len(runs)} turns={[r.get('turns') for r in runs]} "
              f"cost=${sum(r.get('costUsd') or 0 for r in runs):.2f} {flag}  [{os.path.basename(f)}]")
        for e in errs:
            print("   error:", str(e)[:300])
        for i, r in enumerate(runs):
            for g in r.get("graders", []):
                if g.get("scored") is False:
                    continue
                if not g.get("passed"):
                    bar_rate = bar.get("graders", {}).get(g["name"])
                    tag = " (always passed at bar)" if bar_rate == 1 else ""
                    print(f"   run{i} FAIL {g['name']}{tag}")
                    ex = (g.get("explanation") or "").strip().replace("\n", "\n        ")
                    print("        " + ex[:900])
print("\n", totals)
