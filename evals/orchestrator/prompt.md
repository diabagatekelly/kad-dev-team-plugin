---
name: orchestrator
tags: [orchestrator]
runs: 3
---

You're working across eight independent, unrelated invocations of the
orchestrator skill. For each, apply step 1 (identify the target), step 2
(inspect), and the routing table in step 3, then state: (1) what state you
detected, (2) what you'd do next — which persona/skill you'd route to, or
what you'd ask if a step requires asking before anything else can happen,
and (3) why. This is a dry run of the routing decision only — do not
actually produce any artifact or adopt any other persona's identity, and
don't chain past the one next step for any directory.

## Directory A

You were invoked with the artifacts directory parameter set to
`examples/newsletter-app/`. Its contents: empty — no files at all.

## Directory B

You were invoked with the artifacts directory parameter set to
`examples/recipe-app/`. Its contents:
- `problem-framing.md`, top heading `# Problem: Recipe Bookmark Sprawl`

No scope-map, requirements, or slice files.

## Directory C

You were invoked with the artifacts directory parameter set to
`examples/budgeting-app/`. Its contents:
- `problem-framing.md`, top heading `# Problem: Manual Personal Finance Tracking`
- `scope-map-001.md`, containing:
  ```
  ## Status
  Active

  ## Steps
  1. Transaction retrieval — getting transaction data into the system.
  2. Transaction categorization — assigning a category to each transaction.
  3. Budget & spending view — showing actual spend against budgeted amounts.
  4. Checking/savings rebalancing — surfacing how much surplus to move.
  ```

No `requirements-*.md` or slice files anywhere in the directory.

## Directory D

You were invoked with the artifacts directory parameter set to
`examples/travel-planner/`. Its contents:
- `problem-framing.md`, top heading `# Problem: Ad Hoc Group Trip Planning`
- `requirements-001.md`, top heading `# Requirements: problem: Ad Hoc Group Trip Planning (requirements-001)`, `## Status` = `Active`

No scope-map file (this problem was small enough to skip one) and no
slice files yet.

## Directory E

You were invoked with the artifacts directory parameter set to
`examples/inventory-app/`. Its contents:
- `problem-framing.md`, top heading `# Problem: Small-Batch Inventory Drift`
- `scope-map-001.md`, `## Status` = `Active`, with steps including step 1
  "Stock count entry"
- `requirements-001.md`, top heading `# Requirements: scope-map-001 step 1 (requirements-001)`, `## Status` = `Active`
- `slice-1.md`, top heading `# Slice 1 (scope-map-001 step 1): Record a manual stock count for one item`

No file anywhere indicating this slice has been written up as a user
story yet — no `pr-writeup`/user-story artifact, and the user hasn't
mentioned filing it.

## Directory F

Same as Directory E, except: the user tells you slice 1 has already been
written up as a user story and filed, **and** `software-architect` has
already produced a design doc for it (`design-1.md` exists, titled
"Design: Record a manual stock count for one item"). Nothing else has
changed — no code exists yet, no slice 2 exists.

## Directory G

The user says: "I want to figure out how to split shared household bills
fairly — can we start scoping this out?" You were invoked with **no
artifacts directory parameter** — nothing was given to you, and nothing
was mentioned about where this should live.

## Directory H

Same as Directory E, except: the user tells you slice 1 has already been
written up as a user story and filed. Nothing else has changed — no
architect design exists yet, no slice 2 exists.
