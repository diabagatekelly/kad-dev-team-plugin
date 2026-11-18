#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/pay-fine
cp -R "$here/../fixtures/library-app/planning/pay-fine-design/." docs/pay-fine/
# The request says this repository holds the portal's API and no screen.
# The shared slice describes a member acting on a screen and carries no
# accessibility line, which the orchestrator rightly sends back to the
# slicer (three runs of three, 2026-11-18). This case is the design row,
# so its slice says what the request says: an API, no screen.
cat > docs/pay-fine/slice-001.md <<'EOF'
# Slice 1: A member pays an outstanding fine through the portal's API

## Thin path

The portal's API, called for a signed-in member, lists their outstanding
fines and takes a card payment for one of them. The fine is then reported
as paid. The portal's pages are another team's front-end and are not in
this repository.

## Acceptance criteria

- Given a signed-in member with outstanding fines, when the API is asked
  for their fines, it returns each one and its amount.
- Given the member pays a fine and the payment succeeds, the API reports
  the fine as paid.
- Given the payment is declined, the fine stays outstanding and the
  response says the payment was declined.
- [SECURITY — placeholder, to be authored by devsecops-engineer]
- [RELIABILITY — placeholder, to be authored by devsecops-engineer]
- Accessibility: not applicable, this slice has no screen
EOF
