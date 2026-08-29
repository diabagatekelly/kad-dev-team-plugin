Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/vertical-slicing/SKILL.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/acceptance-criteria/SKILL.md

# Slice 1: Import a CSV and see transactions auto-categorized against your existing categories

## Thin path
A single user uploads a CSV export of transactions from one account. Each transaction's description is matched against the provided sample of prior manual accounting; a match assigns that sample's category, and anything without a match is shown as "Uncategorized" rather than dropped or guessed. No login, no bank credentials, no AI vendor, no budget comparison, no money movement — just today's manual entry-and-categorization step, done for you.

## Acceptance criteria

**Categorization — match found**
Given an imported transaction whose description matches (case-insensitive, exact string) a description in the provided sample data,
When the import completes,
Then the transaction is shown with that sample entry's category, with no manual selection required.

**Categorization — no match found**
Given an imported transaction whose description matches nothing in the provided sample data,
When the import completes,
Then the transaction is shown as "Uncategorized" and is visually distinguishable from categorized transactions, rather than dropped or guessed into a category.

**Invalid file**
Given a file that isn't a parseable CSV, or is missing a required column (date, amount, description),
When the user attempts to import it,
Then the import is rejected with a message identifying the file as unreadable, and no transactions are added.

**Duplicate import**
Given a transaction with a given date, amount, and description has already been imported,
When a CSV containing a transaction with that same date, amount, and description is imported again,
Then it is not added a second time to the list.

**Security placeholder**
Given this slice stores real transaction data (dates, amounts, descriptions) locally,
When `security-engineer` reviews this slice,
Then they define concrete, testable criteria for how that data is stored and handled at rest — not assumed satisfied by "it's local-only."
*(Placeholder — not authored by this persona; security expertise required.)*

**Accessibility placeholder**
Given this slice ships a CSV upload control and a categorized transaction list as real UI,
When `accessibility-engineer` reviews this slice,
Then they define concrete, testable accessibility criteria for those two elements — not assumed satisfied by default.
*(Placeholder — not authored by this persona; accessibility expertise required.)*

## Explicitly deferred
- **Bank-aggregation API import** — CSV proves the categorization value end-to-end without touching bank credentials, the single biggest security surface in the whole feature. Becomes its own later slice (input-variation), not a dropped requirement.
- **AI/ML-driven categorization** — rule-based matching against your sample satisfies "must stay free" with zero AI vendor involved, and uses the constraint you already gave. AI/ML becomes an enhancement slice once there's a rule-based baseline to compare it against.
- **Budget-vs-category spend check** — a real part of the monthly workflow in the problem doc, but it depends on transactions already being categorized, which this slice produces but doesn't consume. Slice 2 (workflow-steps slicing).
- **Move-money recommendation (fixed rule vs. threshold vs. other)** — same reasoning; depends on both categorization and budget-check existing first. Deferring the whole capability, not just the trigger detail.
- **"Must stay free" — AI-only vs. entire infra stack** — doesn't affect slice one either way, since it needs no AI vendor and no hosted infra to run. Flagging for `software-architect` to confirm against whatever hosting choice eventually gets made.
- **Multi-account import in one pass** — one CSV, one account, at a time. A second account is "import again," not a new capability.
- **Unauthorized-access criteria** — not included. Single-user is confirmed, so there's no access-control surface in this slice to write a criterion against yet.

## Still open
- **Exact CSV column layout and the real content of the sample categorization data** — needed by `software-architect`/`tdd-coach` to build the actual parsing and matching logic; doesn't block this write-up (deliberately format-agnostic), but blocks implementation.
- **Matching key (exact description string match)** — named as a decision, not a settled fact: if real descriptions vary in formatting, this may under-match and should be revisited before implementation.
- **Security and accessibility review itself** — tracked via the two placeholders above; needs `security-engineer` and `accessibility-engineer` once those personas exist.
- **"Very secure" anticipating shared access later** — single-user is answered for slice one, but if shared/multi-device access matters down the line, that reintroduces an identity concept this slice deliberately skips. Flag for whoever scopes that slice.
