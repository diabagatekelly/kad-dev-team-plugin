#!/usr/bin/env bash
# One more commit on the slice branch of a built slice (run after
# `state.sh slice-review-r0`): the snapshot `slice-no-exit`, the pickup
# shelf. A hold whose copy is set aside is cancelled by releasing the copy
# first, and collected by handing it over. Planted (answer key L17): when
# the shelf refuses the release for good (the copy is not found), the
# cancel is turned down and the hold kept, collecting is turned down too,
# and a hold placed again queues behind the one that cannot leave, so
# that title's queue never moves again. Every line does what its test
# says; nothing in the code is wrong line by line.
#
# Usage, from the eval run's working directory:
#   bash no-exit.sh [criterion]
# `criterion`: the slice's reliability document is committed as planning
# too, with R3, the criterion the cancel's refusal meets word for word.
set -euo pipefail
loop="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
target=docs/cancel-hold

if [ "${1:-}" = criterion ]; then
  cp "$loop/docs/reliability-slice-001-shelf.md" "$target/reliability-slice-001.md"
  git add "$target/reliability-slice-001.md"
  git commit -qm "Planning: reliability criteria for slice 001, the pickup shelf among them"
fi
cp -R "$loop/snapshots/slice-no-exit/." .
for py in python3 python; do
  if "$py" -I -c "pass" >/dev/null 2>&1; then break; fi
done
"$py" -I - README.md <<'PY'
import sys
path = sys.argv[1]
text = open(path, encoding="utf-8").read()
before = "- Not yet: the staff HTTP route"
if text.count(before) != 1:
    sys.exit("no-exit.sh: the README's 'Not yet' line was not found once")
added = ("- Puts a copy set aside for a hold back into circulation when that hold\n"
         "  is cancelled, and turns the cancel down, with nothing changed, when\n"
         "  the pickup shelf does not release the copy.\n"
         "- Hands the copy set aside to the member who is next, and takes their\n"
         "  hold off the queue.\n")
open(path, "w", encoding="utf-8", newline="\n").write(text.replace(before, added + before))
PY
git add README.md lending/pickup-shelf.ts lending/collect-hold.ts lending/cancel-hold.ts \
  infra/memory/in-memory-pickup-shelf.ts test/pickup-shelf.test.ts test/cancel-hold.test.ts \
  test/cancel-hold-again.test.ts test/cancel-hold-card-length.test.ts
git commit -q -F - <<'MSG'
Release the copy set aside when a hold is cancelled, and collect a hold

Delivers: the reliability criterion's pickup-shelf clause
Decided: a shelf that keeps the copy turns the cancel down and changes nothing
Deviation: none
MSG
