Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/architecture-design/SKILL.md

# Design: Export transaction list as CSV

## Importance ordering assumed
Which transactions are included in the export (the currently-filtered set
shown in the view) is a business rule — getting it wrong means the user
downloads the wrong data, so it's kept independent of any library. How the
CSV bytes actually get written is low-importance and freely swappable —
nothing about the business changes if the CSV-writing mechanism changes.

## Structure
- **Strategic**: a transaction-export concept responsible for taking the
  currently-displayed/filtered transaction set and producing plain row
  data (one row per transaction, matching the AC) — this is where the
  "what gets exported" business rule lives, named for the export itself,
  not a technical role.
- **Tactical**: a CSV-writing adapter that takes the plain row data and
  produces CSV bytes, and the request-handling code that calls the export
  logic synchronously (per the approved decision below) and returns the
  resulting file — both swappable without touching the business rule
  above.

## Boundaries and interfaces
The boundary between the strategic export logic and the tactical
CSV-writing step passes plain data only: an ordered list of plain rows
(arrays/objects of primitives), never a library-specific type. No
interface is needed on the strategic side purely for the Dependency Rule
here — the tactical CSV-writing step is a leaf the strategic side calls
into with plain data in, plain bytes out; there's no case today where the
strategic side needs to be agnostic about *which* writer it's calling,
since there's only one (see the rejected pluggable-interface decision
below).

## Third-party isolation
`csv-stringify` is a narrowly-scoped, single-purpose library — Low risk
tier. It's fine to call directly from the tactical CSV-writing step; a
dedicated domain interface and adapter for it would be isolation ceremony
with no payoff, the kind reserved for higher-lock-in-cost libraries like
an ORM or a cloud SDK. This is a rule application, not a decision — there
was no real alternative worth presenting for approval.

## Decisions
- **Synchronous vs. asynchronous export — presented for approval,
  approved as proposed.** Proposed: synchronous, given the confirmed data
  volume (a single user's own history, never more than a few hundred
  rows) — a background job with polling/notification would be structure
  built for a scale problem that doesn't exist. Alternative considered: an
  async job queue, rejected for the same reason. Approved as proposed.
- **Generic pluggable-export-formatter interface — presented for
  approval, approved as proposed (rejected).** Proposed: reject it and
  build CSV export directly, since there's no second concrete format today
  and an interface built for formats nobody's asked for yet is a premature
  abstraction. Alternative considered: building the generic interface now
  anyway, rejected since a second format isn't a near-term certainty.
  Approved as proposed — CSV export is built directly; the interface gets
  extracted if and when a second format is genuinely requested.

Neither decision cleared the ADR bar (architectural + significant +
non-obvious) — both are scoped to this one slice and easily reversible if
a second export format or a scale requirement shows up later, so no ADR
was offered.

## Existing violations touched
None — this is new, additive structure; it doesn't touch or need to modify
anything upstream.

## Open questions
None load-bearing for this slice's structure. If a second export format is
ever requested, that's when the pluggable-interface question gets
revisited — not before.
