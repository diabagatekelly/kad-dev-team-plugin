---
name: software-architect:architecture-design
tags: [software-architect, architecture-design]
runs: 3
---

**Format note:** this case models a multi-decision approval loop — the
persona now presents every real decision one at a time and waits for
approval before moving on, which can take more than one round. The
packaged `agent-eval` procedure only documents a single
phase1-question → scripted-answer → final-output round; this case extends
that to a second round the same deliberate way this plugin's `evals/README.md`
already documents adapting the harness elsewhere. `eval-result/` for this
case holds `phase1-question.md`, `phase2-question.md`, and `output.md`
(the finished artifact, after both approvals). Graders may target
`phase1` or `phase2` accordingly; anything else grades `output.md`.

A slice has already been cut by product-slicer. Design its structure
before any code is written:

# Slice: Export transaction list as CSV

## Thin path
From the transaction list view, the user clicks "Export CSV" and gets a
CSV file of the transactions currently shown in that view.

## Acceptance criteria

Given the user is viewing their transaction list,
When they click "Export CSV,"
Then they receive a CSV file containing exactly the transactions currently
displayed (respecting any active filter), with one row per transaction.

Given the transaction list is empty,
When they click "Export CSV,"
Then they receive a CSV file with just a header row, not an error.

## Explicitly deferred
- Export formats other than CSV.
- Scheduling/emailing a recurring export.

## Still open
- Whether export should run synchronously in the request or be handled
  some other way — a technology/structure decision, not this persona's
  call.

The engineer about to build this adds: "While I'm in here, I'll add a
generic export interface with pluggable formatters so we can bolt on PDF
and JSON export later without much rework. I'm planning to use the
`csv-stringify` npm package for the actual CSV generation."

## Scripted answers

- If asked to approve running export synchronously vs. asynchronously via
  a background job: "Synchronous is fine — this is a single user's own
  transaction history, never more than a few hundred rows. No plans to
  support exporting other people's data or anything at real scale."
- If asked to approve rejecting the generic pluggable-formatter interface
  in favor of building CSV export directly: "Agreed — build CSV export
  directly, skip the generic interface. We can add the abstraction later
  if a second format actually gets requested."
