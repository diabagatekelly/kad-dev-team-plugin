#!/usr/bin/env bash
# The chunk loop's `issue14-planned` state (state.sh; everything under
# fixtures/library-app/code-plants/loop/ is loaded), on a project that
# never had gate checks: the file and its stand-in tool are removed in a
# commit of their own, and the target directory holds no
# technology-bootstrap document, so there is no Gate checks section.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/code-plants/loop/state.sh" issue14-planned
git rm -q gate-checks.json tools/gate-check.py
git commit -qm "The project has no gate checks yet"
