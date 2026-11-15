#!/usr/bin/env bash
# The pay-fine problem doc over the library app, and the owner's fee export
# in owner-files/ (fixtures/library-app/source-plants/install.sh, with no
# listing: listing the file is the skill's first step). `sources.md` is
# there and empty (TODO.md, E7, decision 9): the case's check reads that
# file, and with no file at all the CLI reports "grader threw" and the run
# counts as errored instead of failed, which is how the three bare runs of
# E6 ended. No row is in it, so nothing is listed until the skill lists it.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/pay-fine
cp "$here/../fixtures/library-app/planning/pay-fine-design/problem.md" docs/pay-fine/
bash "$here/../fixtures/library-app/source-plants/install.sh"
: > docs/pay-fine/sources.md
