#!/usr/bin/env bash
# The fully planned cancel-hold slice in a repository with a remote
# (fixtures/library-app/code-plants/loop/base.sh over the
# fixtures/library-app/route-plants/cancel-hold/ planning set), plus the
# open-work stand-in for the GitHub CLI at tools/gh
# (fixtures/library-app/route-plants/open-work/gh): one open pull request
# from a slice branch with two unresolved comments, one open High issue.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/base.sh" "$here/../fixtures/library-app/route-plants/cancel-hold"
mkdir -p tools
cp "$here/../fixtures/library-app/route-plants/open-work/gh" tools/gh
chmod +x tools/gh
printf 'tools/\n' >> .git/info/exclude
