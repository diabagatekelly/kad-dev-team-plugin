---
name: architecture-cartographer:map-query
tags: [architecture-cartographer, map-query]
runs: 3
---

You're `architecture-cartographer`, consulted inline by another persona
mid-conversation. Here's the project's current persisted architecture map:

```markdown
# Architecture map — updated 2026-08-02

## Modules
| Path | Tier | Internal edges (imports) | External packages | Public exports |
|---|---|---|---|---|
| domain/case-directory.ts | tier 1 | none | none | CaseDirectory, findCaseById, listCasesByStatus |
| domain/case-directory.types.ts | tier 1 | none | none | CaseDirectory (interface), CaseSummary |
| domain/assign-case.use-case.ts | tier 1 | domain/case-directory.types.ts | none | AssignCaseUseCase |
| infra/mongo-case-directory.ts | tier 3 | domain/case-directory.types.ts | mongodb | MongoCaseDirectory |
| infra/notification-client.ts | tier 3 | none | @sendgrid/mail | NotificationClient, sendAssignmentEmail |
| ui/case-list-view.tsx | tier 3 | domain/case-directory.types.ts | react | CaseListView |

## Changes since the prior map
New: domain/assign-case.use-case.ts, infra/notification-client.ts (both added for the case-assignment slice).

## Duplication candidates
None found.

## Wrong-direction candidates
None found.
```

A teammate mentions, in passing, that a branch adding a `RefundLedger`
module finished yesterday and hasn't gone through a `map-update` run yet.

Answer these three questions, in order, using `map-query`:

1. **(architecture-design, structural level)** "We're about to design a
   slice that needs to persist and retrieve court-order records tied to a
   case. Does a comparable structural boundary already exist?"
2. **(tdd-implementation, implementation level)** "I'm about to write a new
   `OrderRepository` class with methods to find a record by ID and list
   records by status. Does something like it already exist?"
3. **(tdd-implementation, implementation level)** "I'm about to write a
   helper that renders a case summary as a downloadable PDF. Does
   something like it already exist?"
