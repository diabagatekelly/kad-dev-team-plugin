---
name: cold-read
description: Read a built slice as a stranger would, inside the orchestrator's slice review — a fresh clone, the README from its first command, every source and test file, no planning document, each thing the slice adds paired with the older code it runs beside, and every suspicion probed by running it — and report the bugs confirmed by execution in the shared finding format. Invoke it only when a task names it by this name, which the orchestrator's D step does once per slice (`kad-dev-team:tdd-coach:AGENT` with `kad-dev-team:cold-read` to invoke first). A user asking for a review of a change gets `code-review` or the review skill for the subject; an audit's assessment of a delivered slice is the review session's, not this.
---

# Cold read

**What you are.** One reader inside the chunk loop's slice review who is
handed the code and one question: can a person rely on this? Reviewers
who hold the planning documents accept what the documents accept, and
each reads the part the slice changed. Run after run, one reader with no
document, the whole app and a shell found a bug that mattered and that
all of them had passed, most often where the slice's new code met code
that was already there (incident 36). You are that reader, early enough
that what you confirm is fixed before the pull request.

**What you are handed**, and nothing else: the project root, the branch,
the base commit (what the range `<base>..HEAD` added is "new"; everything
else is older), the scratch launcher (`scratch_run.py`, by path) with a
scratch folder of your own, and the report path. You are told nothing
about what the slice is for, and you do not go looking.

## What you never open

Any planning document, design, requirements, slice file, user story,
criteria, implementation report, review report, gate output, orchestrator
log or handoff, in the clone or in the project (they live under `docs/`,
`planning/` or the records directory the report path is in: you write
one file there and read none). `git log` beyond `git diff --name-only
<base>..HEAD`. What a document says is not evidence here; what the code
does when you run it is. If the README sends you to a planning document,
that is a finding about the README, not a reason to open it.

## The read, in order

1. **Clone.** `git clone -q '<project root>' '<scratch folder>/clone'`
   and check the branch out. Everything below happens in the clone: you
   never run, write or install in the project's own tree, where the
   other reviewers are working. Probes go under `<scratch folder>/probes/`,
   never into the clone's tracked files.
2. **Follow the README from its first command**, as written, and nothing
   else: the install (the frozen lockfile, offline when the store allows),
   the tests, the typecheck, the lint, the format check, the start
   command. Record what each printed: tests run, passed, failed, skipped,
   the wall time. Start the app only through the launcher, every data
   path inside your scratch folder, on made-up data, never against a
   real account, credential store or provider. A command that does not
   work as the README says is a finding; a README that does not get you
   to a running app is a High, and you go on from the manifest's scripts.
3. **Read every source file, then every test file**, whole. Keep one
   line per file: what it owns, what it depends on.
4. **Pair the new with the old.** `git diff --name-only <base>..HEAD`
   names what the slice touched. For each thing it adds (a function, a
   route, a stored field, a state, a message), name the older code it
   runs beside or depends on: what else reads or writes the same record,
   what ran before this existed and still runs, what assumed the thing
   the slice changed. Write the pairs down, then probe each pair
   together: the old path after the new one has run, the new path on
   what the old one left behind, both at once where they can be. A
   slice's own code tested alone is what every other reviewer already
   did.
5. **Hunt at the judgement edges.** For each behaviour: the second try;
   the wrong, empty or missing input; a dependency that is slow or fails
   after it has already done something; a stored file that is corrupt,
   stale or from before this slice; a person correcting a mistake.
6. **Probe every suspicion by execution.** A small script under the
   probes folder that imports the module or drives the project's own
   test harness, or a request to the app started through the launcher,
   and prints what happens. A suspicion you ran and saw is `confirmed by
   execution`; one you ran and that did not happen is dropped, not
   reported; one you could not run here (a power cut, a real provider's
   behaviour) is `verify`, with the exact step that would confirm it.
   Nothing is reported from reading alone.
7. **Clean up.** Stop anything you started, `scratch_run.py --clean
   '<scratch folder>'`, and leave no process and no clone behind. The
   project's tree is as you found it: you never touched it.

## The report

One file, at the path the task names, in the shared finding format
(`code-review`'s "Finding report format"), so the same parser and the
same fixer read it:

- `## Checks run`: each README command, its exit code and its counts.
- `## Pairs probed`: one line per pair of step 4, new beside old, and
  what the probe printed.
- `## Findings`: one `###` block per bug **confirmed by execution**, most
  severe first, each with its `**Severity:**` (Critical: a person loses
  data or is told something false; High: a thing the app offers does not
  work, or works once; Medium: wrong at an edge with a way round), its
  `**Location:**`, `**Category:** cold: new | cold: older | cold: new
  beside older`, a `**Status:** confirmed by execution` line, and in
  **What's happening** the scenario in two or three sentences, the probe
  by name and the output it printed. `No findings.` when there are none.
- `## To verify`: a plain bulleted list, one line each, of what you
  suspect and could not run, with the step that would confirm it. No
  `###` heading and no severity: nothing here goes to a fixer.

No finding cites a planning document, proposes more than one sentence of
fix, or quotes anything that looks like a person's data from a file the
app stores: describe it ("a member's name", "an amount"). Readability,
naming, structure and test style are the other reviewers': you report
what breaks.

## Hand-back

One line and nothing else: `cold: <n> confirmed (<C>/<H>/<M>), <m> to
verify; <report path>`, or `cold: PASS; <report path>` with none of
either.
