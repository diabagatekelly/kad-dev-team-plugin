#!/usr/bin/env bash
# The fully planned cancel-hold slice in a repository with a remote
# (fixtures/library-app/code-plants/loop/base.sh over the
# fixtures/library-app/route-plants/cancel-hold/ planning set), the owner's
# fee export in owner-files/ (ignored by git) and its listing committed in
# docs/cancel-hold/sources.md, the slice file's thin path carrying one row of
# the export (fixtures/library-app/source-plants/: install.sh,
# slice-001-cancel-hold-with-row.md; answer key PD2), and the loop fixture's
# quiet GitHub CLI stand-in at tools/gh.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
fx="$here/../fixtures/library-app"
bash "$fx/code-plants/loop/base.sh" "$fx/route-plants/cancel-hold"
bash "$fx/source-plants/install.sh" docs/cancel-hold
cp "$fx/source-plants/slice-001-cancel-hold-with-row.md" docs/cancel-hold/slice-001.md
git add docs/cancel-hold/sources.md docs/cancel-hold/slice-001.md
git commit -qm "Planning: the fee export listed as a source, an example on slice 001"
git push -q origin main
mkdir -p tools
cp "$fx/code-plants/loop/tools/gh" tools/gh
chmod +x tools/gh
printf 'tools/\n' >> .git/info/exclude
