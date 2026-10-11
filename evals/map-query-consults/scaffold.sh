#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
cp -R "$here/../fixtures/library-app/code-plants/map/query/." .
