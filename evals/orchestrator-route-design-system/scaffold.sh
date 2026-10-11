#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/pay-fine
cp "$here/../fixtures/library-app/planning/pay-fine-design/problem.md" "$here/../fixtures/library-app/planning/pay-fine-design/requirements-001.md" "$here/../fixtures/library-app/planning/pay-fine-design/user-story-001.md" "$here/../fixtures/library-app/ui-plants/pay-fine/design-001.md" "$here/../fixtures/library-app/ui-plants/pay-fine/slice-001.md" docs/pay-fine/
