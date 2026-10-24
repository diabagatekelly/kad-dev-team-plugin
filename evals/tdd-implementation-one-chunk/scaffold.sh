#!/usr/bin/env bash
# The cancel-hold slice's documents, a planned implementation report with
# three chunks, and a git repository on the slice branch with the plan
# committed, the way the orchestrator's B step leaves things for chunk 1.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/cancel-hold
cp -R "$here/../fixtures/library-app/route-plants/cancel-hold/." docs/cancel-hold/
cp -R "$here/../fixtures/library-app/code-plants/chunk/." .
# The in-place test runner the tdd cases plant (`npm test` runs the .ts
# tests without a build); without it every implementer spends its turns
# inventing one, and the test-run graders cannot see those runs.
cp "$here/../fixtures/library-app/code-plants/tdd/package.json" package.json
cp "$here/../fixtures/library-app/code-plants/tdd/test/ts-resolve.mjs" test/ts-resolve.mjs
git init -q
git config user.name "library-app"
git config user.email "library-app@example.test"
git config commit.gpgsign false
git checkout -q -b slice-001-cancel-hold
git add -A
git commit -q -m "Plan: slice 001 in 3 chunks"
