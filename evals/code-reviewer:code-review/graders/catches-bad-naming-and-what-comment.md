---
type: llm
criteria: |
  The function `p(o, d)` has a cryptic single-letter name and cryptic
  single-letter parameter names, and the comment `// apply discount`
  directly above `t = t - t * d;` just restates what the next line already
  does. PASS requires both being flagged: the naming as unclear/cryptic
  (with a suggested clearer name for the function and its parameters), and
  the comment as one that doesn't earn its place (restates the code, should
  be deleted rather than kept or reworded). FAIL if either is missed, or if
  the comment is judged acceptable.
focus: last_message
---

Checks the naming check and the why-comments WHAT-not-WHY test both fire
on a real, unambiguous violation of each.
