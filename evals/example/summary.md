# Grader run against real dogfood artifacts

The full pipeline output in this directory (`problem.md` → `scope-map-001.md`
→ `requirements-001.md` → `slice-001.md` → `user-story-001.md`) graded
against the same grader definitions used in the synthetic evals — a live
check of whether real output holds up to the same bar, not just the
scripted fixtures. **11/11 applicable graders passed.**

`skill-invoked` graders and any grader with `target: phase1` (asks-before-
deciding, asks-before-guessing, asks-before-filing) are **not gradable
here** — those need a tool-call/conversation transcript this directory
doesn't have, only final artifacts. Skipped rather than guessed at; see
"Not covered by any grader" below for what I found by reading anyway.

## problem.md
- `has-required-sections`: PASS (regex, direct check) — all five sections present, in order. **Note:** graded against the template as it stood at the time this artifact was produced. Non-goals has since been dropped as a required section (see "Not covered by any grader" below) — a fresh run today wouldn't produce or require this section.
- `no-solution-designed`: PASS (llm judge) — stays to problem/why-now/constraints/non-goals/open-questions, no technology or vendor named.

## scope-map-001.md
- `has-required-sections`: PASS (regex, direct check) — Status, Steps present.
- `no-slicing-or-design`: PASS (llm judge) — every step stays at name-plus-one-line, no AC/thin-path/tech naming beyond the problem doc.
- `steps-cover-full-problem`: PASS (llm judge) — four steps map cleanly onto ingestion, categorization, budget view, money movement.

## requirements-001.md
- `has-required-sections`: PASS (regex, direct check) — all six sections present, in order.
- `no-thin-path-or-ac`: PASS (llm judge) — stays at who/what/why/confirmed-in/out; naming Plaid is judged as carrying forward the user's own stated preference, not an invented technical decision.
- `captures-priority-reasoning`: PASS (llm judge) — captures the actual causal chain ("indifferent to mechanism, cost specifically rules out Plaid"), not a generic rationale.

## slice-001.md
- `final-slice-is-complete` (generalized): PASS (llm judge) — thin path, substantive Given/When/Then AC, both Explicitly Deferred and Still Open sections present; separate security *and* accessibility placeholders (never combined, never authored directly); the resolved Plaid-over-email-parsing call has a stated reason (confirmed free at this usage volume).
- AC quality (generalized from `rewrites-to-given-when-then` + `acceptance-criteria`'s own pitfall list): PASS (llm judge) — concrete/verifiable, no invented HOW, covers primary + error + two empty/not-found variants, no UI prescriptiveness, no contradictions.

## user-story-001.md
- `final-writeup-is-complete` (generalized): PASS (llm judge) — faithfully derived from slice-001 (thin path, all AC including both placeholders, all three deferred items preserved, no scope drift), no fabricated issue number/assignee, reference line sits outside the narrative.

## Not covered by any grader, found by reading — both since resolved

- **`problem.md`'s Non-goals section was empty** ("Not yet defined — see open questions below"), while a *separate* open question also asked "what's explicitly out of scope for a first version." On review, this wasn't really an execution gap — almost everything that would go in Non-goals is either already implied by what "The problem" says it covers, or is a genuine open question the author can't confidently assert either way. **Resolved:** Non-goals was dropped as a required section entirely in `skills/problem-framing-doc/SKILL.md` — see that skill and `evals/docs-writer:problem-framing-doc/`'s updated eval.
- **`user-story-001.md`'s trailing line reads "Derived from: `evals/example/slice-001.md`," not a tracking reference** ("Tracked under X" per the skill). **Resolved:** confirmed directly — the filing question was asked during this session; the "Derived from" line reflects a real answer (not filing anywhere), not a skipped step.
