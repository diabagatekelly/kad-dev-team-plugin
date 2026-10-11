#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs
cp -R "$here/../fixtures/library-app/docs-plants/staleness/docs/." docs/
