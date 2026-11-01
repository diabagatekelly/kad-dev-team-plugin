#!/usr/bin/env bash
# The ground every chunk-loop case stands on: the library app with the
# in-place test runner and the loop fixture's manifest, linter and
# formatter configuration and tool stand-ins, one planning set copied into
# docs/cancel-hold/, the planning-stage log entries, and a git repository
# on `main` with one commit and a local bare `origin` (the loop's A step
# refuses to start without a remote, and delivery pushes to it).
#
# Usage, from the eval run's working directory:
#   bash base.sh <planning directory>     (e.g. the fixture's route-plants/cancel-hold)
set -euo pipefail

planning="${1:?usage: base.sh <planning directory>}"
loop="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fixture="$(cd "$loop/../.." && pwd)"
target=docs/cancel-hold

bash "$fixture/scaffold.sh"
mkdir -p "$target"
cp -R "$planning/." "$target/"
cp "$fixture/code-plants/tdd/test/ts-resolve.mjs" test/ts-resolve.mjs
cp "$loop/package.json" package.json
cp "$loop/eslint.config.js" eslint.config.js
cp "$loop/.prettierrc" .prettierrc
mkdir -p node_modules/.bin
cp "$loop/bin/eslint" "$loop/bin/tsc" node_modules/.bin/
chmod +x node_modules/.bin/eslint node_modules/.bin/tsc
cp "$loop/docs/orchestrator-log-planning.md" "$target/orchestrator-log.md"
printf 'node_modules/\ndist/\n' > .gitignore
git init -q
git config user.name "library-app"
git config user.email "library-app@example.test"
git config commit.gpgsign false
git checkout -q -b main
git add -A
git commit -qm "Library lending service"
git init -q --bare .git/origin.git
# Windows caps paths at 260 characters; a bare repository deep in a temp
# directory needs this to receive a pack. A no-op elsewhere.
git config core.longpaths true
git --git-dir=.git/origin.git config core.longpaths true
git remote add origin "$PWD/.git/origin.git"
git push -q origin main
