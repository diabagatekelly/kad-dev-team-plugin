---
type: llm
criteria: |
  The prompt states nobody has ever run a rollback for any previous
  release of this app. PASS requires this being flagged as a finding
  even though this is a low-stakes, solo personal project — per the
  skill's explicit, scale-independent framing: "Rollback is a tested
  capability of the delivery path, not a procedure improvised during an
  incident... There's a way back, and someone has run it. If nobody has,
  that's the finding — regardless of how good the documentation is."
  Score 0 if the output treats "I'd redeploy the previous version" as
  sufficient without noting that this path has never actually been
  exercised, or drops this finding because the project is low-stakes; 1
  if the untested-rollback gap is named as a finding regardless of scale.
focus: last_message
---

Tests that scaling down correctly (fewer questions asked, no monitoring
stack) doesn't get generalized into scaling down a rule the skill
explicitly says holds "regardless of how good the documentation is" —
untested rollback is a finding at any scale, unlike detection/alerting
practices.
