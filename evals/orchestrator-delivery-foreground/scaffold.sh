#!/usr/bin/env bash
# The chunk loop's `delivery-ready` state, built by
# fixtures/library-app/code-plants/loop/state.sh (everything under
# fixtures/library-app/code-plants/loop/ is loaded) over the app, the
# fixtures/library-app/code-plants/tdd/ runner and the
# fixtures/library-app/route-plants/cancel-hold/ planning set.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/state.sh" delivery-ready
# The stand-in's header says in plain words that nothing reaches GitHub.
# Two runs of three (2026-11-16) read it, declined to call the slice
# delivered and stopped before the external review and the cost, which is
# honest and is not what this case is about. The comments go; the
# stand-in answers as before.
sed -i.bak -e '1!{/^[[:space:]]*#/d;}' tools/gh && rm -f tools/gh.bak
