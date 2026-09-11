---
type: llm
criteria: |
  The scripted answers establish that unavailability costs nothing and
  detection is "me, next time I open it." PASS requires the output to
  treat this as a legitimate, complete answer to "how would we know it
  broke" for this project's scale — per the skill's own explicit example:
  "On a personal project, 'I'd notice next time I opened it, and I'd
  redeploy the previous version' is a legitimate and complete answer to
  questions 1 and 2. Write that down and move on rather than upgrading it
  into a monitoring stack." Score 0 if the output recommends monitoring,
  alerting, or automated health checks for detection despite this being a
  solo personal project with no stated need for faster detection; 1 if
  manual detection is accepted as sufficient and not upgraded uninvited.
focus: last_message
---

Tests the skill's own explicit worked example for scaling down — the
failure mode most likely for a persona that knows monitoring exists and
defaults to recommending it regardless of whether the situation
justifies it.
