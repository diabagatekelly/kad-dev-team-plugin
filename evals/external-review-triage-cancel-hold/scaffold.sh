#!/usr/bin/env bash
# The cancel-hold slice as delivered: its documents, the implementation
# report, the code after two chunks and one fix round, the plugin's own
# reviewer reports and sidecar, and the external reviewer's comments
# `delivery` collected on the pull request.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/cancel-hold
cp -R "$here/../fixtures/library-app/route-plants/cancel-hold/." docs/cancel-hold/
cp -R "$here/../fixtures/library-app/code-plants/triage/." .
