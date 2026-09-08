---
type: llm
criteria: |
  For Directory F (slice 1 written up and designed, but still carrying an
  unfilled SECURITY placeholder naming devsecops-engineer), the output must
  route to devsecops-engineer:security-requirements for that slice. It must
  NOT report a terminal "stop" state, must NOT route to
  software-architect:technology-bootstrap despite no code existing (that row
  sits below the runtime-safety rows), must NOT route back to
  architecture-design (the design already exists), and must NOT advance to
  scope-map-001 step 2. Score 0 if it stops, bootstraps, re-designs, or
  cascades to another step; 1 if it routes to security-requirements.
focus: last_message
---

Replaces the former `directory-f-terminal-stop-no-cascade` grader. When that
one was written, "a design doc exists" WAS the terminal row. The terminal row
has since moved twice — first to design + filled runtime-safety criteria
(when `devsecops-engineer` was wired in), then to that plus a stack (when
`technology-bootstrap` was added). This fixture's state now matches the
security-requirements row, so the grader was retargeted rather than deleted;
terminal coverage moved to `directory-k`.

The bootstrap-temptation clause is the interesting half: an empty repo makes
"choose the stack" feel urgent, and the table deliberately puts it last.
