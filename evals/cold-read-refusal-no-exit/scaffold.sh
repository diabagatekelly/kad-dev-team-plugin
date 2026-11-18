#!/usr/bin/env bash
# The chunk loop's `slice-review-r0` state, built by
# fixtures/library-app/code-plants/loop/state.sh (everything under
# fixtures/library-app/code-plants/loop/ is loaded), with one more commit
# on the slice branch: the pickup shelf (no-exit.sh, answer key L17).
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/state.sh" slice-review-r0
bash "$here/../fixtures/library-app/code-plants/loop/no-exit.sh"
