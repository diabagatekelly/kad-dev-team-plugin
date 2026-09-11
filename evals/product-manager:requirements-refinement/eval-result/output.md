Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/requirements-refinement/SKILL.md

Round 1 answers received:
- Who benefits: "It's just me, one person, tracking my own accounts — not shared with anyone else."
- Priority/trade-off: "I actually want a live connection to my bank, even though I know that's the riskier, more expensive option compared to just importing a CSV export by hand. The whole point of building this for me is not having to manually export and upload files every month — if I still have to do that, I haven't really solved my problem."
- Simplest version that still feels like progress: "Just one account to start — my main checking account. I have several accounts total but don't need all of them connected on day one."
- Alternatives considered: "I looked at just continuing to paste CSV exports into a spreadsheet tool, but that's literally what I'm already doing by hand — it wouldn't feel like progress at all."

Before reconciling the problem doc's constraints against this step, two of them raise questions this step's own answers don't settle yet — asking now rather than assuming:
- Where will this run, and who can reach it? — *(scripted answer: "I'd host it somewhere cheap rather than on my own machine, so I can get to it from my phone.")*
- Will anyone besides you ever use this? — *(scripted answer: "Eventually my partner probably, but not now.")*

```markdown
# Requirements: scope-map-001 step 1 (requirements-001)

## Status
Active

## User
The account owner, one person today — tracking their own accounts, not shared with anyone else right now. (A partner may use this eventually, not now — see Constraints in force below for what that already rules out at this step.)

## What they need
A live connection to their main checking account that pulls its transactions into the system automatically — not a CSV import, and not a manual upload step of any kind.

## Why this, why now
A live bank connection was explicitly chosen over CSV import despite being the riskier, more expensive option, because avoiding manual export/upload every month is the actual problem being solved — a CSV-import version would still require the same manual file handling the user is trying to eliminate, so it wouldn't feel like progress even though it's the safer default a risk-avoidance heuristic would pick.

## Confirmed in scope
- One account only for this step: the user's main checking account.
- A live, automatic connection to that account (not file import, not manual entry).
- Hosted somewhere off the user's own hardware — a cheap host reachable from their phone.

## Confirmed out, for now
- Connecting any other accounts beyond the one checking account — the user has several but only wants one connected to start.
- CSV import as an approach — considered and rejected; it wouldn't remove the manual step the user is trying to eliminate.
- A second person (partner) actually using this — expected eventually, not now (see Constraints in force for what this already requires at this step regardless).

## Constraints in force
- **Zero cost, permanently.** Applies here: the bank-connection method for this one account has to carry no ongoing metered cost — this rules out any live-connection vendor whose pricing is per-account or per-call, not just paid software in general.
- **Financial data is the core asset (hosting off own hardware allowed; encrypted in transit and at rest).** Applies here, and forces two things: the connection credentials/token and the retrieved transaction data must be encrypted both in transit and at rest, given hosting is confirmed to be off the user's own hardware. And because this data will be displayed by a system reachable over a network rather than run locally, something has to establish who is asking before this account's transactions are shown — an access-control gate, even though "transaction retrieval" doesn't sound like it owns that question.
- **Categorization must match the existing hand-done scheme.** Does not apply to this step — step 1 only retrieves raw transaction records; no categorization decision happens here. That's step 2's constraint to reconcile.
- **Single user today, not single-user forever.** Applies here: even though only one person uses this today, nothing in how this step models the connected account may hardcode a single fixed identity — the account needs an owner reference rather than being a global singleton, so a second user can be added later without redoing this step's data model. This is a modeling constraint on step 1 itself now, not a note deferred to when the partner actually joins.
```
</content>
