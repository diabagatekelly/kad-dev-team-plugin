#!/usr/bin/env bash
# The chunk loop's `slice-built` state with a README already written: its
# "does not" list names a criterion the slice built (the rejection of a
# cancel for a hold the member does not have), as a README written before
# a criterion moved into the slice does. Beside the state's other two
# Definition of Done failures (a script body in a string, comment density).
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
loop="$here/../fixtures/library-app/code-plants/loop"
bash "$loop/state.sh" slice-built
sed 's/^- Not yet: the staff HTTP route, member self-service cancelling, telling$/- Not yet: the staff HTTP route, member self-service cancelling, turning down a cancel for a hold the member does not have, telling/' "$loop/docs/README-slice.md" > README.md
grep -q "turning down a cancel for a hold the member does not have" README.md
git add README.md
git -c user.email=loop@example.com -c user.name=loop commit -qm "README: clone to running, tests and checks, where things live, what this slice does"
