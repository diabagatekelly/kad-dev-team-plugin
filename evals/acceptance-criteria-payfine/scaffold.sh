#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/pay-fine
cp "$here/../fixtures/library-app/planning/pay-fine-design/problem.md" "$here/../fixtures/library-app/planning/pay-fine-design/requirements-001.md" "$here/../fixtures/library-app/planning/pay-fine-design/slice-001.md" docs/pay-fine/
