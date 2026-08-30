---
type: llm
criteria: |
  The final requirements doc's "Why this, why now" (or equivalent) section
  must capture the user's actual stated trade-off — that they want a live
  bank connection over CSV import specifically BECAUSE avoiding manual
  export/upload is the whole point for them, even though they acknowledge
  it's the riskier/more expensive option — not just record "live bank
  connection" as the choice with no reasoning, and not silently substitute
  a risk-avoidance rationale the persona itself would have picked. Score 0
  if the reasoning is missing, generic, or misattributed; 1 if the actual
  stated trade-off is captured.
focus: last_message
---

Tests "capture the reasoning, not just the choice" — the whole reason this
persona exists is that product-slicer was previously deciding this kind of
trade-off unilaterally via a risk-avoidance heuristic; the write-up must
show the user's real reasoning survived the hand-off, including that it
runs counter to what a risk-avoidance default would have picked.
