#!/usr/bin/env bash
# The chunk loop's `slice-review-r0` state, built by
# fixtures/library-app/code-plants/loop/state.sh (everything under
# fixtures/library-app/code-plants/loop/ is loaded), with the slice's
# reliability document committed as planning (R3, the pickup shelf's
# criterion) and one more commit on the slice branch that meets it word
# for word (no-exit.sh, answer key L17).
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/state.sh" slice-review-r0
bash "$here/../fixtures/library-app/code-plants/loop/no-exit.sh" criterion
