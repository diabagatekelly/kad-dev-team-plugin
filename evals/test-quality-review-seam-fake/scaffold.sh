#!/usr/bin/env bash
# Chunk 1 of the cancel-hold slice built with every test faking the HoldQueue
# port by hand and no seam test (fixtures/library-app/code-plants/loop/,
# snapshot seam-fake), with the plan that names the seam test, over the app,
# the fixtures/library-app/code-plants/tdd/ runner and the
# fixtures/library-app/route-plants/cancel-hold/ planning set.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
loop="$here/../fixtures/library-app/code-plants/loop"
bash "$loop/base.sh" "$here/../fixtures/library-app/route-plants/cancel-hold"
git checkout -q -b slice-001-cancel-hold
mkdir -p docs/cancel-hold/implementation
cp "$loop/docs/implementation-report-plan.md" docs/cancel-hold/implementation/implementation-report-slice-001.md
git add docs/cancel-hold/implementation/implementation-report-slice-001.md
git commit -qm "Plan: slice 001 in 3 chunks"
cp -R "$loop/snapshots/seam-fake/." .
sed 's|@DEVIATION@|none|' "$loop/docs/chunk-1-section.md" >> docs/cancel-hold/implementation/implementation-report-slice-001.md
git add lending infra test docs/cancel-hold/implementation/implementation-report-slice-001.md
git commit -qm "Cancel a member's hold on a title"
