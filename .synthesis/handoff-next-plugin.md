# Handoff: the next plugin, as of 2026-11-21

This file is the whole context a new session needs. Read it in full,
then `next-plugin/design/planning-phase.md`, then the top section of
`TODO.md`. Open a step's folder only when working on that step. The
prompt to start a session is at the end. (The earlier version of this
file, with the two-arm comparison and the first table tests in detail,
is in git history at `3ae86b8`.)

## Standing decisions of the owner

1. **kad is frozen at 0.19.0.** No kad skill, script or eval case
   changes. Everything for the next plugin is under `next-plugin/`.
2. **One step at a time, each validated before the next is built on.**
   A bar is set before a run; a step holds when the owner says so.
3. **Any product, any field.** Nothing is shaped to the finance
   projects it is tested on. No frozen text names a finance or
   provider concept
   (`next-plugin/validation/V1-benchmark-and-judge/wording_check.py`).
4. **The owner is asked only what is theirs** (accepted 2026-11-21):
   the problem and its scope; a rule of the product in their own field;
   a matter of taste, shown as real alternatives; a risk, cost or
   obligation they must accept. Never asked: anything the library, a
   dependency's documentation or a test can answer; good practice in
   user experience, accessibility and security; the solution to an
   identified technical problem; where files go. A preference is never
   asked before the fact it depends on is known. Decisions come once
   per slice as a short ranked list; what the planner chose unasked is
   in one record the owner can overturn.
5. **Every skill and step is tested before it is adopted, the bare
   model first.** A text is carried only for what it adds over the
   task and its inputs alone; the model for a step is chosen by
   measurement, not habit. The plugin evaluation built into the tool
   was expensive on kad: how runs are made and judged is to be talked
   through with the owner when the first step is reached, not assumed.
6. **In a session with the owner, decisions about the plugin itself
   are put one at a time,** each with what is needed to decide it
   (its cost, where one applies) in front of them. This is about how a
   session talks with the owner; inside the plugin, a slice's
   decisions reach the owner as the one ranked list of decision 4,
   after the facts they rest on are known.
7. **The planning personas are kept** (the owner, 2026-11-18: "even in
   a new plugin"). What is weighed stage by stage is each persona's
   skill text and model, not whether planning has personas; the tests
   and the build are where a different approach is wanted.
8. **Privacy.** This repository is public: methods, scripts, prompts
   and results as counts. Anything that quotes a project (code, plan
   text, tables, cold reads, dossiers, answers) goes to the private
   audit repository (`~/.claude/kad-audit/repo`), in a folder named
   after the step.
9. **Sessions run in a VM** set up by the plugin with permission, on
   any OS; locks on by default; a plain-words page for the user.

## What is done, and where

Folders below are under `next-plugin/`.

| Step | Result | Folder |
|---|---|---|
| V0, where a session runs | Docker Sandboxes holds the bar on the Mac (suite, headless and driven browser, mutation pass, push with a one-repository token, sessions, transcripts out, teardown, the host unreachable). **Windows not tried.** | `validation/V0-where-a-session-runs/` (`vm.sh`, `SAFETY.md`, `LOG.md`, `RESULT.md`) |
| V1, the benchmark and its judge | 65 defects from five plans; the matcher agrees with itself (63 and 58 of 65); the owner agreed on 11 of 15 sampled calls against a bar of 13 and said it holds. | `validation/V1-benchmark-and-judge/` |
| E1 | A library of 250 ways software commonly fails, by 21 kinds of action, from 115 public pages, written blind to our defects: full for 30 of 65, part for 25. | `validation/E1-failure-mode-library/` (`library.json`) |
| E2 | Crossing the library with everything a slice does: 1,172 cells, a third "cannot happen", no better than the tables. | `validation/E2-library-grid/` |
| E3 | The owner's picture: triage the library for the slice, a dossier of cited facts per dependency, then answers per thing. | `validation/E3-library-triage/` (the three briefs, `answers.py`) |
| E4 | Matcher second version (`matcher-prompt-v2.md`); on two plans the E3 steps name 17 of 43 defects against the tables' 11, in the same number of cells; the settings a build reads are not in the plan (`settings_inventory.py`). | `validation/E4-rescore-and-second-plan/` |
| E5 | Four independent cold reads of one build: one reader finds about half; a second adds about 6, a third 3 to 4, a fourth 2; 3 or 4 estimated unfound. Three readers supported. | `validation/E5-cold-read-overlap/` |

The plan these led to is `TODO.md`'s V2 to V6 (research before
decisions; the library by triage plus two scripted crossings; answers
in three kinds; tests against the real thing; a three-part review
end), agreed by the owner on 2026-11-21. Every bar in it is still
"proposed".

## The design, and what the owner has yet to decide

`next-plugin/design/planning-phase.md` is the design of the planning
phase: lessons from kad (of 149 recorded questions the owner took the
first option 108 times; only one of 16 planning skills reads a
dependency's documentation), the 13 stages with what is kept from kad,
what reaches the owner, and how each step is tested.

Its section 7 lists four decisions. **The first is made** (what
reaches the owner: standing decision 4 above). **Open, to be put one
at a time:**

1. The numbers for the question measure: how many questions a slice
   may bring, and how often the owner taking the offered option
   unchanged is too often.
2. Whether to start with the research step.
3. Whether the way of testing a step (bare model first, then a short
   brief, then kad's skill; a ladder of models; three runs; held-out
   plans; cost recorded; in the VM) is right, and how the runs are
   made and judged without the built-in evaluation. This one is put
   with the first step's test worked out and its cost beside it, not
   before: the cost is part of what is being decided.
4. Where the plugin lives. `TODO.md` leaves a repository of its own to
   V9 and the work stays in `next-plugin/` until the owner says
   otherwise; it is listed because the design lists it, and it can
   wait.

Nothing of the plugin is built. `TODO.md`'s rule that no plugin code
comes before V7 stands for the build; for the planning phase the owner
brought the design forward on 2026-11-21, and a stage's text becomes
part of the plugin only when its test has been read and the owner says
it holds.

## Open items

- **V0 on Windows**, in a session on that machine with the owner
  present; with it, the hardening of `vm.sh selftest` recorded in V0's
  `RESULT.md`, and the launcher's real design (one command that runs a
  session and then always exports and destroys).
- **The third project's slices 2, 3 and 4 are held out.** Nothing has
  been tuned on them; use them only to confirm.
- **For the next matcher version and the next owner sample:** two
  points recorded under V1 in `TODO.md`.
- **Checking sources by script** (fetch each cited page, find the
  quote) is V2's, for the library and the dossier alike.
- **The stages kept from kad that have no measure yet** (problem,
  scope, requirements, slice, design, screens): each needs one agreed
  with the owner before its text is judged.
- **For the owner:** the `v0-trial` token on the code host can be
  revoked.

## How things are run (so they are not re-derived)

- **A fresh agent per judgment, blind,** given one folder and told to
  read nothing else; three runs where a count matters; never score
  your own method. A bar is recorded in the step's README before the
  run.
- **The judge** is
  `next-plugin/validation/E4-rescore-and-second-plan/matcher-prompt-v2.md`
  (hash beside it), run on Opus for comparability, counted by
  `next-plugin/validation/V1-benchmark-and-judge/agreement.py`. Report
  named, and named or part.
- **The benchmark and every run** are in the audit repository, in
  folders named as here but in lower case: `v1-benchmark-and-judge/`,
  `e1-failure-mode-library/` to `e5-cold-read-overlap/`. Working
  folders on this Mac: `~/kad-eval-*`.
- **A VM:** `sbx` is installed and signed in; a prepared image
  `v0-pft4:1` (Node and a browser) is kept.
  `next-plugin/validation/V0-where-a-session-runs/vm.sh` has the
  verbs, and its `create` switches every lock on first and refuses if
  one is off. A VM made any other way is made only after `vm.sh
  status` shows every lock on. Interactive steps (`sbx login`,
  `/login` inside a VM, `sbx secret set`) are the owner's, in their
  own terminal.
- **A cold read in a VM:** a neutral clone (no remote, no tags);
  `VM_TEMPLATE=v0-pft4:1 vm.sh create NAME DIR` (so the locks are
  checked); create the base branch inside; `claude -p --model opus
  --dangerously-skip-permissions` with `evals/tools/cold_read.md`'s
  brief; then copy out the report and the transcripts (`vm.sh out`).
- **An agent stopped by "Login expired"** may already have written its
  output: look before starting it again.
- **After opening or pushing to a pull request,** the external
  reviewer's comments are triaged without being asked (fix, decline
  with the reason, or defer with a record), and a fix that would make
  measured results stale is weighed against running them again.
- **Reach probes from inside a VM** (can it reach the host, the
  router) need the owner's word each time.

## Prompt for the next session

Paste this to start:

> Read `.synthesis/handoff-next-plugin.md` in full, then
> `next-plugin/design/planning-phase.md`, then the top section of
> `TODO.md`. kad is frozen at 0.19.0: change nothing of it; all work is
> under `next-plugin/`. We are building the next plugin's planning
> phase one step at a time, each step tested before it is adopted, the
> bare model first, and a bar set by me before each run. First, without
> running anything, put to me the decisions still open in the handoff,
> one at a time, in its order, and wait for each answer; when you reach
> the one about how a step is tested, work out the first step's test
> and its cost first and put them with it. Ask me only what is mine to
> decide. Keep anything that quotes my
> projects in the audit repository; this repository is public.
