Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/architecture-design/SKILL.md

Approved — *(scripted answer: "Agreed — build CSV export directly, skip the generic interface. We can add the abstraction later if a second format actually gets requested.")* — CSV export is built directly, no generic pluggable-formatter interface.

Both decisions for this slice are now approved. Final design:

```markdown
# Design: Export transaction list as CSV

## Importance ordering assumed
Which transactions get included in the export — respecting the active filter, one row per transaction, an empty list producing a header-only file — is a business rule and stays strategic: it's the actual behavior this slice promises, independent of any file format or library. The CSV-writing mechanics themselves (delimiter handling, escaping, line endings) are tactical: swapping the serialization library wouldn't change what the business does, only how the bytes get produced.

## Structure
**Strategic:** an export-row selector (the business rule for which transactions to include and in what order, producing plain data rows — not CSV-specific in any way).

**Tactical:** a CSV writer adapter (the sole importer of the CSV-serialization library, turning plain data rows into actual CSV bytes) and an export-delivery piece (returning the generated file synchronously as part of the request).

## Boundaries and interfaces
One boundary: between the export-row selector (strategic) and the CSV writer (tactical). The strategic side owns the interface; what crosses it is plain data — an ordered list of rows, each a plain record of the fields to export (date, description, amount). Nothing CSV-specific (no delimiter choices, no library types) crosses back into the strategic side.

## Third-party isolation
The CSV-serialization library (e.g. `csv-stringify`, as the engineer proposed) is a narrowly-scoped, types-only-ish utility with low lock-in cost — fine to use directly inside the CSV writer adapter, which is already the only place that imports it by virtue of the boundary above. Isolating it further behind its own dedicated interface would be ceremony with no payoff at this scope.

## Technology at each boundary
The export-row selector / CSV writer boundary forces a real technology choice now — this slice's whole purpose is producing an actual CSV file, so an in-memory stand-in wouldn't satisfy its own acceptance criteria. Accepting the engineer's proposed library for this: it's a narrow-scope, low-lock-in choice (see Third-party isolation above), not an architecturally significant fork worth its own approval round on top of the two decisions already made for this slice.

No other boundary in this slice forces a technology choice — the slice reads transactions already available to the view it's exporting from, so no new persistence boundary is introduced here.

## Decisions
1. **Export execution: synchronous vs. background job.** Proposed synchronous, with an async job queue as the rejected alternative (unneeded infrastructure for a single user's own, small transaction history). Presented for approval; approved as proposed, synchronous. Not ADR-worthy — cheap to reverse if volume assumptions change.
2. **Generic pluggable-formatter interface vs. CSV built directly.** Proposed building CSV directly and rejecting the generic interface, with the engineer's proposed generic interface as the rejected alternative (premature — only one format exists today). Presented for approval; approved as proposed, CSV built directly. Not ADR-worthy — cheap to reverse if a second format is actually requested.

## Existing violations touched
None — this is new code with nothing pre-existing to reconcile.

## Open questions
None blocking this slice. If a second export format is ever requested, that's the trigger to revisit the generic-interface decision above — not something to design for now.
```
</content>
