# Security review: slice 001, the whole slice (round 0)

Range `@BASE@..@HEAD@`.

## Findings

### The notice markup interpolates the reason into HTML unescaped

**Severity:** Medium
**Location:** lending/cancel-hold-notice.ts:38
**Category:** injection

**What's happening:** `cancelNotice` builds `<p>${body}</p>` from `result.reason`, which carries the ISBN and the card's last four digits as given to `run`; nothing escapes them.

**Why it matters:** the next slice serves this markup to the desk screen; an ISBN typed at the desk with markup in it renders as markup.

**Suggested fix:** escape the heading and body before interpolating, and pin it with a test that passes a reason with a tag in it.

Counts: C0 H0 M1 L0.
