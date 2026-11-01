#!/usr/bin/env bash
# The cancel-a-hold problem and its Active requirements, whose first slice
# needs no screen (the staff route is a later slice), for the slicer's
# not-applicable accessibility line.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/cancel-hold
cp "$here/../fixtures/library-app/planning/cancel-hold-consequence/problem.md" "$here/../fixtures/library-app/planning/cancel-hold-consequence/requirements-001.md" docs/cancel-hold/
