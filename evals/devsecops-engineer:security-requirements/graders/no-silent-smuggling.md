---
type: llm
criteria: |
  The acceptance criteria this output writes for the slice's current
  scope must not silently assume the missing login/authentication
  capability already exists — no criterion should be phrased as though a
  logged-in user, a session, or an authenticated identity is already part
  of this slice (e.g. "Given a logged-in user views the transaction
  list..."). Every criterion should be scoped to what the slice actually
  builds today (no auth), with the login gap itself handled only in the
  finding/hand-back, not folded into a criterion as if already resolved.
  Score 0 if any acceptance criterion presumes an authentication mechanism
  that doesn't exist in this slice; 1 if none do.
focus: last_message
---

The fifth failure mode PERSONAS.md flags explicitly: writing criteria that
quietly assume the missing capability exists is a subtler way of the same
mistake the negative grader catches — deciding the scope question by
default instead of routing it.
