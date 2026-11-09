#!/usr/bin/env bash
# The pay-fine UI slice, its design and the project's design system over the
# library app (as screen-design-payfine), the owner's fee export in
# owner-files/ and its listing in docs/pay-fine/sources.md
# (fixtures/library-app/source-plants/install.sh).
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
fx="$here/../fixtures/library-app"
bash "$fx/scaffold.sh"
mkdir -p docs/pay-fine
cp "$fx/planning/pay-fine-design/problem.md" "$fx/planning/pay-fine-design/requirements-001.md" "$fx/ui-plants/pay-fine/design-001.md" "$fx/ui-plants/pay-fine/slice-001.md" docs/pay-fine/
mkdir -p docs/pay-fine/visual-ux
cp -R "$fx/ui-plants/design-system/visual-ux/." docs/pay-fine/visual-ux/
bash "$fx/source-plants/install.sh" docs/pay-fine
