#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/cancel-hold
cp -R "$here/../fixtures/library-app/planning/cancel-hold-consequence/." docs/cancel-hold/
