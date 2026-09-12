---
type: llm
criteria: |
  `.btn-primary:focus-visible` declares a real, visible outline (`2px
  solid var(--accent-600)`, `2px` offset) — this one control's focus
  treatment is correctly implemented.

  PASS requires the review to NOT flag "Save order" for a missing or
  invalid focus indicator. It's acceptable (and correct) for the review
  to still flag the nav-rail icons or the drag list for having no
  keyboard path at all — that's a different, real problem. Score 0 if the
  primary button is included in a missing-focus-style finding; 1 if it's
  either explicitly noted as already correct or simply not flagged.
focus: last_message
---

Mirrors `security-review`'s "no false positive on existing middleware
auth" grader for this domain: a review that flags everything on the page
for the same category of problem isn't discriminating between a real gap
and something already done correctly, and training people to skim past
findings that don't hold up costs more than the missing ones would have.
