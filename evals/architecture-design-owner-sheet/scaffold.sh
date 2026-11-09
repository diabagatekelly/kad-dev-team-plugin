#!/usr/bin/env bash
# The pay-fine planning set up to the slice and its story over the library
# app, the owner's fee export in owner-files/ and its listing in
# docs/pay-fine/sources.md (fixtures/library-app/source-plants/install.sh).
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/pay-fine
cp -R "$here/../fixtures/library-app/planning/pay-fine-design/." docs/pay-fine/
bash "$here/../fixtures/library-app/source-plants/install.sh" docs/pay-fine
