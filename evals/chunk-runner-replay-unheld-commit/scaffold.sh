#!/usr/bin/env bash
# The chunk loop's `planned` state, built by
# fixtures/library-app/code-plants/loop/state.sh (everything under
# fixtures/library-app/code-plants/loop/ is loaded) over the app, the
# fixtures/library-app/code-plants/tdd/ runner and the
# fixtures/library-app/route-plants/cancel-hold/ planning set, then the
# repository the history was captured on
# (fixtures/library-app/replay/chunk-runner-wait/restore.sh: the same
# commits under the hashes the captured runner already read).
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/state.sh" planned
bash "$here/../fixtures/library-app/replay/chunk-runner-wait/restore.sh"
