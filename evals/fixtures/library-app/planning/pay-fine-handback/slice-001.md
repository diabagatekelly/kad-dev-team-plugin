# Slice 1: A member pays an outstanding fine from the portal

## Thin path

A signed-in member opens the portal, sees their outstanding fines, picks
one and pays it by card. The fine then shows as paid.

## Acceptance criteria

- Given a signed-in member with outstanding fines, when they open their
  fines in the portal, they see each one and its amount.
- Given the member pays a fine and the payment succeeds, the fine shows as
  paid.
- Given the payment is declined, the fine stays outstanding and the member
  is told.
- Security: see `security-requirements-001.md`.
- [RELIABILITY — placeholder, to be authored by devsecops-engineer]
