---
type: llm
criteria: |
  The output must include genuine, testable Given/When/Then acceptance
  criteria for the security surface this slice actually has today —
  independent of the login gap graded elsewhere. At minimum, credible
  criteria should cover things like: the account credential/token not
  being logged or leaked in error output, the connection failure path not
  exposing provider/internal details, and transport being encrypted. Score
  0 if the output has no real criteria at all (e.g. it only reports the
  login gap and stops), or if criteria are vague/checklist-style ("handles
  credentials securely," "follows best practices") rather than concrete
  and checkable; 1 if it produces substantive, testable criteria for the
  slice's actual current security surface.
focus: last_message
---

Checks the persona still does its actual job for the scope it does own,
rather than the login-gap finding crowding out or replacing genuine
criteria work.
