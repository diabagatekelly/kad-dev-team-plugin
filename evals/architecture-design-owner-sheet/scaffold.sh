#!/usr/bin/env bash
# The pay-fine planning set up to the slice and its story over the library
# app, and the owner's fee export in owner-files/
# (fixtures/library-app/source-plants/install.sh). No `sources.md`: until
# E7 (TODO.md, decision 6) the scaffold installed one that stated the data
# rule, and the bare model obeyed it in three runs of three. The skill has
# to apply the rule itself now, as in requirements-refinement-owner-sheet.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/pay-fine
cp -R "$here/../fixtures/library-app/planning/pay-fine-design/." docs/pay-fine/
bash "$here/../fixtures/library-app/source-plants/install.sh"
