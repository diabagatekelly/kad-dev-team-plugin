#!/usr/bin/env bash
# The fully planned cancel-hold slice in a repository with a remote
# (fixtures/library-app/code-plants/loop/base.sh over the
# fixtures/library-app/route-plants/cancel-hold/ planning set), the
# planning pull request stand-in for the GitHub CLI at tools/gh in mode
# `none` (nothing open), and a plan that is not on the default branch:
# the slice file has gained its size line since the last commit, so it
# differs from `origin/main`.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/base.sh" "$here/../fixtures/library-app/route-plants/cancel-hold"
# The remote must look like GitHub for the open-work step to ask the
# tracker; a fetch fails and the local `origin/main` is what is compared.
git remote set-url origin https://github.com/example/library-lending.git
mkdir -p tools
cp "$here/../fixtures/library-app/route-plants/planning-pr/gh" tools/gh
chmod +x tools/gh
printf 'none\n' > tools/gh-mode
printf 'tools/\n' >> .git/info/exclude
printf '\n## Size\n\nCriteria: 2 functional; chunks expected: 1\n' >> docs/cancel-hold/slice-001.md
