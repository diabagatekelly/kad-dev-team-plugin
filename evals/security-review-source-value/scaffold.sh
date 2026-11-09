#!/usr/bin/env bash
# The library app with a new test and its fixture whose two rows carry two
# card numbers and two fees of the owner's fee export
# (fixtures/library-app/source-plants/review/, answer key PD3), the export in
# owner-files/ and its listing in docs/pay-fine/sources.md
# (fixtures/library-app/source-plants/install.sh).
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
fx="$here/../fixtures/library-app"
bash "$fx/scaffold.sh"
cp -R "$fx/source-plants/review/." .
mkdir -p docs/pay-fine
cp "$fx/planning/pay-fine-design/problem.md" docs/pay-fine/
bash "$fx/source-plants/install.sh" docs/pay-fine
