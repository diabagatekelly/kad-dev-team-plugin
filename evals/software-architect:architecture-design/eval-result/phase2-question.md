Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/architecture-design/SKILL.md

Approved — *(scripted answer: "Synchronous is fine — this is a single user's own transaction history, never more than a few hundred rows. No plans to support exporting other people's data or anything at real scale.")* — export runs synchronously in the request.

Next decision: the engineer proposed **a generic export interface with pluggable formatters, so PDF and JSON export can be bolted on later without much rework.**

**Recommendation: reject it — build CSV export directly, no generic interface.** Only one format exists today. A pluggable-formatter abstraction earns its place when there are at least two concrete formats that need it *now* — a plausible future format isn't a second real use case, it's a guess at one. Building the generic shape today means designing an interface against requirements (PDF's, JSON's) nobody has actually stated yet.

**Alternative considered and rejected: building the generic interface now, as the engineer suggested.** This is the premature-abstraction case this design process exists to catch — the interface would be speculative today and easy to add for real once a second format is actually requested, at which point the actual shape of that need will be known instead of guessed. This isn't ADR-worthy either — rejecting it costs nothing to reverse if a second format shows up next month.

Agree, or do you want the generic interface built now?
