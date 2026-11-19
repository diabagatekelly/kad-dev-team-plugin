#!/usr/bin/env bash
# The cancel-hold slice, fully planned and passing the readiness gate (the
# loop fixture's base, fixtures/library-app/code-plants/loop/base.sh;
# everything under fixtures/library-app/code-plants/loop/ is loaded, over
# the fixtures/library-app/code-plants/tdd/ runner and the
# fixtures/library-app/route-plants/cancel-hold/ planning set), on a
# project whose standing file already holds the owner's autopilot answer
# and the line `cadence: solo` with their words, committed on main.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
loop="$here/../fixtures/library-app/code-plants/loop"
bash "$loop/base.sh" "$here/../fixtures/library-app/route-plants/cancel-hold"
cp "$loop/docs/autopilot-solo.md" docs/cancel-hold/autopilot.md
git add docs/cancel-hold/autopilot.md
git commit -qm "Planning: the owner's standing answers"
git push -q origin main
