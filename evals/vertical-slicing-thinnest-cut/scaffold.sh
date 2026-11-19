#!/usr/bin/env bash
# The library app with the renew-a-loan problem and its agreed
# requirements (fixtures/library-app/planning/renew-loan/): six confirmed
# behaviours, no slice yet.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/renew-loan
cp "$here/../fixtures/library-app/planning/renew-loan/problem.md" "$here/../fixtures/library-app/planning/renew-loan/requirements-001.md" docs/renew-loan/
