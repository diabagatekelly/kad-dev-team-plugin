#!/usr/bin/env bash
# The chunk loop's `solo-unconfirmed` state (the `solo` cadence as far as
# S.5: built, gated, the readers' reports recorded, the verify report in
# hand, and nothing confirmed by execution), built by
# fixtures/library-app/code-plants/loop/state.sh (everything under
# fixtures/library-app/code-plants/loop/ is loaded) over the app, the
# fixtures/library-app/code-plants/tdd/ runner and the
# fixtures/library-app/route-plants/cancel-hold/ planning set.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/state.sh" solo-unconfirmed
