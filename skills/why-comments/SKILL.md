---
name: why-comments
description: Judge whether a code comment earns its place, using a WHY-not-WHAT test. Use when writing, reviewing, or deciding whether to delete an inline code comment.
---

# WHY-not-WHAT Comments

Default to zero comments. A comment earns its place only when it explains
something the code cannot express on its own:

- a constraint that isn't visible locally ("this must stay synchronous — the
  caller holds a lock")
- a workaround for a specific external bug or limitation
- a non-obvious invariant a future edit could silently break
- a rejected-sounding-more-obvious alternative and why it doesn't work

Never write a comment that a reader could produce by reading the next line.
`// increment counter` above `counter++` is noise, not documentation. Delete
comments like this on sight during review rather than leaving them.

**Judge the comments, not the code.** For each comment in scope: keep,
delete, or rewrite (give the rewrite). Naming, logic and structure belong
to `code-review`; if you notice a real code problem, one line saying so
and where is enough — one sentence inside the comment's own verdict, not
a section of its own, not a second problem added to it, not what the fix
should be or which review should look. A comment that contradicts the
code (it says "once" over a loop) is a comment finding: the comment is
wrong, and that is the whole verdict here; what the loop should do is the
code's reviewers' question, raised in that one sentence and left there.
The answer the user asked for is about the comments, and a review that
goes on to the code has answered a question nobody asked.
