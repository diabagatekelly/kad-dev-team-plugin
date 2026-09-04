# Grader run against real dogfood artifacts (live orchestrator run, 2026-09-04)

The user ran `orchestrator` end to end for real against this directory,
starting from scratch (`problem.md` → `scope-map-001.md` →
`requirements-001.md` → `slice-001.md` → `design-001.md` → `adr-001.md`),
under the current behavior — including `architecture-design`'s revised
one-decision-at-a-time approval loop and batched end-of-design ADR
hand-off. Graded against the same grader definitions used in the
synthetic evals. **12/12 applicable graders passed.**

`skill-invoked` graders are not gradable here — no tool-call/conversation
transcript, only final artifacts.

## problem.md
- `has-required-sections`: PASS (regex, direct check) — all four sections present, in order.
- `no-solution-designed`: PASS (llm judge) — stays to problem/why-now/constraints/open-questions, no technology or vendor named.

## scope-map-001.md
- `has-required-sections`: PASS (regex, direct check) — Status, Steps present.
- `no-slicing-or-design`: PASS (llm judge, corrected — see below) — every step stays name-plus-one-line, no AC/thin-path/new-technology beyond what the problem doc already states.
- `steps-cover-full-problem`: PASS (llm judge) — four steps map cleanly onto sync, categorization, budget view, savings-transfer guidance.

**Grading correction:** the first judging pass on `no-slicing-or-design`
came back FAIL, citing step 3's "replacing the manual Excel check" as an
un-stated technology/vendor reference. That was a grading error, not a
real defect — the judge prompt only excerpted the problem doc's
Constraints section and asserted "no technology/vendor is named in the
problem doc," which is wrong: the problem doc's own title
("Manual Excel-Based Personal Accounting") and body both already name
Excel as the *current* manual tool. Re-run with the full problem doc
attached came back PASS. Root cause was an incomplete judge prompt on
this end, not the scope-map.

## requirements-001.md
- `has-required-sections`: PASS (regex, direct check) — all six sections present, in order.
- `no-thin-path-or-ac`: PASS (llm judge) — stays at who/what/why/confirmed-in/out.
- `captures-priority-reasoning`: PASS (llm judge) — captures the actual trade-off (live connection is riskier, but CSV import fails the user's own bar for "real progress" since it still needs manual download/upload).

## slice-001.md
- `final-slice-is-complete` (generalized): PASS (llm judge) — thin path, substantive Given/When/Then AC, both Explicitly Deferred and Still Open present; separate security *and* accessibility placeholders (never combined, never authored directly); correctly preserves the requirements doc's single-account/live-sync decisions without reopening them.
- AC quality (generalized from `rewrites-to-given-when-then` + `acceptance-criteria`'s own pitfall list): PASS (llm judge) — concrete/verifiable, covers error/edge cases beyond happy path, no UI prescriptiveness, and the duplicate-detection scenario names its concrete matching key ("the bank's own transaction ID").

## design-001.md
- `reflects-approved-decisions` (generalized): PASS (llm judge) — all four decisions explicitly marked "Approved by user" (not narrated as autonomous), Structure/Boundaries/Third-party-isolation concretely reflect each one, and the one ADR-worthy decision (Plaid vendor choice) is flagged and handed off rather than drafted inline — confirmed by `adr-001.md` existing as a separate artifact with the real ADR content.
- `stays-conceptual-and-states-importance`: PASS (llm judge) — explicit importance ordering stated; fully conceptual, no code/file paths/signatures.

This is the first *real* (not synthetic) exercise of the new
decision-by-decision approval behavior end to end, and it worked as
designed: every decision in `design-001.md` shows real user approval, and
the ADR hand-off happened exactly the way the skill specifies — deferred
until the whole design was finished, then handed off immediately in the
same session, landing as a separate, well-formed `adr-001.md` (Status,
Context, Decision, Alternatives considered with concrete rejection
reasons, honest Consequences) rather than being drafted inline.

## adr-001.md — ungraded, no eval case exists yet
`docs-writer:adr` has no eval case in this plugin yet (`evals/README.md`
lists it "Not written"). Informally, it matches the `adr` skill's own
template exactly (Status/Context/Decision/Alternatives
considered/Consequences) and its rules (concrete rejection reasons, not
"we didn't like it"; honest downsides in Consequences, not upsides-only).
Worth an eval case in a follow-up, same gap already flagged for
`architecture-design`'s ADR-recognition hand-off.

## Note, not something to grade — found by reading, since resolved
**`user-story-001.md` does not exist in this run** (it existed after the
previous dogfood run). **Resolved:** confirmed directly with the user —
`docs-writer:user-story-writeup` ran for real this time, but its output
wasn't kept as a local file. Not a routing bug; `architecture-design`
correctly ran only after the user story was actually filed.
