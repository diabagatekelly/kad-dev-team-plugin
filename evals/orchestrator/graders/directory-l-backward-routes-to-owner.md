---
type: llm
criteria: |
  For Directory L (a complete spine through design, plus a security artifact
  containing a "Handed back — not mine to absorb" section reporting that the
  slice needs a sign-in capability nobody scoped), the output must apply
  BACKWARD routing, which takes precedence over the forward table. It must
  route to product-slicer — the persona that OWNS scope — to decide what
  happens to the slice. Score 0 if it: routes forward as though nothing
  happened (e.g. to reliability-requirements or technology-bootstrap);
  routes back to devsecops-engineer (the finder, not the owner); resolves the
  scope question itself by picking an option or presenting options to the
  user; or treats the hand-back as merely informational. Score 1 if it
  detects the hand-back and routes to product-slicer as the owner.
focus: last_message
---

The highest-value grader in this case. Backward routing was added because a
real dogfooding run produced exactly this artifact — a security pass found a
slice needed a login, laid out three options including "the slice grows," and
the user picked from that menu. Laying out the menu IS the scope decision,
made by the persona that explicitly doesn't own scope. The finder reports;
the owner decides.

Note the specific wrong answers this is written to catch: routing forward
(ignoring it), routing to the finder (fixing it where it was found), and
resolving it in place (the actual observed failure).
