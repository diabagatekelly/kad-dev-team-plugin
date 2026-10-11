#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/cancel-hold
cp -R "$here/../fixtures/library-app/route-plants/cancel-hold/." docs/cancel-hold/
cp "$here/../fixtures/library-app/route-plants/cancel-hold-reliability-open/slice-001.md" docs/cancel-hold/
