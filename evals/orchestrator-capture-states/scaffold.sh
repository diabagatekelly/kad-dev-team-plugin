#!/usr/bin/env bash
# The chunk loop's `delivery-ready-ui` state, built by
# fixtures/library-app/code-plants/loop/state.sh (everything under
# fixtures/library-app/code-plants/loop/ is loaded) over the app, the
# fixtures/library-app/code-plants/tdd/ runner and the
# fixtures/library-app/route-plants/cancel-hold/ planning set.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/state.sh" delivery-ready-ui
# The stand-in's header says in plain words that nothing reaches GitHub;
# runs that read it declined to call anything delivered
# (orchestrator-delivery-foreground, 2026-11-16). The comments go; the
# stand-in answers as before.
sed -i.bak -e '1!{/^[[:space:]]*#/d;}' tools/gh && rm -f tools/gh.bak
