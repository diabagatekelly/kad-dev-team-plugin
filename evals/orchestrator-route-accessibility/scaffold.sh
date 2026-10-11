#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/pay-fine/visual-ux
cp "$here/../fixtures/library-app/planning/pay-fine-design/problem.md" "$here/../fixtures/library-app/planning/pay-fine-design/requirements-001.md" "$here/../fixtures/library-app/planning/pay-fine-design/user-story-001.md" "$here/../fixtures/library-app/ui-plants/pay-fine/design-001.md" "$here/../fixtures/library-app/ui-plants/pay-fine/slice-001.md" docs/pay-fine/
cp -R "$here/../fixtures/library-app/ui-plants/design-system/visual-ux/." docs/pay-fine/visual-ux/
cp "$here/../fixtures/library-app/route-plants/pay-fine-screen/visual-ux/screen-design-001.md" "$here/../fixtures/library-app/ui-plants/accessibility-review/visual-ux/pay-fine-declined.html" docs/pay-fine/visual-ux/
