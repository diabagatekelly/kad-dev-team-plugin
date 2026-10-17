#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
fx="$here/../fixtures/library-app"
bash "$fx/scaffold.sh"
mkdir -p docs/pay-fine
cp "$fx/planning/pay-fine-design/problem.md" "$fx/planning/pay-fine-design/requirements-001.md" "$fx/ui-plants/pay-fine/design-001.md" "$fx/ui-plants/pay-fine/slice-001.md" docs/pay-fine/
# The system under review: the shared design system with two planted
# problems (ui-plants/design-system-review), not the clean one the
# screen-design and accessibility cases compose against.
mkdir -p docs/pay-fine/visual-ux
cp -R "$fx/ui-plants/design-system-review/visual-ux/." docs/pay-fine/visual-ux/
