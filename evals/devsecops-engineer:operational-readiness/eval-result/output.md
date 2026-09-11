Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/operational-readiness/SKILL.md

Answers received:
- Unavailable for an hour: "Nothing bad, I just fix it when I get to it. It's just me using it."
- Who would find out, and how: "Me, next time I open it. Nobody else uses this."

Before writing this up, one decision needs your call. The migration renaming `category` to `category_id`, and the code that only understands the new column, are set to ship together in one release. Rolling back the code alone afterward would break immediately, since the column it expects would already be gone — this specific release is one-way as currently planned, unlike every previous release, which was untested but at least in principle reversible.

**Recommendation: split it into an expand/contract sequence** — add `category_id` alongside `category` and backfill first, ship the new code once backfill is confirmed (with `category` still present, so a code-only rollback stays safe), and drop `category` in a later release once the new code has run successfully.

**Alternative considered and rejected: ship migration and code together as planned, accepting this release can't be rolled back.** Not chosen because the risk isn't about how likely a bug is — it's that there would be no tested way back at all if one shows up after data has already moved through `category_id`.

Approve splitting the release this way? — *(scripted answer: "Let's split it — I'd rather not risk being stuck if something goes wrong, even though it's low stakes.")* — approved.

```markdown
# Operational readiness: category → category_id migration and code release

## Situation
Solo developer, sole user, personal finance tracker on a single small server, redeployed manually. An hour of unavailability costs nothing, and detection is manual — the developer, next time they open the app. Both are legitimate, complete answers at this scale; nothing below upgrades them into monitoring or alerting this project doesn't need.

## How we'd know it broke
Current state: nothing beyond opening the app. That's fine for general availability at this scale. One gap found regardless of scale: if the database connection string is missing at startup, the app starts anyway and returns a 500 for every request instead of failing to start — see Findings.

## How we'd put it back
No rollback has ever been run for this app — a finding on its own, independent of this release. This specific release also couples a schema rename to code that depends on it, which would make a plain code-only rollback break immediately. Resolved above: split into expand/contract so the release stays rollback-able, approved.

## What someone needs to know
- What this depends on: the database connection string is the only required piece of configuration.
- What's genuinely irreversible: dropping the old `category` column, which happens in the final step of the expand/contract sequence, in a later release — flag that clearly in that release's own notes when it ships, not only here.
- No known recurring failure modes yet for this app beyond what's listed in Findings below.

## Findings

### Finding: Startup succeeds with missing required configuration
**Severity:** Medium
**When this bites:** The database connection string environment variable is missing, unset, or wrong after a manual redeploy — an easy mistake in an SSH-and-pull workflow.
**What's happening:** The app starts anyway and returns a 500 for every request rather than failing to start.
**Why it matters:** A "why is everything 500ing" outage takes far longer to diagnose than a startup crash that names the missing variable — even for a solo project, this turns a one-line fix into a debugging session.
**Suggested fix:** Fail fast at startup if the connection string is missing or invalid, and print what's missing.

### Finding: No rollback has ever been exercised
**Severity:** Medium
**When this bites:** The first time a release actually needs rolling back — the worst possible time to discover the path doesn't work.
**What's happening:** "Redeploy the previous image" has never actually been run.
**Why it matters:** This holds regardless of how good the plan looks on paper — a rollback nobody has run is a hypothesis, not a capability.
**Suggested fix:** Run the redeploy-previous-image path once, deliberately, outside of an incident.

### Finding: This release originally coupled a schema change to code that depends on it
**Severity:** High
**When this bites:** If the new code had any bug not immediately obvious, discovered after the migration already ran.
**What's happening:** Resolved above by splitting into expand/contract — recorded here so it appears in the findings list, not only in the narrative that led to it.
**Suggested fix:** Already decided (see Decisions).

## Decisions
**1. Split the migration and code deploy into expand/contract rather than shipping together.** Approved as recommended. Rejected: shipping together as planned and accepting the release is one-way. Not ADR-worthy on its own — a one-time sequencing choice for this release, though the same shape (add alongside, backfill, cut over, drop later) is worth reusing for any future column rename.

Nothing here recommends an on-call rotation, a post-mortem template, or monitoring — none of it is justified by a project with one user who already said an hour of downtime costs nothing.
```
</content>
