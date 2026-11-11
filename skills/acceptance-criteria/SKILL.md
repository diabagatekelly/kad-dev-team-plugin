---
name: acceptance-criteria
description: Judge and write acceptance criteria that are actually testable — Given/When/Then scenarios, common pitfalls (vague language, specifies-HOW-not-WHAT, happy-path-only, prescriptive UI detail, self-contradiction), and the boundary between AC and Definition of Done. Use whenever acceptance criteria need a quality check, whether or not a new slice is being cut.
---

# Acceptance Criteria Quality

Write scenarios, not descriptions. Each one names a precondition, an action,
and an observable outcome — vague enough language ("works correctly",
"handles errors") is a sign the criterion isn't actually testable yet.

```markdown
Given <a concrete starting state>
When <a single action>
Then <an outcome someone could verify by looking, with no ambiguity>
```

Bad: "The app assesses fines correctly."
Good: "Given a loan returned three days after its due date, when it is
checked in, then a fine of three days at the board's daily rate is
assessed to that member's account."

A slice with acceptance criteria that all read like the "bad" example isn't
ready to hand to `tdd-coach` or `code-reviewer` yet — send it back.

**Four more pitfalls to check for**, beyond plain vagueness:

- **Specifies HOW, not WHAT.** "Uses MongoDB to store the transaction" is an
  implementation detail; "the transaction is retrievable after import" is
  the outcome. If a criterion names a database, library, or UI element, it's
  prescribing a solution instead of describing a result.
- **Happy-path-only.** A slice whose criteria only cover success is missing
  half its scope. At minimum check for: the primary path, unauthorized
  access, invalid input, the "not found" case, and duplicate/repeat action —
  drop whichever don't apply, but check all of them.
- **Overly prescriptive UI detail.** "The button is blue and 40px tall" is
  unfalsifiable as a *behavior* claim and will be wrong the moment someone
  restyles it. "I can identify and activate the import control" survives a
  redesign.
- **Self-contradicting.** Two criteria that can't both be true at once
  (e.g. one says transactions are categorized on import, another says
  categorization only happens manually) — a sign the underlying behavior
  wasn't actually decided yet, not just an editing slip.

**A file the owner provides is described, never quoted.** A sheet, an
export or a screenshot the owner points at stays where it is, outside the
repository, and nothing in it is written down by value: not in this
document, not in a question, not in a reply. In this order:

1. **List it before anything opens it**, as a row of `sources.md` in the
   target directory (create the file in this shape when it is not there).
   `Listed at` is `git rev-parse --short HEAD` at that moment: what was
   in the tree at that commit cannot have come from a file nobody had
   read, and the scan does not count it. Write a dash instead when there
   is no commit or no shell, and whenever the file was read, or a value
   of it may already be written down, before this row existed: with a
   dash everything counts. In `Tab or range`, name the one tab the stage
   reads when the file has several, never `all` for a workbook of many:
   the scan reads the tab named and nothing else, and every cell of
   every tab of a large workbook matches the language of any repository.

   ```markdown
   # Sources

   Files the owner provided. Locations only: no value from any of them
   is written here or anywhere else in the repository. Nothing opens one
   of them but kad-dev-team's `source_scan.py` (its `describe` for a
   file's shape, its `scan` for what got written down): never `cat`,
   read or grep one. A value that reached a commit is removed by the
   `delivery` skill's "Removing a value from history", on the owner's
   words, and no other way.

   | Source | Location | Tab or range | Read on | Listed at |
   |---|---|---|---|---|
   | <what it is> | `<its path, outside the repository>` | <the tab or range the owner named> | <date> | `<commit>` |

   ## Allowed by the owner

   Values a source also holds that the owner has said may be written,
   in their words, dated. Nobody else adds a line.
   ```
2. **Read its shape, not its rows**, and only the tab or range the owner
   named: `python3 -I "${CLAUDE_SKILL_DIR}/../orchestrator/scripts/source_scan.py"
   describe '<path>' --tab '<tab>'` prints the column names, the row count
   and what kind of cell each column holds, and never a cell (add
   `--extract '<a scratch file outside every repository>'` when rows have
   to be counted by a script: the session never prints that file). With
   no shell: the first line alone for the column names (`Read` with
   `limit: 1`) and a count-only search for the rows. Never `cat`, `head`,
   `Read` in full or load the file with a library to look inside:
   whatever a command prints stays in the session's transcript for good,
   and one command that dumps a file puts the whole of it there (incident
   15). A file `describe` cannot read (a screenshot, a PDF)
   is listed the same way and looked at for its layout alone.
3. **Invent every example** (the names, the amounts, the dates) and say
   so once in the document ("examples are invented; none is a row of the
   sheet"), however much better a real row would make the point. One real
   row taken as an example in a requirements document was carried by the
   slice, the design, the story, the plan's test names and thirteen test
   files (incident 16).
4. **Check what you build on before you repeat it.** When `sources.md`
   lists a source, `python3 -I "${CLAUDE_SKILL_DIR}/../orchestrator/scripts/source_scan.py"
   scan --planning '<target directory>'` prints the file, line and cell of
   every value of a listed source it finds, never the value. A hit in
   your own document is rewritten with an invented value; a hit in a
   document that is not yours is reported as a backward route to its
   owner, not edited; a hit that is the app's own word and no row of the
   file is the owner's to allow, never yours. The readiness gate and the
   chunk gate run the same scan.

**Acceptance criteria are not a Definition of Done.** AC describe the
user-observable behavior a change adds; DoD is the separate, broader
checklist for whether it's actually shippable (tests written, reviewed,
deployed). Don't let a slice write-up quietly turn into a DoD — that
checklist belongs to the personas who own testing/review/deploy, not to
scoping.

**Reviewing one criterion doesn't need a slice write-up.** When there's no
slice being cut, shape the review as: verdict (done / not done / rejected),
why, the fixed rewrite. That's it — don't borrow "Explicitly deferred" or
"Still open" headers from a slice write-up for a task that isn't one; an
empty deferred section is a tell that the wrong template got used.

**If fixing one criterion exposes a gap outside this review** — e.g. the
rewrite implies a case (a miss, an error path) that has no criterion of its
own yet — flag it explicitly, with concrete options if there's a real
decision to make. Don't silently pick one and fold it into the rewrite as
if it were already decided; that's a product call, and this review's job
is judging the criterion in front of it, not making that call for someone.

**The rewrite can't decide what the vague criterion never decided.**
"Handles errors gracefully" doesn't say what a member sees when the
provider is down; making it concrete means choosing that outcome, and the
choice isn't yours. Mark the undecided outcome in the rewrite as a decision
for the user, with options, or route it to the placeholder that owns that
kind of criterion (a reliability or security placeholder) and say so.
