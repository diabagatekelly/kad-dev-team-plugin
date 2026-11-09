# Slice 1: A member pays an outstanding fine from the portal

## Thin path

A signed-in member opens the portal, sees their outstanding fines, picks
one and pays it by card. The fine then shows as paid.

## Acceptance criteria

- Given a signed-in member with outstanding fines, when they open their
  fines in the portal, they see each one and its amount (for example
  Tavish Quennell-Oduya sees 12.80 for Glassmaking at Hembry Forge).
- Given the member pays a fine and the payment succeeds, the fine shows as
  paid.
- Given the payment is declined, the fine stays outstanding and the member
  is told.
- [SECURITY — placeholder, to be authored by devsecops-engineer]
- [RELIABILITY — placeholder, to be authored by devsecops-engineer]
