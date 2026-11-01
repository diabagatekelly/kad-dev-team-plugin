#!/usr/bin/env bash
# The fully planned, UI-touching cancel-hold slice (security, reliability
# and accessibility documents filled, a screen design) with its
# accessibility line replaced by the slicer's not-applicable line: a slice
# whose line disagrees with its thin path.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/cancel-hold
cp -R "$here/../fixtures/library-app/planning/cancel-hold-readiness/." docs/cancel-hold/
python3 -I - docs/cancel-hold/slice-001.md <<'PY'
import sys
p = sys.argv[1]
lines = open(p).read().split("\n")
out, done = [], False
for l in lines:
    if not done and "ccessibility" in l and l.startswith("- "):
        out.append("- Accessibility: not applicable, this slice has no screen")
        out.append("  (`accessibility-engineer:accessibility-review` when one is added).")
        done = True
        continue
    if done and l.startswith("  ") and not l.startswith("  ("):
        continue  # the replaced line's continuation
    done_cont = False
    out.append(l)
assert done, "no accessibility line to replace"
open(p, "w").write("\n".join(out))
PY
