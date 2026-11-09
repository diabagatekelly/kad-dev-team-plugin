#!/usr/bin/env bash
# The chunk loop's `chunk1-source-value` state, built by
# fixtures/library-app/code-plants/loop/state.sh (everything under
# fixtures/library-app/code-plants/loop/ is loaded) over the app, the
# fixtures/library-app/code-plants/tdd/ runner, the
# fixtures/library-app/route-plants/cancel-hold/ planning set and the owner's
# fee export from fixtures/library-app/source-plants/ (answer key PD4).
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/state.sh" chunk1-source-value
