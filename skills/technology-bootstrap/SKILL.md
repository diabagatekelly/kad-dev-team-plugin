---
name: technology-bootstrap
description: Decide the smallest set of technology choices that must exist before a slice's first failing test can be written — language, runtime, test runner, package manager and its pinning posture — and explicitly defer everything the slice doesn't force. Recommends with trade-offs and gets approval; never decides unilaterally. Use when a designed slice is about to be implemented in a repo that has no stack yet, or when a later slice forces a technology category nothing has chosen.
---

# Technology Bootstrap

## What this decides

The smallest set of technology choices that must exist before the first
failing test can be written in a repo that has none — and nothing else.
This is not a stack plan for the project. It's the answer to "what has to
be true before anyone can type `test` and watch it fail?"

Everything a slice doesn't force stays explicitly undecided, with a named
owner. That's the whole discipline here: an empty repo invites deciding the
entire stack in one sitting, and most of those decisions would be made
against a system nobody has built yet.

## The demand test

One question per candidate technology:

> **Can this slice's first failing test be written without deciding this?**

Yes → don't ask. That's the only filter.

"Is it project-specific?" is *not* a filter, and reaching for it is the
most likely way to get this wrong. A CI/CD pipeline is not project-specific
and still doesn't belong here: the slice ships without one, so asking
produces infrastructure ahead of need — the "technical plumbing" shape this
plugin's `vertical-slicing` skill already rejects at the slice level. The
same goes for a container runtime, a cloud provider, or an observability
stack.

**Almost always forced**, because no test can be written without them:

- **Language and runtime.**
- **Test runner** — including how tests are invoked.
- **Package manager**, and with it the **lockfile and pinning posture**.
  This one rides along whether or not anyone asks: the moment a dependency
  is installed there's a lockfile, and pinning is far cheaper to set now
  than to retrofit across a dependency tree later.

**Sometimes forced — decide by looking at the test, not the category:**

- **UI framework**, if the slice's actor is a person and the first test
  drives a screen.
- **HTTP framework**, if the actor is programmatic and the first test goes
  over the wire.

**Almost never forced by a first slice**, each with an owner:

| Category | Who owns it, and when |
|---|---|
| Database / persistence technology | `architecture-design`, per boundary — and only once the slice actually needs to survive a restart |
| Hosting, deployment, CI/CD | `devsecops-engineer:operational-readiness`, once there's a delivery path to review |
| Auth provider | `architecture-design` per boundary, with a `devsecops-engineer` consult — only if this slice authenticates someone |
| Secrets storage | Same — only if this slice actually handles a secret |

## Why persistence usually isn't forced

The most common mistake this skill exists to prevent: a design names a
persistence boundary, and that gets read as "we need to choose a database."

It isn't. A boundary is an interface. The first implementation behind it
can be in-memory — a map that lives as long as the process — and every test
for the slice's business behavior passes against it. The technology
question arrives later, when data has to outlive a restart, and by then
you'll know the access patterns instead of guessing them. The boundary was
what made deferring free.

Apply the same reasoning to anything else the design isolated behind an
interface. If a real in-memory implementation satisfies the slice's tests,
the technology behind that interface is not a bootstrap decision.

## On the package manager: prefer defaults over flags

The package manager is the one bootstrap choice that quietly sets a
security posture for the life of the project, so it gets a criterion of its
own beyond ergonomics and speed.

Managers within the same ecosystem differ in **whether the safe posture is
the default or an opt-in flag** — whether the lockfile carries content
hashes for transitive dependencies without being asked, and whether install
verifies them without being asked. Both end states look identical in a
review. They are not the same choice.

**Prefer the manager where the safe posture is the default.** A posture
that depends on a flag depends on everyone remembering the flag — every
contributor, every CI job, every one-off script someone writes in a hurry
two years from now. Defaults hold without anyone remembering anything.

Two limits on this:

- **It's a tiebreak, not an override.** Don't drag in a tool that doesn't
  fit the ecosystem or the team for this reason alone. When two credible
  options are otherwise close, this decides.
- **It's a choice, not an audit.** `supply-chain-review` owns the *standard*
  — what counts as pinned, and what keeps a lockfile honest — and it's worth
  consulting for that. Don't run it here: it audits an existing repository's
  posture, and at bootstrap there is no posture yet, no lockfile, and no
  build to compromise.

Record the resulting posture as a decision like any other, so the next
person can tell it was chosen rather than inherited.

## Recommend, don't decide

Technology choices belong to the user. Your job is to make each one easy to
decide well, not to make it.

For each forced category, one at a time: state what needs deciding, your
recommended choice and *why*, and the alternative(s) you considered and
rejected with concrete reasons — then stop and get approval via
`AskUserQuestion` before moving to the next one. Same loop
`architecture-design` runs, for the same reason: a choice surfaced only in
a finished document is a choice the user reviews rather than makes.

Two things to hold on to inside that loop:

- **A strong recommendation is still a question.** You will often have a
  genuinely obvious answer here — the ecosystem's default test runner is
  usually right. Recommend it confidently and still wait. Confidence
  changes the wording, not the loop.
- **Scale the recommendation to the situation.** Ask who's building and
  maintaining this if it isn't already established. A one-person project
  and a team of eight have different right answers about tooling weight,
  and recommending the team-sized answer to one person produces setup
  nobody maintains.

## Consult `devsecops-engineer` when a choice carries a runtime-safety question

Some bootstrap choices are simultaneously security choices. When you hit
one, get the answer from the persona that owns it rather than reasoning
about it yourself.

**This is an inline consult, not a spawn.** Both personas are
`background: false`. Load the relevant `SKILL.md`, ask the narrow question
it covers, record the answer in your decision, and return to this skill —
the same in-conversation adoption `orchestrator` uses. Don't hand the
design over, and don't launch anything.

When to consult:

- **Package manager and pinning posture** → `supply-chain-review`, for its
  standard only: what "pinned" actually means and what keeps a lockfile
  honest. The choice itself stays yours — see the section above.
- **A bootstrap choice that touches secrets or authentication** →
  `security-requirements`.

Don't consult reflexively. A test runner choice carries no security
question, and manufacturing one wastes the user's turn.

## Record what you rejected

Every declined option gets written down with its reason. This is not
bookkeeping — it's what stops the same choice being relitigated in three
months, and it's the same instinct the `adr` skill's "Alternatives
considered" section serves.

"YAGNI," "too heavy for a project this size," and "we already decided
against this family" are complete reasons. A rejection with no reason is
worse than no record at all, because it looks settled without being
checkable.

## Leave the rest explicitly open

Name the categories this slice didn't force as *not yet decided*, with the
owner from the table above — don't just omit them. An omitted decision is
indistinguishable from a forgotten one, which is exactly why
`vertical-slicing` writes placeholders instead of dropping criteria it
can't fill.

## When a choice is ADR-worthy

Apply the same three-part bar `adr` uses — architectural, significant,
non-obvious. A runtime choice that the whole system's hiring and library
ecosystem follows from usually clears it; a test runner usually doesn't.
Say so at the moment you present that decision, keep a running list, finish
the approval loop, then hand off to `docs-writer` inline in the same
session.

## Output format

```markdown
# Technology bootstrap: <what forced this>

## Situation
Who's building and maintaining this, and the slice whose first test is
being unblocked. Everything below is scaled to this.

## Decided
One entry per forced category: the choice, why this slice forced it, the
recommendation made, and what the user approved or changed. Note any
flagged as ADR-worthy.

## Considered and rejected
Per category, the options declined and the concrete reason.

## Deliberately not decided yet
Categories this slice did not force, and who owns each when it does.

## Consults
Any `devsecops-engineer` question asked and the answer recorded.
```

Keep it short. If the honest output is four choices and a list of things
left open, that's the correct output — a bootstrap document longer than
the design it serves is a sign the demand test wasn't applied.

## Re-entering this skill

This runs once per project and then stays additive. When a later slice
forces a category that was left open — the first slice that needs data to
survive a restart, the first one that authenticates — run it again for
*that category only* and append. Never reopen a settled choice unless the
user asks; a bootstrap decision that keeps getting revisited isn't a
bootstrap, it's an unresolved argument.
