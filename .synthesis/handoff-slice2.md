# Work list after slice 2: kad-dev-team 0.14 (written 2026-11-08)

This file is the whole context a new session needs. Read it first, then
only what an item points at. It replaces what was left of
`.synthesis/handoff-run3.md` (closed 2026-11-08; its open items are
carried here with their numbers). `TODO.md` points here under "After
slice 2".

## Where the list stands (2026-11-10, P5 merged; the list is done)

| Section | State |
|---|---|
| P1 Start | **Merged** as kad 0.14.0, PR #41 (2026-11-08) |
| P2 Screen checks and P3 The loop | **Merged** as kad 0.14.1, PR #42 (2026-11-09, merge `4fc83e4`), one PR as decided |
| P4 Planning data | **Merged** as kad 0.14.2, PR #44 (2026-11-09, merge `2ed1b36`), one PR as decided |
| P5 Audit and measurement | **Merged** as kad 0.14.3, PR #47 (2026-11-10, merge `f748a85`), one PR as decided, with the three small items; Sourcery's three rounds (45 comments: 39 fixed with tests, 6 declined with the reason on the thread; the opengrep audit rule on the mutation runner's one command call accepted in code with its reason, as `eval_gate.py` and `rejudge.py` carry it); gate green on all 42 affected cases after each round |
| Slice 2's fix round | **Done** 2026-11-10 on `personal-finance-tracker-3` (PR #20 round 1, kad 0.14.3): reviewed the same day (audit repository, `2026-11-10-slice-2-round-1-review.md`); the review's fixes merged as kad 0.14.4, PRs #49 and #50 (2026-11-11/12): the mutation runner reads node's spec reporter, the source scan classifies a one-word cell by its column and reads the tab a row names, the Definition of Done reads the README's not-done list against the criteria, a structural size finding at the slice review is the architect's decision, and the anchoring pass (`INCIDENTS.md`, `skill_words_test.py`: no skill names a project) |
| Slice 3 | **Next**, on `personal-finance-tracker-3` (see "After this list") |

`main` is at 0.14.4; every section of this list and the fix round's review are merged. Before the
next real run, update the installed plugin on the machine that runs it
(`claude plugin update kad-dev-team@kad-dev-team-marketplace`, then
restart; the Mac has 0.14.4 since 2026-11-12). What P5 built, for
the session that runs slice 2's fix round and slice 3:

- **The audit sync's transcript rules (P5.1).** `audit_sync.py
  --transcripts` finds each session's transcript by its id (the live file
  Claude Code writes, named in the hook payloads, or the hook's snapshot,
  whichever is larger; subagents' the same way), scans every transcript
  file and the session log with `source_scan.scan_transcript` when the
  target directory has a `sources.md` (or `--sources <file>`), and
  withholds a session with a counted hit: transcripts kept on disk, the
  log still copied unless the hit is in it, `withheld: <session> (<n>
  source values in <m> entries of <k> files)` in the sync log and `;
  withheld: <session…>` on the last line, which the C and E lines record
  as printed and the report to the owner names. A transcript the scan
  cannot read, or a listed source it cannot read, withholds too. A copy
  whose source grew is refreshed; a session is `open` until its SessionEnd;
  `<clone>/.kad-sync.lock` serialises syncs (exit 5 when held, a lock over
  an hour old taken over). `audit_report.py` says where each transcript
  is (kept; on disk, not copied; withheld; none) and flags open sessions.
  Measured on the Mac: 23 s to scan slice 2's 73 MB of transcripts with a
  seven-row catalog. **Not done**: the sync of slice 2 itself (P5.1's
  "done when": the session `4e0e20ec` in the audit repository). The dry
  run shows it would carry that transcript and about 88 new subagent
  files and refresh the loop session's; the project has no `sources.md`
  yet, so nothing is withheld until slice 3 lists the workbook. The
  owner runs it: `KAD_AUDIT_REPO="$(git -C ~/.claude/kad-audit/repo
  remote get-url origin)" python3 -I
  skills/orchestrator/scripts/audit_sync.py --project
  ~/Documents/portfolio/personal-finance-tracker-3 --slice 2
  --transcripts`.
- **The two probes as tools (P5.2).** `evals/tools/cold_read.md` is the
  brief: a clone at the delivered commit in the scratchpad, one Opus agent
  with the brief and its parameters, no planning document or reviewer
  report, the six scores, the bug list probed by execution, the format
  the slice 2 assessment used. `evals/tools/mutation_pass.py check | run`
  takes a JSON list of exact-string mutants (each must match once), runs
  the baseline, applies each, runs the typecheck and the suite, restores
  with `git checkout --`, and writes the table, the kill rates (overall,
  the diff's files, per area), the single-test kills and the survivors;
  the report never prints the replaced text. `audit-review` §3b names
  both; the slice 3 review uses them.
- **The three small items**: `orchestrator_log_check.py`'s order check
  no longer counts the state table's accessibility-line repair row as a
  skipped stage (`orchestrator-log-format/check.sh` counts every error,
  no KNOWN line); `chunk-runner-gate-outside`'s `runner-edits-no-code`
  grader is gone (the judge carries it; the case's bar re-recorded);
  the `delivery-ready` state creates `tools/gh-calls.log` empty.
- **Tests without a model**: `evals/tools/audit_sync_test.py` (8) and
  `evals/tools/mutation_pass_test.py` (3); `evals/README.md`'s first gap
  bullet has the detail.

What a session starting P5 needed from the P4 build (kept for the
record):

- **New pieces P5 touches.** `skills/orchestrator/scripts/source_scan.py`
  is P4.2's scanner (its docstring is the reference): `load(planning,
  project)` gives the catalog for `<planning>/sources.md`, and
  `scan_transcript(catalog, path)` returns the counted hits and the
  number of entries that hold one, with every JSON string decoded first.
  That function is what P5.1's "withheld" rule calls for a transcript
  and for the hook's snapshot; `validation_gate.py --agent` already
  prints its answer for a builder's transcript as `source values <n> in
  <m> entries`. `readiness_check.py` has ten checks, numbered in the
  order they print; the tenth, `no-source-values`, routes to the owner.
  The chunk gate's `sources` check needs `--planning '<target
  directory>'` (the runner's command has it).
- **Three decisions of the build the owner has not seen**, each
  reversible, each measured on the real workbook on the owner's Mac
  (counts only; nothing of it quoted, kept or committed):
  1. *The scan does not count everything it matches.* P4.2 as written
     ("every amount … every text value … the only exclusions are a
     stop-word list") gave about 7,000 hits on slice 2's planning
     **after** the scrub, every one a coincidence: the workbook holds
     tens of thousands of cells, nearly half of all three-digit amounts
     of cents among them, and its labels are a finance app's vocabulary.
     Two rules were added, both printed with every result, both off
     under `--strict`: a value already in the tree at the commit the
     source was listed at is not counted (`Listed at`, a new column of
     `sources.md`); an amount alone is not counted when the sources hold
     1% or more of all amounts of its length, and is counted beside a
     text value of its own row in the same file. With them: the
     pre-scrub planning fails on the merchant and its fee (39 cells),
     and the scrubbed planning raises 48 cells in 44 files, all words
     the workbook shares with the documents.
  2. *A source value goes to the owner first, not to a persona.* Only
     the owner can say whether a word on a line is a row of their sheet
     or the app's own. The orchestrator's A.4 runs the scan with
     `--show` and asks once, three answers; what the owner allows is
     written under `## Allowed by the owner` in `sources.md`; what they
     say is theirs goes back to each document's owner to be rewritten.
     Expect that one question, with some tens of words in it, the first
     time slice 3 lists the workbook; it is not a defect.
  3. *The removal is a script, not a recipe.* `source_scan.py map`,
     `rewrite` and `scan --map` are P4.3's procedure, so no value is
     ever typed into a command; `rewrite` is `git filter-branch` with
     the map as its filter and removes nothing but filter-branch's own
     backup refs.
  The owner confirmed the two rules on 2026-11-09 and asked for the
  partial-cell gap closed (PR #46): a single word of a longer cell (a
  surname from a full name, a brand from a card line) is matched, and
  counted only when it is a word of 1% of the source's rows or fewer and
  something else of its row is in the same file (a whole cell of as few
  rows, or an amount of that row); on the scrubbed planning it adds five
  cells to the 48. Not built, and the owner's to ask for: a dictionary of
  ordinary words as stop-words (the Mac's 235,000-word list would cut
  the 48 to about 4, but it is not on WSL and too large to ship; one
  derived from this repository's own prose cut it to 19).
- **How to list the workbook for slice 3.** The rule's row needs a
  commit under `Listed at` for the first rule above to apply: the skill
  writes `git rev-parse --short HEAD` when it lists a file nothing has
  read. For `personal-finance-tracker-3` the workbook *was* read, in
  slice 2, and scrubbed since; listing it at the current head takes the
  scrubbed tree as clean, which is what the scrub's own checks say it
  is. A dash there counts everything, which is the 48-cell question on
  the whole repository instead of on slice 3's new text.
- **What the first rounds of the new cases found, fixed before the
  gate.** The removal case reproduced slice 2's improvisation three
  runs in three: before any skill was loaded the session printed the
  export with `cat`, wrote its values into a pattern file, ran its own
  `filter-branch`, and once expired the reflog; two reports quoted the
  values. No skill text governs a session that has not loaded it, so
  the fix is in what such a session reads anyway: the `sources.md`
  template now says nothing opens a listed file but `source_scan.py`
  and that a removal is `delivery`'s; `delivery`'s description (always
  in context) names the removal and says a flow reaches it through the
  orchestrator; the orchestrator's E has the paragraph. Three runs in
  three then went through the orchestrator and the scripts. The
  readiness case wrote the values into its log line once in three: the
  skill now gives the line's wording.
- **Tool fixes that came with the re-freezes** (six phase histories,
  since three planning skills changed): `history_stale.py` and
  `freeze-history.sh` read `${CLAUDE_SKILL_DIR}` and a relative working
  directory correctly, and `eval_gate.py` recognises the CLI's current
  name for a run's kept directory (`/private/tmp/e-XXXX`). About 1,900
  such directories from earlier gates are still in `/private/tmp` on
  the Mac; nothing here removed them.
- **Unchanged from the P2+P3 notes, still true:** the gate shares the
  account's usage window (P4's first round of nine new cases was cut by
  the 5-hour limit after two of them; resume with `bash
  evals/tools/gate.sh --base main --stale`); new cases are run with
  `--runs 3 --cases <cases>`, their bars recorded with `python3 -I
  evals/tools/record_thresholds.py --gate-only <cases>` from the
  repository root, then `--stale` once more; `cost_by_role.py` has the
  `runner` and `walk` classes; `delivery` posts everything with the
  footer line `— kad-dev-team` and filters by it. Sourcery skips a diff
  over 300,000 characters (PR #42); the triage rule is §2's first
  bullet.
- **Sourcery's round on PR #44** (the rule stands: fix, decline with the
  reason, defer): 25 comments, all answered, none open. 21 findings:
  eleven fixed in `13bac00` (a value in a path found in history and
  renamed by the rewrite; a listed source git would commit, and a
  byte-for-byte copy of one, problems in a history scan too; files not
  read as text counted; the map private, an extract private, neither
  written through a symlink; UTF-16 exports; transcript keys and
  numbers; an unreadable transcript not reported clean; a rewrite
  refused while earlier `refs/original/` backups exist; delivery
  rescans a head that moved), nine declined with the reason on each
  thread (five of them the design calls above), one deferred, which is
  P5.1 (the audit sync withholding a transcript that holds a value; the
  function it needs, `scan_transcript`, shipped in P4). The other four
  comments were one opengrep audit rule on list-form `subprocess.run`,
  declined, and the owner then ignored that rule for this repository in
  Sourcery's dashboard (2026-11-09), so the check no longer fails on
  `source_scan.py`. `evals/README.md`'s planning-data bullet has the
  detail.
- **Three small defects, fixed in P5's PR (0.14.3):**
  `evals/orchestrator-log-format/check.sh` printed one KNOWN order error
  on entry 9 of its fixture because the checker counted the state table's
  accessibility-line repair row (a hand-back to `product-slicer`) as a
  stage the implementation entry skipped; a row that routes back to a
  stage an earlier row names is now a hand-back, and the check counts
  every error. `chunk-runner-gate-outside`'s `runner-edits-no-code`
  grader (doubled braces, matched nothing, and could not be a trace regex
  since a nested fixer's edits are in the runner's trace) is removed; the
  judge's FAIL clause carries it. The `delivery-ready` loop state creates
  `tools/gh-calls.log` empty, as `delivery-ready-source` did, so a run
  that never calls the stand-in fails that grader instead of voiding the
  run. Nothing of the three remains open.
- **Checked at slice 3, not before:** P1.2 and P1.4 (zero questions at
  A, a browser that answers), P2.1 to P2.4 (the walk's table from a real
  browser, smoke screenshots, no agent reading the owner's data, mockup
  screenshots), P3.1 (the main thread under 150k tokens per call at chunk
  8), P3.2 (the `light` arm: say "light" in the message that starts the
  slice), P3.5 (the counted shell edits on real C lines), and now P4:
  no cell of the workbook in the slice 3 transcripts (the requirements
  stage reads it through `describe`), `sources.md` written by the stage
  the owner points at the sheet, the owner's one question at A.4, and
  every chunk's gate printing a `sources` line.

## 0. Where things are

- **This repository** (`kad-dev-team-plugin`, github.com/diabagatekelly/kad-dev-team-plugin): the plugin. Version `0.14.3` in `.claude-plugin/plugin.json` on `main` (0.13.1 when this list was written); each PR below bumped it (P1 0.14.0, P2+P3 0.14.1, P4 0.14.2, P5 0.14.3; the marketplace entry, left at 0.9.2 since that release, says 0.14.3 too). Skills under `skills/<name>/SKILL.md`; the orchestrator's scripts under `skills/orchestrator/scripts/` (`validation_gate.py`, `rounds_record.py`, `readiness_check.py`, `done_check.py`, `sandbox_check.py`, `audit_sync.py`, since 0.14.1 `scratch_run.py`, and since 0.14.2 `source_scan.py`); the launcher `bin/kad`; the audit hook `hooks/audit.sh`; the eval suite under `evals/` (`evals/README.md` is the playbook; `evals/tools/gate.sh` runs the gate; `evals/tools/cost_by_role.py`, `audit_report.py`, `orchestrator_log_check.py` are the audit tools). The design the loop implements is `.synthesis/implementation-flow-v4.md` (D1 to D14; D9 phase 2 is item P3.1 here); the review-cadence reading is `.synthesis/review-cadence-survey.md`.
- **The project the plugin is measured on**: `personal-finance-tracker-3` (github.com/diabagatekelly/personal-finance-tracker-3, local `~/Documents/portfolio/personal-finance-tracker-3`). Slice 1 merged as PR #2; slice 2 is open as PR #20 on branch `slice-002-give-any-transaction-one-of-my-categories` at `77f4477`, with eleven slice 2 findings and seven open slice 1 issues posted as comments on 2026-11-08. Those are addressed with the updated plugin, after this list, as slice 2's fix round; then slice 3 of the unit (seed the rules from the owner's sheet) is the next real run.
- **The audit material**: github.com/diabagatekelly/audit-docs (local `~/Documents/portfolio/audit-docs`; the plugin's own clone for syncing is `~/.claude/kad-audit/repo`). Slice 2's review is `personal-finance-tracker-3-slice-2/plugin-review/2026-11-08-slice-2-review.md`, with six companion files beside it (the cold code read, the H5.1 transcript audit, the mutation pass, the test measures and their script, the cost table, the log check). Slice 1's is `personal-finance-tracker-3-slice-1/plugin-review/2026-11-01-slice-1-review.md`. The audit directory on the Mac is `~/.claude/kad-audit/` (session logs, kept transcripts, `last-review`).
- **Owner**: Kelly Diabagate, works from a Mac (this list was written there) and from Windows through WSL2; the plugin must stay system-agnostic.

## 1. Where we are

Four real runs of the same problem (a personal finance app on Plaid), each on a later plugin version, each reviewed the same way (planning against the skills' rules, the loop against its rules, an independent cold read of the code on a six-dimension rubric, a cold-read bug list).

| | Run 1 | Run 2 (heavy, v3, 0.6.0) | Run 3 (lite, v4, 0.9.2) | Slice 2 (lite, 0.13.1) |
|---|---|---|---|---|
| Scores: architecture / readability / tests / security / reliability / DX | 4/4/4/4.5/3/3 | 4/3/4/4/3/3 | 4/4/4/4/4/4 | 4/4/4/4/3/4 |
| Loop wall clock | | 12.6 h | 6 h 10 m | 3 h 54 m |
| Cost | | $328 | not measured (transcript lost) | $112, orchestrator thread 44% |
| Findings / regressions by fixers | | 781 | 158 / 25% | 97 / 25% |
| Load-bearing bugs a cold read found afterwards | 2 | 3 | 4 | 5 |

The honest reading (the slice 2 review, "Where the plugin stands"): the plugin now writes clean code reliably and cheaply (lint, formatter, typecheck, CI, a README a stranger follows, atomic encrypted saves, logging that never carries row data; tests proven test-first from the transcripts; 38 of 40 mutants killed), and it does not yet ship a slice a user could rely on without a cold read and a browser pass first. Four runs running, one or two load-bearing bugs ship per slice. They sit at judgement edges, not in sloppy code: a decision the slice file deferred ("changing a merchant's general rule", which the code made a permanent misclick trap), a provider that times out after creating something, a merchant with no name, a corrupted file. Six reviewers with the planning documents accept what the documents accept; a reader with no documents who runs the code finds them in an hour. Nothing has looked at the built screen in a real browser by default, and twice the first real look found what every simulated pass missed. The fixer causes a quarter of the findings in every run since run 2.

Two incidents in slice 2 that no earlier run had, both in the review's planning and loop sections: the owner's real budget workbook entered the planning documents and thirteen test files (requirements wrote a real merchant and fee as the example; the slice made it the running example; security-requirements wrote "nothing from the workbook in the repo" five minutes after that was already false; found at D; two history rewrites, the second because the scrub's own record named the removed values); and the slice ran with no browser because the A line said "no Chrome" and the flow is allowed to go on.

This list's aim, in one sentence: make the flow catch what the cold reads catch (a cold read with execution probes and the acceptance criteria walked in a real browser at every D), stop the fixer being a stranger, and make starting a session one word.

## 2. How work on this repository is done

- One PR per section (P2 and P3 are one PR, since both rewrite the orchestrator's C and D and the smoke run), from a branch named after the section, version bumped in `.claude-plugin/plugin.json`, PR body ending with the attribution line the session carries. Sourcery reviews every PR on this repository; its comments are triaged (fix, decline with the reason on the thread, defer), as PRs 36 to 39 show.
- **Every skill change gets an eval case or a grader**, and the gate must be green on every case the diff reaches before the PR merges. `bash evals/tools/gate.sh` (on the Mac: Homebrew's Node 24 first on PATH and the git shims under `$(brew --prefix)/sbin`, which `gate.sh` checks and explains; from Windows `wsl-gate.sh`). `evals/tools/affected_cases.py` picks the cases; the pre-push hook (`git config core.hooksPath .githooks`) runs `eval_evidence.py` and refuses a push whose touched cases have no recorded evidence. **No skill file may change while a gate runs** (the fingerprint voids the evidence). Read every failure before re-recording a bar (`record_thresholds.py`); `evals/README.md` "Playbook" and "Eval gate" have the detail.
- **Every orchestrator text change pulls the orchestrator cases into the gate.** 28 of them are owed since 0.13.1 (H1.6's evidence debt, accepted by the owner on 2026-11-07). Decided 2026-11-08: they are not run on their own; they run with the first PR that touches `skills/orchestrator/SKILL.md` (P1), knowing a regression found then cannot be pinned on 0.13.1 or on the new text. P1 and the combined P2+P3 PR both touch the orchestrator: land them back to back.
- Commits pushed from the Mac need the noreply author address (`41132296+diabagatekelly@users.noreply.github.com`, set as local `user.email` in this repo and in the audit-docs clone); GitHub refuses the yahoo address.
- **Never commit a real transcript, real project content or any value from the owner's workbook.** Eval cases rebuild a situation on `evals/fixtures/library-app/` (or an overlay beside the existing `*-plants/`). The kept transcripts under `~/.claude/kad-audit/transcripts/` and the audit repository's early slice 2 commits contain the workbook dump; read them for audit purposes only and quote nothing from them.
- Real runs are started with `bin/kad` (the sandbox runtime `srt`, audit mode, the audit repository clone, the GitHub token, Chrome under `--chrome` today), never with plain `claude`: a plain session cannot fence the agents, and a shell opened from inside a session carries `CLAUDE_CODE_CHILD_SESSION`, which turns transcript saving off.
- The owner decides scope, requirements and anything in `.synthesis/implementation-flow-v4.md` §13; the plugin recommends and records.

## 3. Decisions taken on 2026-11-08

- H1.6's 28 cases: with P1's gate, not alone (above).
- H5 (the lite policy's tests): answered by the slice 2 review; lite stays the only implementation skill; the two follow-up sentences are P3.8. No rule from the retired heavy policy comes back.
- H4 (slice 1 bugs): #6 to #10 and #13 fixed by PR #2 round 2 (`165ba16`, `425fd26`, merged 2026-11-07); #11, #12, #14 to #18 open, posted on PR #20, fixed with slice 2's fix round after this list.
- D9 phase 2 (the chunk runner): build it (P3.1). Measured: about 427k cache-read tokens per call over 396 calls, $49.74 of $111.96, for one slice in one thread.
- H6's fourth question (review cadence): one measured arm on slice 3 that also changes who fixes (P3.2).
- Screen checks: the acceptance criteria walked in a real browser by an agent, every UI slice, screen-reader announcements the only manual item (P2).
- TODO 4.3 (run 2 leftovers in `personal-finance-tracker-2`): won't do.
- Order of the PRs: P1; then P2 and P3 as one PR; then P4; then P5. (2026-11-10: all five are merged.)

## P1. Start: one word, no questions, Chrome on

**Done 2026-11-08 as kad 0.14.0, branch `p1-start`** (the gate run and its PR are in the branch's commits; P1.2's and P1.4's "Done when" lines that name slice 3 are checked at slice 3).

**Why.** The owner's words: "The whole process of having to manually restart is very clunky and confusing. Also it should just run with chrome all the time. I don't want to know anything about how to set up a sandbox and what permissions to give. I just want to start the orchestrator, and if it needs to open a new shell itself in the same VS Code and assign the default permissions we agree we need, or at least present them to the user to agree to, then just launch." What happens today: `/kad-dev-team:orchestrator` typed in a plain session cannot fence itself, so the A step asks to restart; `kad --relaunch` opens a Terminal.app window through AppleScript (that window is what planted `CLAUDE_CODE_CHILD_SESSION` and lost run 3's and the 2026-11-07 session's transcripts); Chrome needs a one-time enable outside the fence and `--chrome` on every run, and slice 2 ran without it; the sandbox check fails every `kad` session on a folder the launcher itself added (the owner clicked "opt to continue" at A in both sessions since 0.10.0); the consult cap and the shell-edit stall rule produced owner questions nobody wanted; the launcher's saved answers vanished once (first-run questions asked again on 2026-11-08, cause unknown). The fence must exist before Claude Code starts, so the launcher is the entry point and the session never restarts.

Files: `bin/kad`, `skills/orchestrator/SKILL.md` (step 0 and A.1, A.2, the budget line, C.1's stall rule), `skills/orchestrator/scripts/sandbox_check.py`, `README.md`, the launcher section of `evals/README.md`; eval: the routing cases' A step (`orchestrator-readiness-gate` and the other A-line graders) re-frozen for the new question count.

- [x] P1.1 **`kad` is the way in; nothing restarts.** `--relaunch` and the AppleScript go. An orchestrator that finds itself unfenced (the `platform` line without "under the sandbox runtime") prints the one line to type (`kad` from the project root, or the plugin's `bin/kad --project <dir>`) and stops: no question, no handoff file, no new window. The README's first section is that one line. Done when: no code path opens a terminal window; the A step has no restart branch; a plain session's `/orchestrator` ends in one line.
- [x] P1.2 **Chrome on by default.** `kad` enables the extension's native-messaging file itself when it is missing (it runs outside the fence; today the README says "run `claude --chrome` once"); `--no-chrome` opts out; `KAD_CHROME=1` always otherwise. The browser check at A runs only when the slice touches UI: there, a browser that does not answer `list_connected_browsers` is an error with the fix on the line (Chrome not open, extension not installed, `--no-chrome` given), and the one question is restart with Chrome or continue with every screen check owed; on a slice with no screen the field says `browser not needed` and `--no-chrome` costs nothing. Done when: a fresh checkout's first `kad` reaches a browser that answers; a UI slice under `--no-chrome` gets the question; a non-UI slice under it starts without one.
- [x] P1.3 **One screen, once.** The first `kad` on a project prints the permission set in plain words (the project and the audit folder writable; the owner's keys and credential files unreadable; network to the API, sign-in, GitHub, the npm registry and Chrome's bridge; the GitHub token the one credential kept; local ports) and asks one yes, stored with the three existing answers (audit mode, audit repository, extra domains) in `~/.config/kad-dev-team/launcher.json`, per project. Later runs print one line and start. `kad --reset` shows the screen again. Done when: a second run asks nothing; the stored file lists the project.
- [x] P1.4 **The A step asks nothing the launcher guarantees.** Under `kad` (`KAD_SRT_SETTINGS` set): no settings, sandbox or transcript question; the sandbox check still runs and is logged. Delegation is asked once per project and stored (`planning/delegation.md` without a slice number, read by every later slice's A step; the per-slice file stays as the record of the owner's words). Done when: slice 3's A step asks zero questions and its A line is complete.
- [x] P1.5 **The sandbox check's `write` false FAIL.** `sandbox_check.py` treats the launcher's own folders (`KAD_GH_DIR`, `KAD_AUDIT_DIR`, the srt settings directory, the plugin's hook data directory) as allowed writes, named on the line as the launcher's. Done when: a `kad` session's A line says `PASS` without an owner choice; the scratch harness that reproduces the FAIL passes.
- [x] P1.6 **Why `launcher.json` vanished.** Between 2026-11-07 and 2026-11-08 the file disappeared and the first-run questions came back; the folder's `srt/` was rewritten at the same minute (11:38). Read `bin/kad`'s `--reset`, `--prepare` and first-run paths and the orchestrator's `kad --prepare` call for a path that deletes or fails to rewrite it; make the write atomic and never a delete. Done when: the cause is named here and a test of the launcher (a bash test under `evals/` or `bin/`) covers it. **Cause (found 2026-11-08):** `--reset` was the only code path that removed the file, and it removed it first (`rm -f "$conf"` before the three questions, the new file written only after the last answer). The owner ran `kad --reset` from the Terminal between the 0.13.0 fix session of 2026-11-07 and the 0.13.1 session of 2026-11-08 (the shell history holds `bash .../0.13.0/bin/kad --reset --project .../personal-finance-tracker-3 -- '/kad-dev-team:orchestrator'`; the owner's PR #20 comment says the session was started "after `kad --reset` (the stored audit repository is this project's own origin)"), and that run did not reach its write: an interrupted question (Ctrl-C, a closed window) or a failed write between the delete and the rewrite leaves no file, and the next run asks everything again, which is what the 0.13.1 session's Terminal window did at 11:38. The `srt/` folder's matching time is only that run regenerating the settings. Fixed in 0.14.0: nothing in `bin/kad` deletes the file; `--reset` shows the set and rewrites the file whole through a temporary name only on approval, a declined or interrupted run leaves it byte for byte (`evals/tools/kad_test.sh`, the `reset, no terminal: file untouched` and `source: no rm of the stored file` checks).
- [x] P1.7 **No caps that ask the owner.** The consult cap (`8 consults`) leaves the A line and the budget line; consults used go on the E line. The shell-edit stall rule (three in one chunk or fix is a stall, an owner question before the relaunch) becomes a counted deviation: `shell edits <n>` stays on the C line, never a stall, never a question; formatter runs through the manifest's `format` script are not shell edits; the count comes from the transcript (P3.5). The budget line keeps the hours and the review and fix counts. Done when: slice 3's loop asks the owner nothing about edits or consults; the C line still carries the count.

## P2. Screen checks: the acceptance criteria walked in a real browser

**Done 2026-11-08 as kad 0.14.1, branch `p2-p3-loop`, one PR with P3, merged as PR #42 on 2026-11-09** (the "Done when" lines that name slice 3 are checked at slice 3).

**Why.** The owner's words: "Screen checks should happen for sure. In fact if the AC is a checklist, an agent should open the browser and check all AC points pass manual testing (maybe excluding screen reader)." Slice 2: eight smoke runs in happy-dom said the UI chunks worked; the owner's own real-browser review the next day found confirmations and failures drawn 2,000 px above the viewport (a failed save looked like a dropdown quietly reverting), three decisions, two fixes and a review round. Run 3: the same, with the Plaid connect only ever done by hand. Two smoke agents in slice 2 started the app on the owner's real ledger and Keychain (nothing changed; checksums compared), because the smoke-run text has no data rule. The owner's browser review (`personal-finance-tracker-3/planning/implementation/slice002-browser-review.md`, its "Isolation" section) is the template for doing it safely.

Files: `skills/accessibility-review/SKILL.md` (the smoke run and slice review modes, a new "AC walk" section), `skills/orchestrator/SKILL.md` (C.3 and D.3: the launches and what they are handed), `agents/accessibility-engineer.md`, `skills/screen-design/SKILL.md`, `skills/orchestrator/scripts/rounds_record.py` (a per-criterion table into the sidecar); eval: a UI case on the library-app fixture with a running page and a criteria list, graded on the per-criterion table and on the data rule (the agent's `HOME` and paths).

- [x] P2.1 (`accessibility-review`'s "Criteria walk" mode, launched at D.3 as a seventh launch on a UI slice; `rounds_record.py` reads the `## Criteria walked` table into the sidecar and prints `walk <pass>/<fail>/<not reachable>`; NOT REACHABLE rows go to the owner's checklist issue through `delivery`; eval `accessibility-review-ac-walk`) **The AC walk at D.** For every UI-touching slice, one agent at D opens the built app in the real browser (the Chrome tools under `kad`), takes the slice's criteria as a checklist (the Given/When/Then list from the slice file, the A criteria, and the R and S criteria a browser can reach), drives each one and writes a table: criterion, PASS / FAIL / NOT REACHABLE, how it was driven, a screenshot per state. A FAIL is a finding in the shared report format and goes to D's fix round like any other; NOT REACHABLE names why (a native menu the tool cannot operate, a provider connection not made). Screen-reader announcements are the owner's manual checks, listed as such, and nothing else is. Done when: slice 3's D has the table from a real browser, and an owner's-checklist issue like #25 is not needed.
- [x] P2.2 (the smoke run's text: the real browser with the Chrome tools, never a DOM library, a screenshot per state under `<records>/smoke/`; the owed finding only for a browser that stops answering, or when the owner chose to continue without one at A) **The chunk smoke run in the real browser.** The per-chunk smoke agent drives the chunk's Done-when in Chrome, not happy-dom, with a screenshot; the owed finding ("browser checks not run") is only for a browser that stops answering mid-flow, since P1.2 makes no browser an error at A. Done when: slice 3's smoke reports carry screenshots and no owed rows.
- [x] P2.3 (`skills/orchestrator/scripts/scratch_run.py`, tested by `evals/tools/scratch_run_test.py`: `HOME` and every `--env` data path inside a scratch folder outside the project, a path resolving outside refused with exit 3, `--hash` for the orchestrator's before-and-after digest of the owner's data directory, `data unchanged|CHANGED|not named` on the C and D lines; the rule in the orchestrator, `accessibility-review`, the two smoke agents' texts) **Data rule for every agent that starts the app** (smoke, AC walk, slice accessibility review, the stranger test). The app is started through the project's test entry point with every data path given explicitly inside a scratch folder (`HOME` pointed there as well, for anything that resolves from it), by a launcher script that refuses to start when any resolved path is outside that folder; a made-up ledger (the fixture's or one the agent builds); the fixture's fake `security` tool or a disposable Keychain, never the owner's login Keychain, not even for reading; no Plaid connection started; the scratch folder deleted after. The agent never opens the owner's data directory, so the before-and-after hashes of the real data files are the orchestrator's step around the launch, not the agent's, and go on the C or D line. Done when: the transcript audit of slice 3 finds no app-starting agent reading the owner's data directory or the login Keychain, and the launcher script's refusal is tested.
- [x] P2.4 (`screen-design`: each mockup opened in the browser at the default width, at 360 px and with a long list, screenshots beside the mockup; `accessibility-review`'s design-time pass measures the rendered page and keeps `<mockup>-a11y.png`) **Mockups seen, not only written.** `screen-design` renders each mockup in the browser (a long list, the narrow width) and keeps a screenshot beside it; `accessibility-review`'s design-time pass measures the rendered page. Slice 2's mockups were never rendered (no browser, `open` refused) and the layout problem a long table causes was invisible. Done when: slice 3's mockups have screenshots in `visual-ux/`.

## P3. The loop

**Done 2026-11-08 as kad 0.14.1 with P2, merged as PR #42 on 2026-11-09** (P3.2's arm and the slice-3 "Done when" lines are measured at slice 3).

Files: `skills/orchestrator/SKILL.md` (the state table and step 1's inspection for P3.10; B, C, D, the log format, the chunk-loop entry), a new `agents/chunk-runner.md` or an orchestrator-side section, `skills/tdd-implementation-lite/SKILL.md`, `skills/vertical-slicing/SKILL.md` and `readiness_check.py` (P3.3), `validation_gate.py` (P3.5, P3.6), `evals/tools/cost_by_role.py` (P3.7), `evals/tools/orchestrator_log_check.py` (P3.4), `skills/map-update/` and `skills/test-quality-review/SKILL.md` (P3.8); eval: the loop cases (`orchestrator-chunk-review-round`, `orchestrator-one-fix-round`, `orchestrator-gate-deviation`, `orchestrator-readiness-gate`) re-frozen; a new case for P3.3; `tdd-implementation-lite-rename-fix` extended for the commit rule.

- [x] P3.1 (`agents/chunk-runner/AGENT.md` and `skills/chunk-runner/SKILL.md`: the orchestrator's old C.1 to C.4 as the runner's procedure, one line back; the orchestrator keeps the records commit, the sync, the C line, C.5 and the budget; `cost_by_role.py` has the `runner` class; the five mid-chunk `orchestrator-*` cases became `chunk-runner-*` cases and `orchestrator-chunk-runner-launch` and `-handback` grade the orchestrator's side; the nested `Agent` launch a runner needs was probed and works) **D9 phase 2, the chunk runner.** One agent per chunk (`chunk-runner`, Opus, launched by the orchestrator at C) runs the chunk's whole round: launch the builder, run the gate, launch the reviewer and the smoke agent, record the rounds in the sidecar, launch the fixer and the regressions re-review, and hand back the C line and nothing else. The orchestrator keeps A, B, the records commits and the sync after each C line, D and E, and the owner's questions (a chunk runner never asks the owner; a needs-decision or a second gate FAIL comes back on the hand-back line). The chunk runner's transcript is kept and audited like a builder's (`cost_by_role.py` gets the class). Why: the orchestrator's thread averaged about 427k cache-read tokens per call in slice 2 and was 44% of the cost; the v4 design (D9) said to build this above about 250k. Done when: slice 3's main thread is under 150k tokens per call at chunk 8 and the audit attributes every launch; the eval loop cases pass with the runner in between.
- [x] P3.2 (built, not yet measured: `cadence — loop | light` on the A line from the owner's message, the light procedure in the orchestrator's C.4 and D.3 and the runner's text (build, gate, smoke only; D's fixes to each chunk's own builder by `SendMessage`, one Opus fixer for what it cannot clear, `fixes builders <n> opus <m>` on the D line); the slice 3 review decides the keep list) **Review cadence and who fixes: one measured arm on slice 3 (H6's fourth question).** The owner's hypothesis: fewer mid-build reviews may also fix "the fixers that do more harm than good". The review's reading: two problems. The fixer problem is 20 of 81 actionable findings being regressions (25%, every run since run 2): the fixer is a fresh Sonnet agent with no memory of the chunk, editing code it did not write, 25 times a slice. The judgement-edge bugs are what a cold read with probes finds after six reviewers (one or two per slice, four runs running): reviewers who read the criteria accept what the criteria accept. The arm changes three things, each aimed at one of them, and the audit measures each on its own: (a) per chunk, gate and smoke run only, no reviewer and no fix round; (b) at D, the cold review with execution probes (as the audit's cold reads are briefed: all of `src/` and `test/`, no planning document, the suite run, every suspected bug probed by a scratch script, "confirmed by execution" or "verify") plus the AC walk (P2.1), once, then the criteria pass under its own heading; (c) fixes by the chunk's own builder, resumed with its context (`SendMessage` to the agent that built the chunk), not a fresh fixer, with one Opus fixer for what the builder cannot clear, and the regressions-only re-review as today. Lows stay at D. Measured against slice 2: regressions per actionable finding (which speaks to (c)), bugs the post-hoc cold read still finds (to (b)), cost and wall clock (to (a)), and the owner's hours. One slice changing three things is descriptive evidence, not a controlled comparison: each measure maps mainly to one change, the review says so when it attributes, and a change the measures cannot separate stays for a second slice rather than being credited. Build: a `cadence` field on the A line (`loop` | `light`), the light procedure as its own subsection of C and D, and the chunk runner (P3.1) carrying either. Done when: slice 3 ran under `light`, its review states which of (a), (b) and (c) to keep, and the orchestrator's default is set from that.
- [x] P3.3 (`readiness_check.py`'s ninth check `open-items-triaged`: every item under Still open / Explicitly deferred ends with `Usable without it: <how>` or `Blocker: <why>`; untriaged routes to `product-slicer:vertical-slicing`, a blocker to the owner as one three-answer question; `vertical-slicing` writes the sentences; the four criteria reviewers restate each accepted deferral as a finding at D; eval `orchestrator-readiness-open-item`; the fixture slices' deferred items carry the sentence) **A deferred decision the slice depends on blocks delivery.** `vertical-slicing` keeps writing "Still open" items; at readiness each is triaged: "the slice is usable without it" with the sentence that says how, or a blocker that goes to the owner before any build. The review skills' criteria pass restates an accepted deferral as a finding ("the slice ships with X undecided; consequence Y") rather than dropping it. Why: slice 2's "changing a merchant's general rule" was deferred to requirements, six reviewers accepted it, and the cold read found that the first pick for a merchant is permanent and a misclick has no undo (PR #20, bug 1). Done when: `readiness_check.py` has the triage check and the route; an eval case on the fixture plants a load-bearing open item and expects the block.
- [x] P3.4 (the orchestrator opens a new chunk-loop entry after the last route; `orchestrator_log_check.py` attaches step lines appended under a later entry to the latest chunk-loop entry with a WARN: slice 2's log replays with its 60 loop errors gone, 21 errors left, all planning-stage; `orchestrator-log-format/check.sh` checks both forms) **The log after readiness routes.** After the gate's last backward route the orchestrator writes a new chunk-loop entry ("slice ready for implementation, readiness PASS after …") and the A line under it, as run 3 did at entry 34; slice 2 appended A to E under the second backward route (entry 60) and the checker read all 60 loop calls as unlogged. `orchestrator_log_check.py` attaches A to E lines to the latest chunk-loop entry either way. Done when: slice 2's log, replayed, produces no "stage that ran unlogged" error.
- [x] P3.5 (`validation_gate.py --agent-transcript <path> | --agent <id>`: shell edits counted per file per command from heredocs, redirections, `sed -i`, `python3 -`/`-c` and `node -e` scripts that open a path for writing, `cp`/`mv`/`rm`, the catch-all over the range, formatter runs excluded; `shell edits <n> (reported <m>)`; `committed on a red run: <sha>` from the chained command's recorded output. Replayed on slice 2's two transcripts: chunk 2's builder gives 11 against its reported 1 (the audit's 9 plus the restored `sed -i` break and the heredoc that appended the report section, both of which the rule counts); chunk 4's gives the red-run commit `91df0bb` (fail 1). `tdd-implementation-lite`: the stall sentence replaced by the deviation-on-the-record text, the suite as its own command read before `git commit`; `tdd-implementation-lite-rename-fix` commits under the loop and grades the commit not chained) **Shell edits counted, and the commit as its own command.** `validation_gate.py --agent-transcript <path>` counts Bash commands that wrote under the tree (`>`, `>>`, `tee`, `sed -i`, `perl -i`, `python3 -`/`python3 -c`/`node -e` with a write, `cp`, `mv`, `rm` on a tracked file), and as the catch-all any tracked file that changed between the agent's start and its hand-back without an `Edit` or `Write` call naming it and prints `shell edits <n> (reported <m>)`; the C line takes the counted number; formatter runs through the manifest's `format` script do not count. `tdd-implementation-lite`: the suite runs as its own command and its result is read before `git commit`; never `test | grep && commit`. Also, from P1.7: `tdd-implementation-lite`'s shell-edit paragraph still says "three in one chunk or fix end your turn as a stall"; the orchestrator no longer stalls or asks (0.14.0), so that sentence becomes "a deviation on the record, audited against the transcript; a formatter run through the manifest's `format` script is not a shell edit" with this item, which runs the lite cases anyway (left out of P1's PR to keep its gate to the orchestrator cases). Why: chunk 2's builder reported 1 shell edit and made 9 (the whole chunk through heredocs and Python); chunk 4's builder committed on a red run through a grep-and-commit chain and reported green. Done when: the two transcripts, replayed through the gate, give 9 and a red-run commit; the lite eval case plants a chained commit.
- [x] P3.6 (`test_key`: NFC, case folded, whitespace folded, a `seam "…"` wrapper stripped on either side; a backticked single word is never a name; slice 2's chunk 1 at `f3ed2cb` and chunk 3 at `363fbff` replay with 0 missing names) **Gate name matching.** The Done-when extractor reads quoted test titles only, strips the `seam "…"` wrapper, compares case-insensitively after NFC normalisation, and never takes a backticked single word as a test name. Why: three false FAILs in slice 2 (a backticked `POST`, the `seam` wrapper, a merchant name's case), two fixers and an owner ruling. Done when: slice 2's three gate outputs replay as PASS.
- [x] P3.7 (verb-first rules, then the review names, then `agentType`; slice 2's table now shows 17 `reviewer:chunk` and 21 `fixer`) **`cost_by_role.py` role classes.** Classify by the launch description's verb (Build, Plan, Fix, Review, Re-review, Smoke, the six review names, Decide, Stranger) and by `agentType`; "fix" counts only at the start. Why: slice 2's table counted the eleven re-reviews as fixers and the eight chunk reviews as "other". Done when: slice 2's table shows 17 chunk reviewers and 21 fixers.
- [x] P3.8 (lite: the commit as its own command, grep the support folder before a helper, the page's strings from one module; `extract_map.py` lists `test/support/`-style folders under the `test-support` tier and `map-query` answers helper questions from it; `test-quality-review/scripts/test_measures.py` prints the duplicated-helper count and the brittle-assertion share with a 0.30 bar, Medium above it: slice 2's suite measures 17 duplicated helpers) **H5.4's follow-up: lite's two sentences, the helpers, the brittle measure.** `tdd-implementation-lite`: the suite as its own command before the commit (with P3.5); grep `test/support` before writing a helper. `map-update` indexes `test/support` exports as their own tier so an implementation-level `map-query` can answer "is there a helper" (slice 2's builders consulted it every chunk and still redefined `choose`, `ledgerContents`, `openPage`; a `chime` fixture is in 17 files). `test-quality-review`'s D measures gain the duplicated-helper count and the brittle-assertion share (regex or equality on markup, CSS or prose, per test), Medium above a bar set from runs 3 and slice 2 (0.61 and 0.57 per test; run 2's heavy suite was 0.11). The page's user-facing strings exported from one module so tests assert on the constant. Done when: the measures print at D, the map has the tier, the lite text is in, and the handoff-run3 H5 items are ticked by reference to the review.
- [x] P3.9 (the runner's gate step: `flaky: <test>` on the hand-back and the C line, one re-run on the first sighting, one fixer at the cause on the second, counted as the gate fixer) **Flaky test rule.** A gate FAIL on a test that passed on the same range before is reported as `flaky: <test>` on the C line; two sightings send one fixer to the cause, counted as the gate fixer. Why: slice 2's intermittent failure took four sightings (chunks 2 to 4) before the orchestrator improvised exactly that. Done when: the C line has the field and the fixer launch is in the text.

- [x] P3.10 (the orchestrator's step 1b with `gh pr list` and `gh issue list` before any planning read, a failed `gh` stopping the routing; `delivery` marks everything it posts with `— kad-dev-team` and filters by it, labels issues `severity:<level>`, folds the walk's NOT REACHABLE and owed rows into one owner's-checklist issue, and is callable from the routing; `external-review-triage` judges any author's comment; eval `orchestrator-route-open-pr` on a stand-in `gh`) **Open work first: pull requests and blocking issues in the routing.** The orchestrator's detected-state step reads the planning documents to find where the problem stands; before that it now asks the tracker two things, with `gh`, and routes on the answers. (1) **An open pull request from a slice branch** (`gh pr list --state open --limit 500`, head matching `slice-<nnn>-*`): the slice is not closed, so nothing newer starts. Route to the chunk loop's E.4 (`code-reviewer:external-review-triage` over every unresolved review thread and issue comment, whoever wrote it: an external reviewer, a bot, the owner, and the owner writing from the same GitHub account the session pushes as; the only comments skipped are the ones this flow posted itself, recognised by the plugin's footer line in their body, so the collector in `delivery` filters by that marker and never by author; then `release-engineer:delivery` to push the fixes, reply to the declines, file the deferrals) under the loop's fix-round rules (one fixer plus one regressions round per round of comments, the gate before each), and report when the PR is clean; merging stays the owner's. A PR whose comments are all resolved and whose checks are green is reported as "ready to merge" with one line, and the flow waits for the merge before any slice work. (2) **Open issues at Critical or High** (`gh issue list --state open --limit 500`; `delivery` files every issue with a `severity:<level>` label in addition to the title prefix, and the routing reads the label first, the title prefix second, and the report's `**Severity:**` line quoted in the body third, so issues filed before this change are still found): each is put to the owner as one question with three answers, fix it in the open slice's fix round, fix it first on its own branch, or accept it as known and recorded; a Critical is never "accept". A `gh` call that fails (not installed, not signed in, no network) stops the routing with the error on the line; the flow never proceeds as if nothing were open. Only then does the planning-document inspection run. Both checks are entries in the log like any route. Why: PR #20 sits open with eighteen findings as comments, and slice 3 would otherwise be cut on a branch behind it; #14 (High, a bank that asks to log in again can never recover) has been open since 2026-11-02 and no stage ever routed it. Files: `skills/orchestrator/SKILL.md` (the state table's first rows and step 1's inspection), `skills/external-review-triage/SKILL.md` (comments by any author, not only an external reviewer's), `skills/delivery/SKILL.md` (E.4 callable from the routing, not only from the loop's own E); eval: a routing case on the fixture with a fake `gh` on PATH answering one open PR with two unresolved comments and one High issue, graded on the route order and the one question. Done when: slice 2's state on 2026-11-08 (PR #20 open with comments, #14 open) routes to the triage first and asks about #14; a project with nothing open routes as today.

## P4. Planning data: nothing of the owner's by value

**Why.** At 20:11Z on 2026-11-07 the owner pointed requirements-refinement at a budget workbook; the orchestrator dumped every tab into the scratchpad (so the whole sheet is in the session transcript), wrote a real merchant and its fee into `requirements-002.md` as the example, and `slice-002.md` made that pair the running example of six acceptance criteria; the design, the story, the chunk plan's Done-when names and thirteen test files carried it (118 occurrences). `security-requirements` wrote S26 ("nothing from the workbook in the repository") five minutes after the slice file already broke it. The readiness gate has no such check. The D security reviewer found it 2.5 hours later. The scrub was a 42-commit `filter-branch` before the first push; its own log bullet named the removed values, which were then pushed and put in the PR body; a second rewrite and force-push with lease followed the next day. The only rule anywhere is the lite skill's "made-up data throughout", which binds the builder, who inherited the names from the plan.

Files: `skills/requirements-refinement/SKILL.md`, `skills/vertical-slicing/SKILL.md`, `skills/acceptance-criteria/SKILL.md`, `skills/screen-design/SKILL.md`, `skills/architecture-design/SKILL.md`, `skills/security-requirements/SKILL.md`, `skills/orchestrator/scripts/readiness_check.py` and `validation_gate.py`, `skills/delivery/SKILL.md`, `skills/security-review/SKILL.md`; eval: a fixture overlay with a provided "sheet" (a CSV of invented rows) and a slice whose criteria must quote none of it; a case for the pre-push grep.

- [x] P4.1 (built, 0.14.2: the rule is one block, "A file the owner provides is described, never quoted", in the same words in `requirements-refinement`, `vertical-slicing`, `acceptance-criteria`, `screen-design` and `architecture-design`, which `evals/tools/source_scan_test.py` compares; `source_scan.py describe` is how a stage reads a file's shape without a cell; `sources.md` gained a `Listed at` column and an "Allowed by the owner" section; four cases, one per planning stage, each with a trace regex that one full read of the sheet fails) **Examples are invented at the point of writing.** A file the owner provides (a sheet, an export, a screenshot) is read where it is, only the tab or range the owner names, into a scratch file the session never prints (the transcript carries the column names and the row count, never a cell), its location, tab and date recorded in `planning/sources.md` (a path outside the repository, no values), and every example in the document written with invented names and amounts and said to be so. Done when: the overlay case's criteria quote nothing from the sheet; the five skills carry the rule in the same words.
- [x] P4.2 (built, 0.14.2, with the two counting rules of "Where the list stands": `source_scan.py`, the readiness gate's tenth check `no-source-values`, the chunk gate's `sources` check and its transcript line, `security-requirements`' scan at the moment the criterion is written; the workbook is read with the standard library, since `openpyxl` is not visible under `python3 -I`; the done-when's three checks hold: slice 2's pre-scrub planning fails, the fixture's passes, the invented sheet's `fee` column is caught in decimal and in cents) **A "nothing from the source" criterion checks the documents it is written into.** `security-requirements`, when it writes an S26-kind criterion, greps the planning directory for the source's distinctive values then and there; a hit is a backward route to the document's owner. `readiness_check.py` and `validation_gate.py` read `planning/sources.md` (so the check does not depend on an A line naming anything) and, for each source, its text and numeric cells (openpyxl or csv, `python3 -I`): every amount is matched in cents and in its formatted forms, every text value is matched as a whole word whatever its length, and the only exclusions are a stop-word list the check prints with its result; a hit under `planning/`, `src/` or `test/` fails the check. Done when: slice 2's planning at the pre-scrub commit (in the audit repository's history) fails the check, the fixture's does not, and the overlay's sheet carries a numeric amount cell that the check catches.
- [x] P4.3 (built, 0.14.2: `delivery`'s "Removing a value from history" and its scan of every commit before every push, `security-review`'s section that names it, the orchestrator's E paragraph, `source_scan.py map`, `rewrite` and `scan --map`; `orchestrator-delivery-removal` plants two values in one commit of a clean tree and grades what the remote received, the log and the report) **A removal from history is a procedure.** In `delivery` (and named by `security-review`'s suggested-fix text): the replacement map lives outside the repository; the record names counts and files, never values; the map's keys are grepped over every commit reachable from the branch (`git rev-list` and `git grep <key> <commit>`, or `git log -S`), not only the working tree, plus the log, the report and the PR body, before every push, and again over the remote's branch after a force-push; a force-push needs the owner's words and `--force-with-lease`; the transcripts and the audit repository are named in the report as copies the owner decides about. Done when: the text is in and an eval case plants a value to remove and grades the record.

## P5. Audit and measurement

Files: `skills/orchestrator/scripts/audit_sync.py`, `evals/tools/audit_report.py`, `evals/tools/` (two new scripts), `.claude/skills/audit-review/SKILL.md`.

- [x] P5.1 (0.14.3, 2026-11-10; the slice 2 sync itself is the owner's to run, see "Where the list stands") **Transcripts picked up by session id.** `audit_sync.py --transcripts` also copies, by session id from `$KAD_AUDIT_DIR/sessions/*.jsonl`, any project transcript under `~/.claude/projects/` not yet in `transcripts/`, with three rules: a transcript (and the hook's snapshot) is copied only after P4.2's scanner found none of `planning/sources.md`'s values in it, otherwise the sync line says `withheld: <session>` and the owner decides (slice 2's transcripts, which hold the workbook dump, would have been withheld); a copy whose source is newer or larger is refreshed on the next sync, and a session counts as complete only when its SessionEnd is in the session log; each sync takes a lock file in the clone so two sessions cannot interleave. `audit_report.py` says "on disk, not copied" or "withheld" instead of "no transcript kept". Why: the owner's browser-review session (`4e0e20ec`, 3.7 MB on disk) shows as "no transcript kept" because the hook copies only at SessionEnd or at an orchestrator snapshot. Done when: that session is in the audit repository.
- [x] P5.2 (0.14.3, 2026-11-10) **The review's two probes become tools.** The cold read with execution probes and the mutation pass (the briefs are in the slice 2 review's companion files and in the agents' prompts of 2026-11-08) become `evals/tools/cold_read.md` (the brief, launched as an Opus agent against a clone) and `evals/tools/mutation_pass.py` (the scripted exact-string mutants and the runner), so the next review and P3.2's D review run them the same way. Done when: `audit-review`'s SKILL.md names them and the slice 3 review uses them.

## After this list

Both runs start with `kad` from the project's root (0.14.4 installed:
`claude plugin update kad-dev-team@kad-dev-team-marketplace`, then a
restart), never plain `claude`.

1. Slice 2's fix round: done 2026-11-10 (see the table). What its review measured against the 2026-11-08 run: orchestrator thread $49.74 to $20.03 (44% to 18% of the session), session $111.96 to $109.68, loop 3 h 54 m to 3 h 39 m, four Highs found in the browser inside the loop, regressions 25% to 19%, the owner's turns in the loop six questions to one, cold read 4/4/4/4/3/4 to 4/3/4/4/3/3, mutation pass 95% to 93%. The cold read's project findings are issues #33 to #41.
2. Slice 3 of the unit (seed the starting rules from the owner's sheet; `planning/slice-002.md`'s slice set) under `kad` with Chrome, the `light` cadence arm and the chunk runner, audited the same way plus the new tools; the review decides P3.2's keep list and the default cadence.

## Dropped

- TODO 4.3, run 2 leftovers in `personal-finance-tracker-2`: won't do (owner, 2026-11-08).
- The heavy policy and anything from it (decided 2026-11-06; confirmed by H5 on 2026-11-08).
