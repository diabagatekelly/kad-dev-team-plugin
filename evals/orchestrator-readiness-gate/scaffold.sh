#!/usr/bin/env bash
# The cancel-hold slice with a desk screen, fully planned, in a repository
# with a remote: fixtures/library-app/code-plants/loop/base.sh (the loop
# fixture's manifest and tool stand-ins, everything under
# fixtures/library-app/code-plants/loop/) over the app, the
# fixtures/library-app/code-plants/tdd/ runner and the
# fixtures/library-app/planning/cancel-hold-readiness/ planning set, whose
# reliability document says "a few times" and whose screen design has no
# mockup for the unreachable-queue state.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/base.sh" "$here/../fixtures/library-app/planning/cancel-hold-readiness"
