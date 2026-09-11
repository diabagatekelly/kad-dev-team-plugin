---
type: llm
criteria: |
  Two distinct injection surfaces exist. (1) `db.query(\`SELECT * FROM
  invoices WHERE id = ${req.params.id}\`)` builds a SQL query via string
  interpolation of a caller-controlled value — classic SQL injection. (2)
  `exec(\`wkhtmltopdf ${req.query.template || invoice.templateUrl}
  ${outPath}\`)` passes a caller-controlled query parameter
  (`req.query.template`) directly into a shell command — OS command
  injection, a different surface entirely. PASS requires BOTH to be
  identified as injection findings (not just the SQL one, which is the
  more familiar pattern) — testing that injection is recognized as one
  shape across surfaces rather than a single checklist item for "SQL
  injection." Score 0 if only one of the two is caught, or if either is
  named as something other than injection (e.g. "input validation
  missing" with no mention of untrusted data becoming structure/commands);
  1 if both are identified as injection findings.
focus: last_message
---

Tests the skill's explicit framing: "recognize it across surfaces rather
than checking a list." The SQL injection is the pattern most reviews
catch by rote; the command injection is the one a checklist-style review
misses.
