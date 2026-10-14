#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
fx="$here/../fixtures/library-app"
bash "$fx/scaffold.sh"
mkdir -p docs/pay-fine
cp "$fx/planning/pay-fine-design/problem.md" "$fx/planning/pay-fine-design/requirements-001.md" "$fx/ui-plants/pay-fine/design-001.md" "$fx/ui-plants/pay-fine/slice-001.md" docs/pay-fine/

# The frozen phase 2 wrote three candidate mockups the user is now choosing
# from; a resumed run starts in a fresh sandbox, so put them back exactly as
# that turn wrote them. The skill rewrites the winner into visual-ux/ from
# the scratch file, which has to exist.
python3 -I "$here/../tools/history_files.py" "$here/history.jsonl" . --require

# "The second one" in this case's prompt is the second file the frozen turn
# listed. The winner-is-the-second-candidate grader checks the mockup
# written to visual-ux/ for that candidate's brand colour, so after a
# re-freeze both this value and the grader's pattern must be re-pinned
# from the new history; this check makes a stale pin fail here, loudly,
# instead of in a silently failing grader.
second="$(ls docs/pay-fine/design-candidates/*.html | sort | sed -n 2p)"
grep -q '#184A82' "$second" || { echo "second candidate $second lacks the pinned brand colour #184A82; re-pin it from history.jsonl" >&2; exit 1; }
