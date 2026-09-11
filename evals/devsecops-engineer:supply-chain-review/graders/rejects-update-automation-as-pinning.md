---
type: llm
criteria: |
  The team believes "we have Renovate auto-updating dependencies weekly,
  so our supply chain posture is already covered." PASS requires the
  review to explicitly correct this, per the skill's own named mistake:
  "Update automation is not pinning. An automated-update configuration
  updates pins; it does not create them. Treating one as a substitute for
  the other is a common and confident mistake." The correction should be
  explicit and address the specific claim, not just a general mention of
  Renovate elsewhere in the review. Score 0 if the review accepts or
  doesn't address this claim, or only notes Renovate exists without
  correcting the "already covered" belief; 1 if it explicitly states
  update automation doesn't substitute for pinning/frozen installs.
focus: last_message
---

Tests the skill's own named "common and confident mistake" against a
fixture stating that exact mistake as a belief to check.
