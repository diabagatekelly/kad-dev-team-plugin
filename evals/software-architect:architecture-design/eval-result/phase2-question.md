Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/architecture-design/SKILL.md

Going with synchronous export, approved.

Second decision: the engineer proposed adding a generic export interface
with pluggable formatters now, so PDF and JSON support can be bolted on
later without rework.

**My recommendation:** reject it — build CSV export directly instead.
**Why:** there's no second concrete format needed today; an interface
built to support formats nobody's asked for yet is a premature
abstraction. If a second format is genuinely requested later, that's the
point to extract the interface, informed by what that format actually
needs rather than a guess made now. **Alternative considered:** building
the generic interface now anyway — this would only pay off if a second
format were already a near-term certainty rather than a "later maybe,"
which isn't the case here.

Do you want CSV export built directly, or should I go ahead with the
generic interface as proposed?
