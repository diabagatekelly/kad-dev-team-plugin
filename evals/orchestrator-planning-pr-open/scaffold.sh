#!/usr/bin/env bash
# The fully planned cancel-hold slice in a repository with a remote
# (fixtures/library-app/code-plants/loop/base.sh over the
# fixtures/library-app/route-plants/cancel-hold/ planning set), plus the
# planning pull request stand-in for the GitHub CLI at tools/gh
# (fixtures/library-app/route-plants/planning-pr/gh, mode `open`): one
# open pull request, #9, from the planning branch of slice 1, its checks
# green, nothing to answer.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/base.sh" "$here/../fixtures/library-app/route-plants/cancel-hold"
# The remote must look like GitHub for the open-work step to ask the
# tracker; nothing here fetches or pushes.
git remote set-url origin https://github.com/example/library-lending.git
mkdir -p tools
cp "$here/../fixtures/library-app/route-plants/planning-pr/gh" tools/gh
chmod +x tools/gh
printf 'open\n' > tools/gh-mode
printf 'tools/\n' >> .git/info/exclude
