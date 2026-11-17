#!/usr/bin/env bash
# The cancel-hold slice, fully planned and passing the readiness gate, in a
# repository with a remote and its gate checks: the loop fixture's base
# (fixtures/library-app/code-plants/loop/base.sh; everything under
# fixtures/library-app/code-plants/loop/ is loaded) over the app, the
# fixtures/library-app/code-plants/tdd/ runner and the
# fixtures/library-app/route-plants/cancel-hold/ planning set. A first
# slice: no delegation file and no autopilot file.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/base.sh" "$here/../fixtures/library-app/route-plants/cancel-hold"
