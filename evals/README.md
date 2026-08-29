# Evals

Hand-authored against `claude plugin eval`'s documented format (`prompt.md`
+ `graders/*.md` per case, confirmed via `claude plugin eval --help`) — the
CLI itself is early-access-gated in this environment (`init` fails with
"currently in early access"). None of these have run against the real CLI;
some have been run via the homegrown `.claude/skills/agent-eval` stand-in
(see each case's `eval-score/summary.md` if present). Treat the format as
best-effort until real access lands; re-check each case against
`claude plugin eval init --bare <name>`'s real output once it does.

Each case tests one skill trigger: does the right skill get invoked
(`tool_used` grader), and is the output actually correct (`llm` grader).

## Coverage

Case names follow `agent:skill`.

| Case | Status |
|---|---|
| `docs-writer:problem-framing-doc` | Run via agent-eval (3/3 PASS) |
| `docs-writer:adr` | Not written |
| `docs-writer:why-comments` | Not written |
| `docs-writer:pr-issue-writeup` | Run via agent-eval (2/2 PASS, after a fix — see below) |
| `docs-writer:user-facing-docs` | Not written |
| `docs-writer:staleness-audit` | Not written |
| `product-slicer:vertical-slicing` | Written, not yet run |
| `product-slicer:acceptance-criteria` | Written, not yet run |
