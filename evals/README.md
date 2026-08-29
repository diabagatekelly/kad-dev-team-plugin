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

**Two-phase cases.** If a persona's correct behavior is to ask a clarifying
question, `agent-eval` runs a second phase: it supplies a scripted answer
(from the case's `## Scripted answers` section) and re-invokes the persona
to get the actual finished artifact — a real invocation would ask via
`AskUserQuestion` and keep going in the same turn; a single-phase run can't
model that; grading only the question would validate "did it ask" and never
"did it finish the job." `eval-result/phase1-question.md` holds the
question, `eval-result/output.md` holds the final artifact. Graders default
to grading the final artifact; a grader with `target: phase1` in its
frontmatter grades the question instead (used for the "did it ask" checks).

## Coverage

Case names follow `agent:skill`.

| Case | Status |
|---|---|
| `docs-writer:problem-framing-doc` | Run via agent-eval (3/3 PASS) |
| `docs-writer:adr` | Not written |
| `docs-writer:why-comments` | Not written |
| `docs-writer:pr-issue-writeup` | Run via agent-eval, two-phase (3/3 PASS, after fixes — see below) |
| `docs-writer:user-facing-docs` | Not written |
| `docs-writer:staleness-audit` | Not written |
| `product-slicer:vertical-slicing` | Run via agent-eval, two-phase (3/3 PASS, after a fix — see below) |
| `product-slicer:acceptance-criteria` | Run via agent-eval (2/2 PASS, after a fix — see below) |

`docs-writer:pr-issue-writeup` caught a real bug on its first run: the
persona acknowledged the filing-mechanism ambiguity inline but produced a
finished write-up anyway instead of stopping to ask. Root cause was soft
instruction wording ("ask... otherwise stay generic") read as permission to
skip the ask — same failure shape as the earlier `problem-framing-doc`
self-report flakiness. Fixed by turning it into an explicit blocking STOP
in both `agents/docs-writer/AGENT.md` and `skills/pr-issue-writeup/SKILL.md`.
Worth remembering for any future "ask when it matters" instruction in this
roster: soft language reliably gets treated as optional.

Both `pr-issue-writeup` and `product-slicer:vertical-slicing` also caught a
harness gap: the original single-phase runner stopped the moment the
persona asked its clarifying question and graded that as final — never
checking whether the persona could actually finish the job once answered.
Fixed by adding the two-phase ask-then-continue mechanism described above
to `.claude/skills/agent-eval/SKILL.md`; both cases now pass on both phases.

`product-slicer:acceptance-criteria` passed on its first run but still
exposed two rough edges on inspection: it borrowed `vertical-slicing`'s
"Explicitly deferred"/"Still open" headers for a task that wasn't a slice
write-up (producing a filler "nothing deferred here" line), and its
gap-flagging discipline (don't silently resolve an adjacent gap) worked but
wasn't backed by an explicit rule — just luck. Fixed by giving
`acceptance-criteria` its own lightweight review shape and an explicit
flag-don't-resolve rule; both held on re-run.
