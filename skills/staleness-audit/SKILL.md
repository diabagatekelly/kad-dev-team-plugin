---
name: staleness-audit
description: Audit existing documentation for staleness and ceremony. Use when reviewing a docs folder to find entries that mislead, restate the code, exist only for ritual, or disagree with the codebase's actual decision history.
---

# Staleness / Ceremony Audit

When reviewing existing docs (not writing new ones), flag:

- **Stale**: describes behavior the code no longer has. Worse than no doc,
  because it actively misleads.
- **Restates code**: could be deleted with zero information loss because the
  code already says it as clearly.
- **Ceremonial**: exists to satisfy a process checkbox, not to answer a real
  future question. Usually identifiable because no one can say who would
  read it or when.
- **Orphaned decision history**: an ADR or scope map that was quietly
  overturned in practice but never marked Superseded — the doc and the
  codebase (or the doc and how the problem was actually sliced) now disagree
  about what was decided.

Report findings the same way any review does: file, the specific claim that's
wrong or pointless, and what to do about it (delete, update, or supersede).
Don't propose new process to prevent staleness — the fix is almost always
"delete the doc," not "add a review cadence."

**Audit the docs, not the code.** When a doc and the code disagree, the
finding is the doc. If the code looks like the thing that's wrong, say so
in one line and leave it to `code-review`, rather than reviewing it here.

**Write for skimming.** Lead with the point; prefer bullets and headers to
prose; a paragraph is one or two sentences at most. If a sentence wouldn't
change what the reader does next, cut it.
