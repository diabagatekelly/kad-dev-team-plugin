#!/usr/bin/env bash
# The pay-fine UI slice, its design and the project's design system over the
# library app (as screen-design-payfine), and the owner's fee export in
# owner-files/ (fixtures/library-app/source-plants/install.sh). No
# `sources.md`: until E7 (TODO.md, decision 6) the scaffold installed one
# that stated the data rule, and the bare model obeyed it in three runs of
# three. The skill has to apply the rule itself now, as in
# requirements-refinement-owner-sheet.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
fx="$here/../fixtures/library-app"
bash "$fx/scaffold.sh"
mkdir -p docs/pay-fine
cp "$fx/planning/pay-fine-design/problem.md" "$fx/planning/pay-fine-design/requirements-001.md" "$fx/ui-plants/pay-fine/design-001.md" "$fx/ui-plants/pay-fine/slice-001.md" docs/pay-fine/
mkdir -p docs/pay-fine/visual-ux
cp -R "$fx/ui-plants/design-system/visual-ux/." docs/pay-fine/visual-ux/
bash "$fx/source-plants/install.sh"
