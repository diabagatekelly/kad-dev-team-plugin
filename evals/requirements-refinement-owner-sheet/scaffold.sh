#!/usr/bin/env bash
# The pay-fine problem doc over the library app, and the owner's fee export
# in owner-files/ (fixtures/library-app/source-plants/install.sh; no
# sources.md yet: listing the file is the skill's first step).
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/pay-fine
cp "$here/../fixtures/library-app/planning/pay-fine-design/problem.md" docs/pay-fine/
bash "$here/../fixtures/library-app/source-plants/install.sh"
