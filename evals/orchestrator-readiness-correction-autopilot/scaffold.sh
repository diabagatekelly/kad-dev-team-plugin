#!/usr/bin/env bash
# The loop's base (fixtures/library-app/code-plants/loop/base.sh over the
# route-plants/cancel-hold planning set; everything under
# fixtures/library-app/code-plants/loop/ is loaded), with two things of
# this case's own: the owner's autopilot answer (the short one, which
# says yes and names no stop, so the skill's account of the stops is the
# only one), and the design's `Kept for later slices` section under
# another heading. Its content is untouched, so the readiness gate fails
# one check (`kept-for-later-slices`) on a correction that changes no
# decision.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
loop="$here/../fixtures/library-app/code-plants/loop"
bash "$loop/base.sh" "$here/../fixtures/library-app/route-plants/cancel-hold"
sed -i.bak 's/^## Kept for later slices$/## What the next slice reads/' docs/cancel-hold/design-001.md
rm -f docs/cancel-hold/design-001.md.bak
grep -q '^## What the next slice reads$' docs/cancel-hold/design-001.md
cp "$loop/docs/autopilot-short.md" docs/cancel-hold/autopilot.md
git add docs/cancel-hold/design-001.md docs/cancel-hold/autopilot.md
git commit -qm "Planning: the design as approved, the owner's autopilot answer"
git push -q origin main
mkdir -p tools
cp "$loop/tools/gh" tools/gh
chmod +x tools/gh
printf 'tools/\n' >> .git/info/exclude
