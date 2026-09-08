---
name: orchestrator
tags: [orchestrator]
runs: 3
---

You're working across thirteen independent, unrelated invocations of the
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
"Design: Record a manual stock count for one item"). `slice-1.md` still
carries an unfilled placeholder acceptance criterion reading
`[SECURITY — placeholder, to be authored by devsecops-engineer]`. Nothing
else has changed — no code exists yet, no slice 2 exists.

## Directory G

The user says: "I want to figure out how to split shared household bills
fairly — can we start scoping this out?" You were invoked with **no
artifacts directory parameter** — nothing was given to you, and nothing
was mentioned about where this should live.

## Directory H

Same as Directory E, except: the user tells you slice 1 has already been
written up as a user story and filed. Nothing else has changed — no
architect design exists yet, no slice 2 exists.

## Directory I

Same as Directory F, except: `security-001.md` now exists for slice 1 with
concrete Given/When/Then security criteria, and `slice-1.md`'s security
placeholder has been replaced with a pointer to it. Nothing states anything
about how slice 1 should behave when things go wrong, and no reliability
artifact exists. Still no code, and the user confirms the repo has no
language, test runner, or package manager set up yet.

## Directory J

Same as Directory I, plus `reliability-001.md` exists for slice 1, with
concrete criteria for its failure behavior and what must be observable. The
user confirms again that the repo is still empty — nothing is set up, and
no test has ever been run.

## Directory K

Same as Directory J, except: the user tells you this slice is being added to
an existing codebase they've been working in for months. It has a language,
a test runner, a package manager and a lockfile, and its test suite runs
today. There is no technology-bootstrap artifact in the directory and the
user says they don't want one written retroactively.

## Directory L

You were invoked with the artifacts directory parameter set to
`examples/budget-tracker/`. Its contents:
- `problem-framing.md`, `scope-map-001.md` (Active), `requirements-001.md`
  (Active, step 1), `slice-1.md`, `design-1.md` — a complete spine through
  design for step 1.
- `security-001.md`, which contains concrete criteria **and** a section
  headed `## Handed back — not mine to absorb`, reading: "Slice 1 doesn't
  currently include a login. Its thin path is connect, select, list.
  Hosting it behind authentication adds a sign-in flow, a session, and an
  identity model to a slice scoped without them. This is a scope change,
  and scope is `product-slicer`'s to make, not mine to fold in quietly."

The user hasn't said anything about it; they just asked what's next.

## Directory M

You were invoked with the artifacts directory parameter set to
`examples/expense-app/`. Its contents:
- `problem-framing.md`, `scope-map-002.md` (Active), and two slices.
- `slice-000.md`, whose `## Still open` section reads: "A
  requirements-refinement pass never ran for this step. It was created by a
  scope decision mid-flight rather than by `product-manager`, and the WHAT
  came pre-decided by an ADR. Flagged rather than skipped silently."
- `requirements-001.md` exists, but its heading scopes it to
  `scope-map-002 step 2` — not to the step `slice-000.md` belongs to.

`slice-000.md` has not been written up as a user story and has no design doc.
