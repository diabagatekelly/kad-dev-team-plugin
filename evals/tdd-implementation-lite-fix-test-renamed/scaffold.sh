#!/usr/bin/env bash
# The chunk loop's `chunk1-gated` state, built by
# fixtures/library-app/code-plants/loop/state.sh (everything under
# fixtures/library-app/code-plants/loop/ is loaded), then one step further:
# after-state.sh's `named-test` (its header says what that leaves).
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/state.sh" chunk1-gated
bash "$here/../fixtures/library-app/code-plants/loop/after-state.sh" named-test
