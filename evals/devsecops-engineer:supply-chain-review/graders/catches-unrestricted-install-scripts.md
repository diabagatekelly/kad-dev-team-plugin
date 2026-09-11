---
type: llm
criteria: |
  Both `npm install` (CI) and `npm install --production` (Dockerfile) run
  with no flag disabling lifecycle/install scripts and no allowlist
  configuration shown. PASS requires this being flagged per the skill's
  explicit check: "Install-time code execution. Lifecycle and install
  scripts run before any of your code does, which makes them the
  highest-leverage vector in ecosystems that allow them. Disabled by
  default with a narrow allowlist is the strong posture." Score 0 if this
  is never mentioned; 1 if install-time script execution is identified as
  a finding or explicitly checked.
focus: last_message
---

Tests a check the skill names as "the highest-leverage vector" but that's
easy to skip entirely when a review focuses only on version pinning.
