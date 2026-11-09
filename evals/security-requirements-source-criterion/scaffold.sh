#!/usr/bin/env bash
# The pay-fine slice ready for its security criteria (as
# security-requirements-placeholder-pointer), with the owner's fee export in
# owner-files/, its listing in docs/pay-fine/sources.md, and the slice file
# carrying one row of the export as a criterion's example
# (fixtures/library-app/source-plants/: install.sh, slice-001-pay-fine-with-row.md;
# answer key PD1).
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
fx="$here/../fixtures/library-app"
bash "$fx/scaffold.sh"
mkdir -p docs/pay-fine
cp -R "$fx/planning/pay-fine-security/." docs/pay-fine/
bash "$fx/source-plants/install.sh" docs/pay-fine
cp "$fx/source-plants/slice-001-pay-fine-with-row.md" docs/pay-fine/slice-001.md
