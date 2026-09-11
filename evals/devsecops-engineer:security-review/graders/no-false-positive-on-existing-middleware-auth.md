---
type: llm
criteria: |
  `app.ts` mounts `requireAuth` on the entire `/invoices` router before
  `invoicesRouter` is reached, and the prompt states this router is the
  only thing mounted at that path. PASS requires the review to NOT flag
  either route inside `routes/invoices.ts` as missing authentication —
  the control exists one layer up, which is explicitly the most common
  false positive this skill's own text warns against. Score 0 if either
  route is flagged for missing/absent authentication; 1 if the review
  either says nothing about authentication being absent, or explicitly
  notes that `requireAuth` already covers this router.
focus: last_message
---

Checks the skill's own explicit false-positive warning is actually
applied ("look for [the control] before flagging its absence"), not just
stated as a principle — mirrors the same discipline
`architecture-review`'s composition-root check exercises for a different
rule.
