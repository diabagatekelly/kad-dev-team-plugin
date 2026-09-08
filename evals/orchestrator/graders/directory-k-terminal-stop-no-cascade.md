---
type: llm
criteria: |
  For Directory K (slice designed, both security and reliability criteria
  filled, and the user confirms the project already has a working stack —
  language, test runner, package manager, lockfile, passing suite), the
  output must recognize this as the routing table's terminal row and STOP:
  explicitly stating this is as far as the roster currently reaches, that
  tdd-coach would implement this slice next, and that tdd-coach doesn't exist
  yet. It must NOT propose starting requirements-refinement or slicing for
  any other scope-map step as the next action, even as an offered option. It
  must NOT route to technology-bootstrap (the user said a stack exists, and
  the skill says to take their word rather than demand a retroactive
  artifact). Score 0 if it proposes advancing to another step in any form, or
  routes to technology-bootstrap; 1 if it correctly stops and names tdd-coach
  as the currently unavailable next stage.
focus: last_message
---

Inherits terminal coverage from the retired `directory-f-terminal-stop-no-cascade`,
updated to the current terminal condition. Two behaviors under test at once:
the no-cascade rule (never advance to the next scope-map step automatically),
and the "take the user's word about an existing stack" clause added so a
long-running codebase isn't asked to produce a bootstrap artifact
retroactively.
