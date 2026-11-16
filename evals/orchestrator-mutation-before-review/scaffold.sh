#!/usr/bin/env bash
# The chunk loop's `slice-review-r0` state, built by
# fixtures/library-app/code-plants/loop/state.sh (everything under
# fixtures/library-app/code-plants/loop/ is loaded) over the app, the
# fixtures/library-app/code-plants/tdd/ runner and the
# fixtures/library-app/route-plants/cancel-hold/ planning set, taken one
# step back: the mutation report that state produced is removed and the
# handoff says the Definition of Done is behind and names nothing after it.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/state.sh" slice-review-r0
records=docs/cancel-hold/implementation
rm -f "$records/slice-mutation.md"
for py in python3 python; do
  if "$py" -I -c "pass" >/dev/null 2>&1; then break; fi
done
"$py" -I - "$records/handoff-slice-001.md" <<'PY'
import re, sys
path = sys.argv[1]
text = open(path, encoding="utf-8").read()
text, a = re.subn(r"(?m)^- \*\*State:\*\* .*$",
                  "- **State:** D.2 done: the Definition of Done was acted on in one batch (the README, one comments review, one fixer, "
                  "the gate) and checked again; every check passes but comment density, which stands as a Medium for the pull request's body",
                  text)
text, b = re.subn(r"(?m)^- \*\*Next action:\*\* .*$", "- **Next action:** the rest of D", text)
text, c = re.subn(r"(?m)^- \*\*Standing:\*\* .*$", "- **Standing:** comment density (Medium, Definition of Done)", text)
if (a, b, c) != (1, 1, 1):
    sys.exit(f"scaffold: the handoff's State, Next action and Standing lines were not each found once ({a}, {b}, {c})")
open(path, "w", encoding="utf-8", newline="\n").write(text)
PY
git add "$records/handoff-slice-001.md"
git commit -q --amend --no-edit
