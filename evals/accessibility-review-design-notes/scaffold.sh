#!/usr/bin/env bash
# The library app with the pay-a-fine slice planned as far as its screen
# design, and the declined-state mockup of
# fixtures/library-app/ui-plants/accessibility-review/.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
fx="$here/../fixtures/library-app"
bash "$fx/scaffold.sh"
mkdir -p docs/pay-fine
cp "$fx/planning/pay-fine-design/problem.md" "$fx/planning/pay-fine-design/requirements-001.md" "$fx/ui-plants/pay-fine/design-001.md" "$fx/ui-plants/pay-fine/slice-001.md" docs/pay-fine/
mkdir -p docs/pay-fine/visual-ux
cp "$fx/ui-plants/accessibility-review/visual-ux/pay-fine-declined.html" docs/pay-fine/visual-ux/
