#!/usr/bin/env bash
# Chunk 1 of the cancel-hold slice built and reviewed, the review rating one
# finding needs-decision (devsecops-engineer:reliability-requirements):
# fixtures/library-app/code-plants/loop/base.sh (everything under
# fixtures/library-app/code-plants/loop/) over the app, the
# fixtures/library-app/code-plants/tdd/ runner and the
# fixtures/library-app/route-plants/cancel-hold/ planning set, with the
# slice pointing at its reliability document.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
loop="$here/../fixtures/library-app/code-plants/loop"
bash "$loop/base.sh" "$here/../fixtures/library-app/route-plants/cancel-hold"
cp "$loop/docs/slice-001-with-pointer.md" docs/cancel-hold/slice-001.md
cp "$loop/docs/reliability-slice-001.md" docs/cancel-hold/reliability-slice-001.md
git checkout -q -b slice-001-cancel-hold
git add docs/cancel-hold
git commit -qm "Planning: slice 001 ready for implementation"
mkdir -p docs/cancel-hold/implementation
cp "$loop/docs/implementation-report-plan.md" docs/cancel-hold/implementation/implementation-report-slice-001.md
git add docs/cancel-hold/implementation/implementation-report-slice-001.md
git commit -qm "Plan: slice 001 in 3 chunks"
plan="$(git rev-parse --short HEAD)"
cp -R "$loop/snapshots/chunk1/." .
sed 's|@DEVIATION@|none|' "$loop/docs/chunk-1-section.md" >> docs/cancel-hold/implementation/implementation-report-slice-001.md
git add lending infra test docs/cancel-hold/implementation/implementation-report-slice-001.md
git commit -qm "Cancel a member's hold on a title"
sed "s/@PLAN@/$plan/; s/@C1@/$(git rev-parse --short HEAD)/" "$loop/records/chunk-1-r0-review-gap.md" > docs/cancel-hold/implementation/chunk-1-r0-review.md
