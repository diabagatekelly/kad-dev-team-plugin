# Combined chunk review: chunk @K@, @TITLE@ (round 0)

Range `@FROM@..@TO@`; lenses `code-review`, `test-quality-review`@RE@.

## Fake inventory

| Double | Replaces | Verdict |
|---|---|---|
| a `HoldQueue` whose `remove` throws | the in-memory queue, for the unreachable branch only | fine: the seam test cannot reach it, and the Test List names the branch |

## Findings

No findings.

Counts: C0 H0 M0.
