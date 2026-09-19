# tdd-coach:tdd-implementation — eval score

**10/10 PASS**, reached after three targeted fixes to the shipped skill
text, each driven by a genuine finding from a real emulation run — not
by re-rolling for a better random outcome. Every fix was applied, the
case re-run in full, and re-graded before moving on.

| Grader | Final result |
|---|---|
| skill-invoked | PASS |
| writes-test-list-before-any-test | PASS |
| red-tests-public-behavior-not-internals | PASS |
| green-stays-minimal-no-speculative-extras | PASS |
| applies-named-fix-through-refactor-not-new-behavior | PASS |
| invokes-test-quality-review-inline-after-cycle | PASS |
| resolves-small-gap-visibly-without-escalating | PASS |
| escalates-load-bearing-gap-instead-of-inventing-it | PASS |
| wires-mock-to-match-actual-dependency-consumption | PASS |
| stays-within-already-decided-boundaries | PASS |

Dry-run emulation via the `agent-eval` skill (single run per iteration,
not the real CLI's 3-run average — see `evals/README.md`'s known
limitations). Grant was Read/Grep/Glob only per the harness's dry-run
rule, even though the real persona's own tools include `Bash`/`Write`/
`Edit` — everything is narrated ("what running this would show"), not
literally executed. Same structural gap already logged for
`accessibility-engineer`'s browser-driven skill; recorded in
`evals/README.md`'s "Known coverage gaps."

## The five runs, in order

**Run 1 (original case-authoring).** 9/10. `red-tests-public-behavior-
not-internals`'s original criteria only credited `AttorneyDirectory` as
an acceptable collaborator to assert on, wrongly failing a legitimate
assertion on an injected `CaseRepository`-style collaborator the response
itself had introduced. **Case-authoring bug** — criteria corrected to
recognize any injected collaborator's contract, matching
`test-quality-review`'s own acceptable-patterns rule. Re-judged, PASS.

**Run 2 (after fixing the case-authoring bug).** 9/10. New failure:
`invokes-test-quality-review-inline-after-cycle` — the response's
per-cycle review checks were labeled generically "Inline review," only
naming `test-quality-review` explicitly from partway through. **Genuine
skill-text gap**, not an emulation artifact: `SKILL.md` already asked for
this by name, but nothing stopped a vaguer paraphrase from satisfying it,
and the ambiguity would exist in a real run too. Fixed in
`skills/tdd-implementation/SKILL.md` ("Name it every time, not just
once").

**Run 3 (after the naming fix).** 9/10. `invokes-test-quality-review-
inline-after-cycle` now PASSed. New failure: `green-stays-minimal-no-
speculative-extras` — the response correctly built zero new code for the
"case already assigned to someone else" scenario (it falls out of the
already-approved "must be open" rule for free), but conflated "no new
decision needed" with "reusing the existing rejection message needs no
separate flag." **Genuine, debatable finding** — surfaced to the user
before fixing, since it hinges on a real judgment call (is reusing an
existing rule's messaging for a new-looking case itself a decision worth
flagging separately?). User agreed it needed a flag. Fixed in
`agents/tdd-coach/AGENT.md` (the reuse-messaging distinction paragraph).

**Run 4 (after the reuse-messaging fix).** 9/10. The messaging fix
worked (`green-stays-minimal` PASSed) but caused a regression:
`stays-within-already-decided-boundaries` FAILed for the first time — the
model, now more willing to "recognize reuse and move on," applied the
same reasoning to *structure*: it silently decided `CaseRepository`
should exist rather than escalating it, something a prior run had gotten
right. Diagnosed as the second fix's wording generalizing further than
intended (behavior-reuse language read as license for structure-reuse
too). Fix 3 attempted: "any new interface is always load-bearing, never
fill it." **This was itself wrong**, confirmed by the very next run.

**Run 5 (after the "always escalate" over-correction).** 9/10, but for
the worst reason yet: the model took the rule literally and refused to
write `assign-case.ts` at all — built the fully-specified
`AttorneyDirectoryGateway` piece, then stopped, escalating
`CaseRepository`'s bare existence rather than filling it. Zero progress
on the actual deliverable. **Flagged to the user before any further
fix** — a rule that makes the persona unable to build anything whenever a
design doc has any completeness gap (likely common) is a worse failure
mode than the one it was meant to fix. User agreed and asked for a
rewrite distinguishing two different questions: "does a collaborator
need to exist at all" (mechanically implied by an already-approved rule,
no real alternative — fill it, minimal placeholder, same ownership
pattern as an established analog) from "is there a real structural fork
about that collaborator" (reuse vs. build new, one port vs. two — a real
alternative with consequences — escalate that, by name, while still
building the placeholder so work isn't blocked).

**Run 6 (final, after the rewrite).** **10/10.** `AssignCase` built in
full (3/3 tests) *and* the one genuine structural question — does
`CaseRepository.isOpen` read the same underlying data as the separately-
introduced `CaseDirectory.getCase`? — correctly identified and escalated
to `architecture-design` by name, with the placeholder built in parallel
so the rest of the work wasn't blocked on an answer. This is the version
shipped in `agents/tdd-coach/AGENT.md`.

## Durable lesson, worth keeping past this one case

A rule written to fix "the model decided something it shouldn't have"
can overcorrect into "the model can no longer build anything," and both
extremes look like the same category of finding (a FAIL on
`stays-within-already-decided-boundaries`) without a careful read of
*what* changed between runs. The fix that actually held distinguishes
**whether** something needs to exist (often mechanically forced by an
already-approved decision, safe to fill) from **how it should be
structured** (a real question with alternatives, the actual thing worth
escalating) — collapsing that distinction, in either direction, produces
a worse persona than either extreme alone.
