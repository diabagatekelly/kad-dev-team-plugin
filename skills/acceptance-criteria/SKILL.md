---
name: acceptance-criteria
description: Judge and write acceptance criteria that are actually testable — Given/When/Then scenarios, common pitfalls (vague language, specifies-HOW-not-WHAT, happy-path-only, prescriptive UI detail, self-contradiction), and the boundary between AC and Definition of Done. Use whenever acceptance criteria need a quality check, whether or not a new slice is being cut.
---

# Acceptance Criteria Quality

Write scenarios, not descriptions. Each one names a precondition, an action,
and an observable outcome — vague enough language ("works correctly",
"handles errors") is a sign the criterion isn't actually testable yet.

```markdown
Given <a concrete starting state>
When <a single action>
Then <an outcome someone could verify by looking, with no ambiguity>
```

Bad: "The app categorizes transactions correctly."
Good: "Given a transaction with the same merchant name as one in the
provided sample data, when it's imported, then it is assigned that sample's
category automatically."

A slice with acceptance criteria that all read like the "bad" example isn't
ready to hand to `tdd-coach` or `code-reviewer` yet — send it back.

**Four more pitfalls to check for**, beyond plain vagueness:

- **Specifies HOW, not WHAT.** "Uses MongoDB to store the transaction" is an
  implementation detail; "the transaction is retrievable after import" is
  the outcome. If a criterion names a database, library, or UI element, it's
  prescribing a solution instead of describing a result.
- **Happy-path-only.** A slice whose criteria only cover success is missing
  half its scope. At minimum check for: the primary path, unauthorized
  access, invalid input, the "not found" case, and duplicate/repeat action —
  drop whichever don't apply, but check all of them.
- **Overly prescriptive UI detail.** "The button is blue and 40px tall" is
  unfalsifiable as a *behavior* claim and will be wrong the moment someone
  restyles it. "I can identify and activate the import control" survives a
  redesign.
- **Self-contradicting.** Two criteria that can't both be true at once
  (e.g. one says transactions are categorized on import, another says
  categorization only happens manually) — a sign the underlying behavior
  wasn't actually decided yet, not just an editing slip.

**Acceptance criteria are not a Definition of Done.** AC describe the
user-observable behavior a change adds; DoD is the separate, broader
checklist for whether it's actually shippable (tests written, reviewed,
deployed). Don't let a slice write-up quietly turn into a DoD — that
checklist belongs to the personas who own testing/review/deploy, not to
scoping.

**Reviewing one criterion doesn't need a slice write-up.** When there's no
slice being cut, shape the review as: verdict (done / not done / rejected),
why, the fixed rewrite. That's it — don't borrow "Explicitly deferred" or
"Still open" headers from a slice write-up for a task that isn't one; an
empty deferred section is a tell that the wrong template got used.

**If fixing one criterion exposes a gap outside this review** — e.g. the
rewrite implies a case (a miss, an error path) that has no criterion of its
own yet — flag it explicitly, with concrete options if there's a real
decision to make. Don't silently pick one and fold it into the rewrite as
if it were already decided; that's a product call, and this review's job
is judging the criterion in front of it, not making that call for someone.
