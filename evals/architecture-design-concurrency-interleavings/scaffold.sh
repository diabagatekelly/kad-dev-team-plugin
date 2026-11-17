#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/nightly-run
cp -R "$here/../fixtures/library-app/planning/nightly-single-run/." docs/nightly-run/
