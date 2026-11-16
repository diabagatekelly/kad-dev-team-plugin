#!/usr/bin/env bash
# Chunk 1 of the cancel-hold slice committed with WHAT-comments on every
# other line and one comment citing a planning decision
# (fixtures/library-app/code-plants/loop/, snapshot chunk1-comments), over
# the app, the fixtures/library-app/code-plants/tdd/ runner and the
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
cp -R "$loop/snapshots/chunk1-comments/." .
sed 's|@DEVIATION@|none|' "$loop/docs/chunk-1-section.md" >> docs/cancel-hold/implementation/implementation-report-slice-001.md
git add lending infra test docs/cancel-hold/implementation/implementation-report-slice-001.md
git commit -qm "Cancel a member's hold on a title"
# The gate's output on this commit, as the runner saves it before it
# launches the reviewer (0.15.0: the reviewer reads what the gate covers
# there; the first runs without it spent their hand-back saying so).
for py in python3 python; do
  if "$py" -I -c "pass" >/dev/null 2>&1; then break; fi
done
"$py" -I "$here/../../skills/orchestrator/scripts/validation_gate.py" --project . --base HEAD~1 --test-cmd 'npm test' \
  --allow lending/hold-queue.ts --allow lending/cancel-hold.ts --allow infra/memory/in-memory-hold-queue.ts \
  --allow test/cancel-hold.test.ts --allow test/in-memory-hold-queue.test.ts \
  --allow docs/cancel-hold/implementation/ --allow docs/cancel-hold/orchestrator-log.md \
  --module-dir lending/ --module-dir infra/memory/ --coverage --planning docs/cancel-hold \
  > docs/cancel-hold/implementation/gate-chunk-1-r0.txt 2>&1 || true
