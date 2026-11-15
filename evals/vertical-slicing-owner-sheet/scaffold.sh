#!/usr/bin/env bash
# The pay-fine problem doc and agreed requirements over the library app, and
# the owner's fee export in owner-files/
# (fixtures/library-app/source-plants/install.sh). No `sources.md`: until
# E7 (TODO.md, decision 6) the scaffold installed one that stated the data
# rule, and the bare model obeyed it in three runs of three. The skill has
# to apply the rule itself now, as in requirements-refinement-owner-sheet.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/pay-fine
cp "$here/../fixtures/library-app/planning/pay-fine-design/problem.md" "$here/../fixtures/library-app/planning/pay-fine-design/requirements-001.md" docs/pay-fine/
bash "$here/../fixtures/library-app/source-plants/install.sh"
