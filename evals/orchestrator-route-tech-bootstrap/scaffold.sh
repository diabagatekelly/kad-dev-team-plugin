#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
mkdir -p docs/cancel-hold
cp -R "$here/../fixtures/library-app/route-plants/cancel-hold/." docs/cancel-hold/
