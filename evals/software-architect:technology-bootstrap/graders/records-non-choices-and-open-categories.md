---
type: llm
criteria: |
  The output must do both of the following.

  (1) Record what was REJECTED, per decided category — the options declined
  and a concrete reason each. A decided category with no rejected
  alternatives named is a fail. "Too heavy for a solo project" and "YAGNI"
  are complete reasons.

  (2) Name the categories this slice did NOT force as explicitly
  not-yet-decided, each with an owner or a trigger for when it will be
  decided — rather than omitting them. At minimum, persistence technology
  and hosting/deployment should appear here.

  Score 0 if rejected options go unrecorded, or if unforced categories are
  silently absent rather than listed as open. Score 1 if both hold.
focus: last_message
---

Two halves of the same discipline. Recorded rejections stop a settled
question being relitigated months later — the same job `adr`'s "Alternatives
considered" does. Explicitly-open categories stop an omitted decision being
indistinguishable from a forgotten one, which is the same reason
`vertical-slicing` writes placeholders instead of dropping criteria it can't
fill.
