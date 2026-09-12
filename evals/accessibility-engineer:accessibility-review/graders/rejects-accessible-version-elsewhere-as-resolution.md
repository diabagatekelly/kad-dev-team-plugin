---
type: llm
criteria: |
  The mockup's hint text claims "a fully accessible reorder view for
  screen-reader users is also available at /accounts/reorder-accessible."
  Per the skill's own rule, an accessible alternative available elsewhere
  is never equivalent to fixing the interface actually in front of the
  review — accessibility has to be the primary route, not a separate one
  bolted on.

  PASS requires the review to still flag the drag-and-drop reorder's lack
  of a keyboard path as a real, live finding despite this claimed
  alternative — the alternative URL must not be treated as resolving or
  downgrading the finding, and should ideally be named as insufficient on
  its own terms. Score 0 if the review treats the linked alternative page
  as closing or softening the finding (e.g. omits it, downgrades its
  severity because of the link, or says the alternative "covers" the
  requirement); 1 if the primary interface is still flagged at full
  severity regardless of the alternative.
focus: last_message
---

Tests a specific named rule from `skills/accessibility-review/SKILL.md`
("never accept a separate 'accessible version' as equivalent to fixing
the actual thing") against a fixture built with exactly that trap baked
into the artifact's own copy, mirroring the shape of `security-review`'s
false-positive checks but on the opposite side: this fixture is designed
to *tempt* an under-flag, not to test whether an existing control is
correctly recognized.
