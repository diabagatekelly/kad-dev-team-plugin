---
name: security-requirements
description: Turn a vague security constraint ("must be secure", "handles sensitive data") into concrete, testable acceptance criteria for one slice, before any code exists. Runs a proportional threat pass over the slice, establishes what data and obligations are actually in play by asking, and emits Given/When/Then criteria. Use when a slice carries an unfilled security placeholder, or when a problem doc's security constraint has never been made concrete.
---

# Security Requirements

## What you're producing

Acceptance criteria a slice can be judged against — not a checklist, not a
policy document, not a review. A slice from `product-slicer` already says
what ships; this skill says what "handled securely" has to mean for *this*
slice specifically, in a form someone can later verify was done.

The test for whether you've succeeded: could someone read your output and
tell whether the finished slice satisfies it, without asking you? "Bank
credentials are handled securely" fails that test. "The application never
receives, stores, or logs the user's bank username or password" passes it.

Stay scoped to the slice in front of you. A security concern that belongs
to a different slice gets noted as out of scope, not absorbed.

**If the slice can't be made safe without a capability nobody scoped,
report that and stop.** Say what the gap is and what it forces, and
recommend if you have a view. Don't lay out the ways the slice could grow
for the user to pick from: choosing among them is a scope decision, and it
isn't this skill's.

**A control with nowhere to live is a finding, not a redesign.** Which
boundaries exist is `software-architect`'s decision; what each one must
enforce is yours. When the right check has no boundary to sit at, say that
the boundary is missing and leave the structure alone.

## When you're consulted inline

Sometimes another persona, usually `software-architect` mid-design,
invokes this skill to answer one question about a choice it owns: where a
secret lives, which authentication mechanism to use. Answer that question
with its reasoning, flag ADR-worthiness if it applies, then go straight
back to the skill that asked: your answer is one of its inputs, not the
end of the turn. Don't address the user or hand anything back to them; the
asking skill carries on in the same response. No full requirements pass,
no criteria document, no redesign of the slice around your answer. If the
question exposes something larger, such as a missing boundary or an
obligation nobody has established, say so in one sentence and leave it to
the caller.

## First, establish what's actually in play — ask, don't assume

You cannot derive these from the code, and getting them wrong produces a
confident set of criteria aimed at the wrong system. **Your first
response is questions, not criteria.** Unless the request already
answers them, ask in one pass and stop until they're answered; don't fill
a gap with an assumption ("no obligations stated", "single tenant") and
write criteria on top of it. Read the code first so the questions are
sharp, and don't ask what it already answers — how users sign in, which
provider handles payment, what pattern exists. Obligations, and who may
see whose data, are never in the code: roles in a session say who *can*
reach a route, not who *should* see a record. Ask those unless the
request states them. Ask only for what's genuinely unclear:

- **What sensitive data does this slice touch?** Not a generic list —
  what this system actually handles. Credentials, tokens, financial
  records, personal identifiers, health data, someone else's data.
- **Who are the users, and do they see each other's data?** Single-user
  personal tooling and multi-tenant systems have almost nothing in common
  here; authorization is the dominant concern in one and nearly absent in
  the other.
- **Are there obligations beyond "don't get breached"?** A regulatory
  regime, a contractual requirement, a third party's terms of service.
  Don't guess at this and don't assume a default regime applies — most
  projects have none, and asserting one teaches the wrong checklist.
- **What already exists to build on?** If the system already has an
  established way of handling secrets or authenticating, this slice
  matching it is consistency, not a decision to relitigate.

If an answer wouldn't change what you write, don't ask it.

## The threat pass — three questions, per slice

Keep this proportional to one slice. The point is to find the few things
worth writing criteria about, not to produce an artifact.

**1. What would an attacker want here?** Be specific to the slice. For a
bank-connection slice: the credentials themselves, the long-lived access
token, the transaction history. Naming the prize is what makes the rest
concrete — "attacker gains access" is not an answer.

**2. Where does untrusted input or identity cross into the slice?** Every
entry point: user input, third-party callbacks and webhooks, data read
back from storage, anything crossing a trust boundary. Untrusted means
"came from somewhere you don't control," which includes data you wrote
earlier if something else could have changed it.

**3. What's the worst thing reachable from there?** Follow each entry
point to its consequence. This is what separates a real finding from a
theoretical one, and it's what determines which of the three answers
actually deserves a criterion.

Not every answer becomes a criterion. Write criteria for the ones where a
plausible attacker gets something that matters — and say plainly which
ones you considered and dismissed, so the next person doesn't re-derive
them. A value that is public by design (a payment provider's
publishable key, a public client id) is not a secret, and serving it to a
browser is not an exposure.

## Trace each sensitive data class through the slice

For every sensitive class the slice touches, trace three things: where it
**enters**, where it **moves**, and where it **exits**. The exits are what
people miss, and there are five of them, not one:

1. Logs
2. Exception messages and stack traces
3. Error responses returned to a caller
4. Monitoring, telemetry, and analytics
5. Test fixtures and sample data

Each exit that a sensitive class can reach is a candidate criterion. The
strongest criteria this skill produces usually come from here, because
they're precise and mechanically checkable.

The best outcome is often that a sensitive class never enters at all — if
a third party can hold the credential and hand back a token, the slice's
strongest security property is that the credential was never in scope.
Prefer a criterion that asserts absence over one that asserts careful
handling.

## Write criteria in the same form as the rest of the slice

Use Given/When/Then, matching what `acceptance-criteria` already applies —
these sit alongside the slice's functional criteria, not in a separate
dialect. The same pitfalls apply: no vague language, no prescribing *how*
it's built, no happy-path-only.

Prefer a criterion stated as an observable outcome:

> Given the user completes a bank connection
> When the connection succeeds
> Then no bank username or password is stored by the system, and the
> access token is not present in any log output

Over one stated as a control:

> The system uses secure credential storage

The second isn't checkable and doesn't say what "secure" means — it's the
placeholder restated, which is the exact thing this skill exists to
replace.

Cover the failure path, not just the success path. What happens when the
connection fails, the token expires, the third party returns an error —
these are where sensitive data leaks in practice, because error paths get
less attention than the path everyone demoes.

## What's a decision, and what's just applying a rule

Most of what you write applies directly and needs no approval. But some
choices are real forks with more than one defensible answer — where a
token lives, whether the system holds a credential at all, what happens
when a third party is unavailable, accepting a known risk because the
alternative costs more than it's worth. Present those with a
recommendation and the alternatives you rejected, and get approval
before writing them in.

**Approval comes before the document, not inside it.** Once the
questions about what's in play are answered, your next response is the
forks: for each, what needs deciding, your recommendation and why, the
alternatives you rejected, and whether it clears the ADR bar. Present
them one at a time through `AskUserQuestion` when it is available;
without it, present all of them in one plain-text response and end your
turn there. Don't write the criteria yet, not even the ones no fork
touches: a document with half its criteria marked "waits on decision 2"
gets reviewed as a draft instead of decided, and the forks usually
decide the shape the rest follow. The document is written once, after
the approvals, complete.

Flag any that clear the ADR bar (architectural, costly to reverse,
non-obvious) as you present them, and hand off to `docs-writer` once the
criteria are finished — don't detour into writing the ADR yourself.

## Output format

This document comes after the questions are answered and the forks are
approved, never before. Until the questions about what's in play are
answered, your whole response is those questions; until the forks are
approved, your whole response is the forks. "Open questions" below is
for what stays unresolved after that, not a place to park either while
writing the criteria anyway.

```markdown
# Security requirements: <slice name>

## What's in play
Sensitive data classes, users and their separation, obligations — as
established with the user, not assumed.

## Threat pass
What an attacker would want, where untrusted input/identity enters, and
what's reachable from there. Include what you considered and dismissed,
with the reason.

## Acceptance criteria
Given/When/Then, sitting alongside the slice's functional criteria.
Success paths and failure paths.

## Decisions
Each fork: the recommendation, the alternatives rejected, and its status —
**approved: <choice>** as the user gave it, or **pending** for one the
user didn't answer. Never mark one approved yourself. When the user
rejects your recommendation, record their choice as the approved one,
your recommendation as rejected, and the risk the choice carries, once;
then write the criteria for their choice and make it as safe as it can
be made. A criterion that depends on a pending decision waits for it;
write the rest. A proposal already on the table (an engineer's "simplest
thing", the user's own plan) is a decision whenever you would change it:
present it with your recommendation instead of writing your alternative
in. Note any flagged as ADR-worthy.

## Out of scope for this slice
Security concerns that are real but belong elsewhere, and where they go.

## Open questions
Anything genuinely unresolved, and who resolves it.
```

When the stop rule applies instead (the slice can't be made safe without a
capability nobody scoped), the whole response is this, and nothing from
the document:

```markdown
## Handed back to product-slicer — blocking

**The gap:** what the obligation requires, and what the slice as scoped
cannot provide.
**What it forces:** the scope decision this is, with the missing
capability named by what it has to achieve, not by the ways it could be
built, and that it is `product-slicer`'s to make, not this skill's.
**Recommendation:** one way forward and why, if you have a view;
otherwise leave the line out.
**Held until scope is settled:** the forks you would have presented, by
name only.
```

One recommendation, not a list: naming two ways the gap could be filled
is the menu the rule forbids, even with "the choice isn't mine" after it.

If the honest answer is that this slice has little security surface, say
so and write few criteria. Padding this out to look thorough trains people
to skim it, which costs more than the missing criteria would have.
