#!/usr/bin/env bash
# The library app with the cancel-hold slice planned as far as its design,
# the pickup shelf in it (fixtures/library-app/planning/cancel-hold-shelf/):
# the slice's reliability line is still a placeholder.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/cancel-hold
cp -R "$here/../fixtures/library-app/planning/cancel-hold-shelf/." docs/cancel-hold/
