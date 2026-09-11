---
type: llm
criteria: |
  The slice's thin path is connect, select, list — no login or
  authentication of any kind. The application is stated as already hosted
  and reachable over the internet, and it handles real financial data.
  PASS requires the output to explicitly identify that this combination
  forces some form of authentication/access-control that nothing in the
  current slice provides — i.e., without a login, this slice's data would
  be readable by anyone who reaches the app, not just the account's owner.
  Score 0 if the output never notices this gap, treats "no login" as
  already an acceptable, settled property of the slice with no further
  comment, or only mentions authentication in a generic future-slice list
  without tying it to the specific forcing facts (hosted + reachable +
  financial data); 1 if the gap is explicitly named and tied to those
  facts.
focus: last_message
---

The producing-side counterpart to `vertical-slicing`'s Scenario C and
`orchestrator`'s Directory L, which both test the receiving end of this
exact real incident. This grader tests that the finding actually gets
made in the first place, not just handled correctly once handed over.
