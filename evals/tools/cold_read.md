# The cold read: a stranger's assessment of a slice, with execution probes

The brief for the cold read the plugin reviews run on a slice once it is
delivered, as an Opus agent against a clone and nothing else. It is the
method the slice 2 review used on 2026-11-08, written down so the next
review (slice 3) and every review after it read the code the same way,
and so the scores compare across runs. The reader has no planning
document, no reviewer report and no git history beyond the diff's file
names: six reviewers with the planning documents accept what the documents
accept; a reader with none who runs the code finds, in an hour, the bugs
that sit at the judgement edges (a deferred decision made permanent, a
provider that times out after creating something, a merchant with no
name).

## How the review session launches it

1. Clone the project at the commit under review into the scratchpad, not
   the owner's working copy: `git clone -q <repo> <scratch>/cold-read &&
   git -C <scratch>/cold-read checkout -q <sha>`. Never the project's own
   directory: the probes write files and the reader must not see a
   planning folder.
2. Launch one agent with `model: opus` (an Opus 5.5 model id), the whole
   of the **Brief** section below as its prompt, and the parameters block
   filled in: the clone's path, the commit, the base branch, the install,
   test, typecheck, lint and format commands from the project's manifest,
   the output path, and the scratchpad path for probes.
3. Save what it returns as `<review dir>/<date>-code-assessment-<project>-
   slice-<n>.md` beside the slice review, and compare its scores with the
   earlier assessments' (same rubric, same scale) in the review's table.
4. Read nothing of it into the review until the plugin's own numbers are
   in: the cold read is the control, and its bug list is compared with
   what the loop's reviewers found and what they accepted.

The agent must never be given the planning directory, the reviewer
reports, the implementation report or the orchestrator log; if the clone
carries them (they are committed), the brief tells the reader not to open
them, and the review notes any `Read` of one in the agent's transcript as
a protocol break.

## Brief

You are reading a repository as a stranger who has been handed the code
and asked one question: can a user rely on this? You have the code, its
tests and its README. You have not seen, and must not open, any planning
document, design document, requirements, user story, slice file,
implementation report, review report, orchestrator log or handoff, in
this clone or anywhere else (they are under `docs/`, `planning/` or a
similar folder: do not read them). Do not read `git log` beyond `git diff
--name-only <base>...HEAD` to learn which files the change touched. What
you find from the code and by running it is the finding; what a document
says is not evidence here.

Parameters:

- Clone: `<path>` at `<sha>`; base branch `<base>` (the diff's files are
  "new code"; everything else is older).
- Commands, from the manifest: install `<cmd>` (frozen lockfile, offline
  if the store allows), test `<cmd>`, coverage `<cmd>` if one exists,
  typecheck `<cmd>`, lint `<cmd>`, format check `<cmd>`, audit `<cmd>`.
- Probes go under `<scratchpad>/probes/`; mutation copies under
  `<scratchpad>/mut/`. Write nothing into the clone's tracked files;
  `git status --porcelain` in the clone must be empty when you finish.
- The app must never be started against real data: no real keychain,
  no real home directory store, no real provider credentials. A probe
  that starts the app does so with a scratch `HOME`, a fake provider and
  a fake secrets tool, the way the project's own tests do (find the
  harness under `test/support/` or the equivalent and use it).
- Output: write the assessment to `<output path>` in the format below and
  return its path and the verdict paragraph.

Method, in this order:

1. **Verify.** Run the install, the test suite, the coverage command if
   there is one, the typecheck, the lint, the format check and the audit.
   Record exact counts and wall time: tests run, passed, failed, skipped;
   coverage per kind and the uncovered lines if few; what the audit
   found and whether it is dev-only. Note the Node or runtime version and
   the package manager version. A command that does not work as the
   README says is a developer-experience finding.
2. **Read the code**, every source file, then every test file. Keep
   notes by file: what it owns, what it depends on, where a reader stops.
3. **Hunt bugs at the judgement edges.** For each behaviour the slice
   adds, ask what happens on the second try, on the wrong input, when the
   provider is slow or fails after a side effect, when a record has no
   name or an empty value, when a file on disk is corrupt or tampered,
   when the user corrects a mistake. Write each suspected bug as:
   file:line; the scenario in two or three sentences; the consequence for
   the user; then **probe it by execution**: a small script under the
   probes folder that imports the module (or drives the test harness) and
   prints what happens. Mark each one **Confirmed by execution** with the
   probe's name and the printed result, or **Verify** with the exact step
   that would confirm it when execution is not possible here (a power
   cut, a provider's real behaviour). Say whether the code is new in this
   change or older.
4. **Judge the tests.** Faked versus real at each boundary; whether a
   wrong rule would be caught (run three or four hand mutations in a
   scratch copy of the clone and report the failure counts); brittle
   assertions (exact prose, CSS, regexes over markup) with file:line;
   duplicated helpers (a fixture or a connect helper rewritten across
   files, with the count); states the tests build that the app cannot
   produce; the test-to-source non-blank line ratio; tests that read
   source text, manifests or script bodies; noise in a green run (stack
   traces, unhandled rejections).
5. **Readability.** Comment lines and whether they say why or restate
   the code (file:line for a few of each); naming consistency with the
   domain; files over 300 lines and functions over 80; the three places a
   reader stops.
6. **Security and reliability notes.** What reaches logs and error
   messages (run a probe that triggers the generic fault path and read
   the log line); origin and host checks; the error paths and their
   status codes; atomic writes and what is not synced; lock behaviour;
   start-up with a bad file.
7. **Developer experience.** Did the README's commands work as written;
   what tripped you; what is hidden (install hooks, exact pins, coverage
   not wired).
8. **Score** each of six areas 1 to 5 with a one-line reason, where 5 is
   production-grade for the app's stated scope and 3 is "works, with a
   real gap": architecture and boundaries; readability and code quality;
   test quality; security; reliability and correctness; fitness and
   developer experience.

Rules:

- Quote nothing that looks like a person's data, a transaction, a
  merchant, an amount or an account from any file the app stores or any
  fixture that looks real; describe it instead ("a merchant name", "a
  fee"). Invented fixture values that are plainly the project's own test
  data may be named.
- Every finding carries a file and line. Every confirmed bug carries the
  probe and its printed output. Weight the bugs: first the one a user
  hits soonest with the worst consequence.
- Do not propose fixes beyond one sentence; this is an assessment.
- Leave the clone's tracked files unchanged and say so at the end, with
  the probes' and the mutation copy's paths.

Format of the assessment (markdown):

```
# Code assessment: <project> at <sha> (slice <n>), <date>

Verified: <the commands and their exact results, one paragraph>.

## Verdict
<one paragraph: a user can / cannot rely on it, and the two or three reasons>

## Scores
| Area | Score | Reason |
(six rows)

## Suspected bugs, in order of weight
1. **<title>.** <file:line>. <scenario>. <consequence>. **Confirmed by execution** (<probe>): <result>. | **Verify**: <step>. <New code | older>.

## Tests
- **Faked vs real.** …
- **Would a wrong rule be caught?** …
- **Brittle assertions.** …
- **Duplicated helpers.** …
- **States the app cannot produce.** …
- **Ratio.** …
- **Source and script text.** …
- **Noise.** …

## Readability
- **Comments.** … **Naming.** … **Long functions and files.** … **Where a reader stops.** …

## Security and reliability notes
…

## Developer experience
…

Probes: <paths>. Mutation copy: <path>. The clone's tracked files are unchanged.
```
