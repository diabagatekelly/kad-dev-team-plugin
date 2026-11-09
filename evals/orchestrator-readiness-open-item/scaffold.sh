#!/usr/bin/env bash
# The fully planned cancel-hold slice in a repository with a remote
# (fixtures/library-app/code-plants/loop/base.sh over the
# fixtures/library-app/route-plants/cancel-hold/ planning set), its slice
# file's Explicitly deferred section gaining one item marked as a blocker,
# and the loop fixture's quiet GitHub CLI stand-in at tools/gh.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/base.sh" "$here/../fixtures/library-app/route-plants/cancel-hold"
printf -- '- Restoring a hold a member cancelled by mistake. Blocker: a member who cancels by mistake has no way back, and nothing says whether restoring is this slice'"'"'s or a later one'"'"'s.\n' >> docs/cancel-hold/slice-001.md
git add docs/cancel-hold/slice-001.md
git commit -qm "Planning: an open item on slice 001"
git push -q origin main
mkdir -p tools
cp "$here/../fixtures/library-app/code-plants/loop/tools/gh" tools/gh
chmod +x tools/gh
printf 'tools/\n' >> .git/info/exclude
