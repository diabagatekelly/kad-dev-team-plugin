"""Print what the judge was shown for every failed grader of a case, from report.html.

usage: python -I report_evidence.py <results-dir> <case> [chars] [grader-regex]
"""
import glob, html as H, json, os, re, sys

d, case = sys.argv[1], sys.argv[2]
chars = int(sys.argv[3]) if len(sys.argv) > 3 else 1800
only = re.compile(sys.argv[4]) if len(sys.argv) > 4 else None
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

for folder in sorted(glob.glob(os.path.join(d, "2026-*"))):
    agg = os.path.join(folder, "aggregate-result.json")
    if not os.path.isfile(agg):
        continue
    a = json.load(open(agg, encoding="utf-8"))
    if not any(c["name"] == case for c in a.get("cases", [])):
        continue
    h = open(os.path.join(folder, "report.html"), encoding="utf-8", errors="replace").read()
    h = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", "", h)
    t = H.unescape(re.sub(r"<[^>]+>", "\n", h))
    t = re.sub(r"\n\s*\n+", "\n", t)
    print("\n################", os.path.basename(folder), case)
    for m in re.finditer(r"✗ fail\n([^\n]+)\n", t):
        name = m.group(1).strip()
        if only and not only.search(name):
            continue
        print("\n---- FAIL", name)
        print(t[m.end(): m.end() + chars])
