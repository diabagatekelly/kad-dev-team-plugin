#!/usr/bin/env bash
# The chunk loop's `issue14-planned` state, built by
# fixtures/library-app/code-plants/loop/state.sh (everything under
# fixtures/library-app/code-plants/loop/ is loaded) over the app, the
# fixtures/library-app/code-plants/tdd/ runner and the
# fixtures/library-app/route-plants/cancel-hold/ planning set with the reliability document, the built slice and the
# issue-fix planning plants (docs/issue14-*.md, docs/issues-high-14.json).
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/state.sh" issue14-planned
