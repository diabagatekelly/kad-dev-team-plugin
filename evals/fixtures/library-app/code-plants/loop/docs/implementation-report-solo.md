# Implementation report: slice 001

## Criteria
| Criterion | Test | Level | Why this level |
|---|---|---|---|
| A member with a hold: cancelled, gone from the queue | "cancels a member's hold through the real in-memory queue" | port | the slice has no route yet; the use case over the real in-memory queue is its outermost interface |
| A member with no hold: rejected with a reason, queue unchanged | "rejects a cancel when the member has no hold on the title" | port | as above |
| Security: only the named hold is removed | "removes only that member's hold on that title" | port | as above |
| Reliability: twice in a row, an unreachable queue | "a second cancel of the same hold through the real queue is a rejection" | port | as above |

## Branch tests
| Test | Branch | Why no criterion's test reaches it |
|---|---|---|
| "a queue that cannot be reached fails the cancel and leaves the queue as it was" | the queue's failure path | the real in-memory queue never fails; a queue that throws is passed at the port |
| "a reason with markup in it is shown as text, not rendered" | the notice's escaping | no criterion's test renders the notice |

## Wording
lending/cancel-hold-notice.ts: "a rejected result carries its reason into the notice" (3 strings)

## Decided
- The rejection reason names the card's last four characters and the ISBN.

## Escalated
- none

## Deviation
- none

## Verified
First run: 15 tests, all failing on their assertions. Suite: 15 green.
Break: the queue's match flipped to `!==`, caught by "cancels a member's hold through the real in-memory queue", restored, green.
