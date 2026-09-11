# software-architect:technology-bootstrap — eval summary

**Result: PASS — 6/6 graders passed**

| Grader | Result |
|---|---|
| skill-invoked | PASS |
| asks-only-what-the-first-test-forces | PASS |
| defers-persistence-with-the-in-memory-reason | PASS |
| pinning-posture-treated-as-a-choice | PASS |
| recommends-rather-than-decides | PASS |
| records-non-choices-and-open-categories | PASS |

## Notes

First run of this case (previously "written, never run"). `software-architect`
is `background: false`, so this ran via the agent-eval harness's **inline
path** rather than a spawned subagent — emulated directly in-conversation,
self-resolving each ask-recommend-approve cycle with the case's scripted
answers rather than pausing for real input each time.

The negative grader (`asks-only-what-the-first-test-forces`) — the one this
case exists for — passed cleanly: CI/CD, hosting, a database, observability,
and an auth provider were never solicited as decisions, only named as
explicitly-open categories with owners. The persistence defer used the
skill's own "in-memory implementation satisfies the tests" reasoning rather
than treating the boundary's existence as itself forcing a technology.

One judgment call worth flagging for future runs: UI framework was treated
as *not* forced by the first failing test, on the reasoning that the first
testable behavior is connection/store logic rather than rendering. This is
a defensible reading of "decide by looking at the test, not the category,"
but it's a real interpretive choice, not a mechanical one — a differently
-shaped first test could force it. No grader in this case checks that call
either way.
