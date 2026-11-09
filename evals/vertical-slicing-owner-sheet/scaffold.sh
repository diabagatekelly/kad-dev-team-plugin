#!/usr/bin/env bash
# The pay-fine problem doc and agreed requirements over the library app, the
# owner's fee export in owner-files/ and its listing in docs/pay-fine/sources.md
# (fixtures/library-app/source-plants/install.sh).
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/pay-fine
cp "$here/../fixtures/library-app/planning/pay-fine-design/problem.md" "$here/../fixtures/library-app/planning/pay-fine-design/requirements-001.md" docs/pay-fine/
bash "$here/../fixtures/library-app/source-plants/install.sh" docs/pay-fine
