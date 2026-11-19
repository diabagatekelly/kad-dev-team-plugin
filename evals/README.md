# Evals

`claude plugin eval` is out of early access and confirmed working.

Each case is a `case.yaml`, executed by `claude plugin eval` as a
genuine child `claude` process per run, with a no-plugin baseline arm
(`--ablation with-without`). Today that is the `library-app-*` suite for
`software-architect:architecture-review` plus two
`architecture-review-neg-*` trigger cases, and the `security-review-*`
suite for `devsecops-engineer:security-review` (five cases on the same
fixture plus two negative trigger cases), followed by the
`reliability-review-*`, `supply-chain-review-*`,
`operational-readiness-*`, `security-requirements-*` and
`reliability-requirements-*` suites on the same fixture, and the code
personas' `tdd-implementation-*`, `test-quality-review-*`, `code-review-*`
and `map-*` cases (their plants are case-only overlays in
`fixtures/library-app/code-plants/`), and the UI personas'
`design-system-*`, `screen-design-*` and `accessibility-review-*` cases
(overlays in `fixtures/library-app/ui-plants/`). Results land in
`evals/results/<timestamp>/` (gitignored) each time the suite runs;
nothing is hand-copied into case directories. The orchestrator's routing
table has one `orchestrator-route-*` case per row (overlays in
`fixtures/library-app/route-plants/`).

The original emulated cases (a `prompt.md` with `graders/*.md`, run by a
`.claude/skills/agent-eval` stand-in that role-played the persona) were
replaced skill by skill and are gone, along with the stand-in; their
summaries are in git history.

## The library-app suite

`fixtures/library-app/app/` is a 60-file TypeScript lending service for a
community library (catalog, members, loans, fines, reminders, legacy
reporting, Postgres/email/SMS/payment adapters, a composition root). It is
one realistic app, not clean-vs-dirty snippets: most of it is sound, and
`fixtures/library-app/answer-key.md` lists every deliberate exception —
15 planted violations and 9 traps (code that looks wrong and isn't), each
tied to a principle in `agents/software-architect/AGENT.md`,
`skills/architecture-review/SKILL.md` or `.synthesis/software-architect.md`.
`fixtures/library-app/verify.sh` proves the app type-checks, that the
planted runtime import cycle really crashes at module load, and that the
type-only cycle really doesn't. Other personas can plant their own
defects in the same app later.

Each `library-app-*` case scopes the reviewer to one module or one PR and
carries one substance-only grader per planted violation in scope ("did it
find this and propose a fix that would work"), one per trap ("did it
refrain from flagging this"), and a display-only trigger check. Rule
names, category labels and exact severity words are never graded; two
earlier generations of cases (inline snippets with answer-key graders)
failed mostly on their own graders being narrower than a good review, and
that is what this design avoids. `tools/pairwise_judge.py` adds what the
CLI lacks: a blind side-by-side judge that sees the with-plugin and
no-plugin reviews unlabelled in both orders and records its reasoning in
`pairwise.json` (the CLI's judges answer PASS/FAIL in one word and keep no
reasons). The judge itself is
`tools/implementation_judge.py` (the orchestrator's Combine-step judge
until the chunk loop replaced that flow on 2026-10-24; kept here because
these tools still use it; the heavy-against-lite comparison went with the heavy skill on 2026-11-06); this tool
imports it and adds the review rubric and the results-dir plumbing.
`tools/compare_arms.py`, which judged the slice built by `tdd-implementation` against the same slice built by `tdd-implementation-lite` (G2's measurement), went with the heavy skill on 2026-11-06; there is one implementation skill now and nothing to compare. Its last results are the G2 rows in the coverage table.

Run it:

```
bash evals/fixtures/library-app/verify.sh
claude plugin eval . --case 'library-app-*' --ablation with-without --scaffold \
  --judge-model sonnet --max-cost-usd 14 --no-publish --trust-plugin
claude plugin eval . --case 'security-review-*' --ablation with-without --scaffold \
  --judge-model sonnet --max-cost-usd 10 --no-publish --trust-plugin
python3 -I evals/tools/pairwise_judge.py evals/results/<timestamp>
```

`library-app-*` does not match the security cases and `security-review-*`
does not match the architecture ones, so each suite runs on its own.
Every real case pins `execution.model: sonnet`; see "Which model" below
for why, and for the one Opus comparison run.

Things the CLI does not tell you, learned the expensive way: `--scaffold`
is mandatory (each case's `scaffold.sh` copies the fixture into the run's
working directory; `context.add_dirs` is passed to the child at its
original absolute path but nothing tells the agent that path, so the first
smoke test "passed" on an empty review); `--case` cannot be repeated, the
last one wins; `add_dirs`, `scaffold_script` and `baseline_file` must all
resolve inside the case directory, and symlinks out are refused; the
`baseline` grader compares against a checked-in reference transcript, not
the live no-plugin arm; a `tool_used` grader on a subagent call needs
`tool: Agent`; an `llm` grader with `focus: trace` sees only the first and
last 12 trace messages (the rest is elided), so on a long run it is really
grading the final report — check process with `regex` (which scans the
whole trace; `(?:…[\s\S]*){N}` with `contains` means "at least N"),
`tool_order` and `tool_used`, and code with `focus: {source: file, path}`;
a `tool_used` grader that isn't `tool: Skill` is scored in
both arms unless marked `arm: with-only`; `AskUserQuestion` is never
available and the scaffolded project's `.claude/settings.json` (hooks
included) is ignored, see "Interactive skills" below.

**Grade a report from a saved file, not from `last_message`.** The judge
has failed a long review as `last_message` and passed the identical text
as a file, and an agent-path run can end on a one-line postscript that
then gets graded instead of the report. Every review case therefore asks
for the review at `docs/reviews/<case>.md` (`Write` in `allowed_tools`, a
`review-written` `file_exists` grader, each `llm` grader with
`focus: {source: file, path: …}`, and a `leaves-the-code-alone` trace
regex that fails any other Write or Edit); the tdd cases do the same with
`docs/reports/<case>.md`. `last_message` is for a phase that ends in
questions. A full pass costs about $7.50 at
`--runs 1` plus about $2 for the pairwise judge; the suite's `runs: 3`
default triples the first number.


## Playbook: a real suite for another skill

This is the procedure that produced the library-app suite, written so the
next skill doesn't repeat the three generations it took to get here. Budget
two to three calibration passes at `--runs 1` (about $8 each for a
nine-case suite with the pairwise judge) before trusting anything.

1. **Derive coverage from the spec, not from a fixture.** Read the persona's
   `AGENT.md`, each `SKILL.md`, and `.synthesis/<persona>.md`. Make one row
   per principle: what a violation looks like, and what its "looks wrong
   but isn't" trap looks like. The synthesis usually names principles the
   skill text only implies (for `software-architect` it added design
   influence, interface ownership, YAGNI-vs-Dependency-Rule and
   state-the-ordering). Check which of those live only in `AGENT.md`:
   the eval never loads it, and neither does a direct or inline skill
   invocation, so anything the skill needs must be in the skill.
2. **Plant in `fixtures/library-app/app/`** (see its README for the rules:
   no hints, no accidental problems, traps for every principle that has a
   wrong-looking side, `verify.sh` green). Add every plant to
   `answer-key.md` with a prefix for the persona.
3. **Scaffold cases with `tools/new-case.sh <name> <skill>`.** One case per
   module or PR, scoped so no run faces more than about five findings; one
   case on a clean module expecting nothing above Low; keep or add
   negative trigger cases (a request the skill must *not* fire on). Prompts
   name files only to set scope. Graders: one "finds it" per plant in
   scope, one "doesn't flag it" per trap, all substance-only; never grade
   vocabulary, labels or exact severity words, and never put revision
   history in a grader (the judge reads it as instructions).
4. **Calibrate.** Run `--ablation with-without --runs 1 --scaffold` and the
   pairwise judge. Read every failure in the with-arm and every pass in
   the without-arm. Decide in this order: is the answer key wrong, is the
   grader narrower than a good review, is the fixture leaking the answer
   or carrying an accidental problem, and only then is the skill wrong.
   A case both arms pass is a regression guard, not evidence of uplift;
   say so in the coverage table.

   Checking a judge verdict: `tools/rejudge.py <result.json> <grader>`
   rebuilds the eval's judge prompt from the result file and asks
   `claude-sonnet-5-5` the same one-word question (`--explain` asks it
   why; `--criteria-from` tries a reworded grader on an old output). Treat
   its answer as a hint. It agreed with the eval on a file-focused grader
   with stacked exceptions, and disagreed on three others: the eval's
   judge failed them 3/3 and the re-ask passed them 5/5. A throwaway probe
   case (scaffold the graded text in, grade it in the eval) showed the
   eval failing a long review as `last_message` and passing the identical
   text as a file. Only the eval's own judge is authoritative, and on a
   borderline output it isn't stable. What helps: grade a saved file
   rather than a long last message, and split a grader that stacks
   exceptions ("may appear in either section", "this is not an addition")
   into plain checks. `claude -p --model sonnet` in this shell may reach a
   different model altogether, so don't re-ask that way.
5. **Fix the skill only for a failure that survives step 4**, re-run the
   affected cases, and record the finding in this README's findings list
   and the persona's `PERSONAS.md` row.
6. **Record the bar.** Once a case's result is accepted, run
   `tools/record_thresholds.py <case>` and commit the `thresholds.json`
   change with the case, so the eval gate has something to hold it to.
   Then run the gate on the case once more: recording the bar also records
   the skills its runs consulted (`skills_invoked`), which widens the set
   of files the case's evidence fingerprints, so evidence recorded before
   the bar existed reads as stale on the first push.
7. **Keep run output out of git.** `results/` is ignored; the coverage
   table carries the numbers and the results directory name, nothing else.

### Interactive skills: one case per phase, chained by `history_file`

`claude plugin eval` never offers `AskUserQuestion`: every run gets the
same fixed tool set (`Task`, `Glob`, `Grep`, `Read`, `Skill`, `TaskStop`,
`ToolSearch`) whatever `allowed_tools` says, and `ToolSearch` cannot find
it. Project hooks don't load either (the sandbox writes its own settings),
so a hook cannot script the answer. What works is the undocumented
`context.history_file` field: the run resumes that session transcript and
`execution.prompt` becomes the next user turn. An interactive skill
therefore runs as a chain of cases:

1. **Phase 1** is an ordinary case. Without the tool, the skill has to ask
   in plain text and end its turn. Grade the question: it asks about the
   real decision, gives its recommendation and the rejected alternatives,
   and has not decided anything unilaterally.
2. **Freeze it.** Run phase 1 through the gate with `--keep-scaffold`
   (`wsl-gate.sh --keep-scaffold --runs 3 --cases <phase-1>`): each run's
   kept directory is printed and recorded as `scaffoldDir` in the result.
   Read the three final messages, take a run whose question is a good one,
   and run `tools/freeze-history.sh <kept-dir>
   evals/<phase-2-case>/history.jsonl` in the clone that ran it (by hand,
   the CLI's `--keep-temp --json <file>` gives the same directory: the
   parent of `out/` in the run's `tracePath`).
   A resumed phase (2 onward) writes its transcript next to its own
   `history.jsonl` instead, one branch per run; freeze it with
   `tools/freeze-history.sh evals/<case>/<session>.jsonl <next>/history.jsonl
   "<text from the chosen run's final message>"`. In WSL that transcript
   is in the clone, and `wsl-gate.sh`'s next mirror deletes it, so freeze
   before the next run and write the output to the Windows checkout
   (`/mnt/c/...`).
   It keeps only the user and assistant turns, so review the message text,
   nothing else, before committing. It writes the plugin's path as
   `<plugin-root>` and refuses to write one containing your home
   directory; `.githooks/pre-commit` rejects any committed line that does
   (enable it once per clone with `git config core.hooksPath .githooks`).
3. **Phase N** sets `context.history_file: history.jsonl` and puts the
   scripted answer in `execution.prompt`. Grade the reaction. At least one
   answer in each chain should reject the recommendation, to check the
   skill changes course instead of finalizing what it had already decided.
   Re-freeze downstream phases whenever the skill text changes at all:
   a frozen history carries the `SKILL.md` text as it was loaded in the
   earlier phase, so a later phase keeps running the old instructions
   until the earlier phase is re-run and re-frozen;
   `tools/history_stale.py` lists every history whose loaded skill text
   no longer matches the skill (it found two stale chains the audit's
   reading of commit dates had missed), and the gate refuses to run
   such a case (it fails and loses its evidence until re-frozen):
   editing a skill and re-running its phase 2 in the same session
   scores the old text, which is how
   `requirements-refinement-payfine-phase2` got three batches of results
   against a history frozen three days earlier. A resumed run starts
   in a fresh sandbox, so anything the frozen turns wrote with `Write`
   is gone; a phase that needs those files (design candidates to choose
   from) recreates them in its `scaffold.sh` with
   `tools/history_files.py history.jsonl . --require`, and pins nothing
   from the frozen text in a grader without a check that fails loudly
   when the history changes (`design-system-payfine-phase3`'s scaffold
   checks the pinned brand colour is still the second candidate's).
   Grade a phase that ends in questions or forks on `last_message` (it is
   short); grade a phase that writes the document on the saved file.

Answers arrive as a user message rather than an `AskUserQuestion` result,
which is the one fidelity gap.

## Eval gate

The gate is two parts: a run that costs model time, done on your machine
on the Claude subscription, and a free check on every pull request that
the run happened against exactly the files the change touches. Like a
coverage gate: the cost is paid once, locally, and the PR carries the
proof.

**Running the gate.** From the repository root on Windows:

```
wsl -d Ubuntu-22.04 -- bash evals/tools/wsl-gate.sh            # what changed against main
wsl -d Ubuntu-22.04 -- bash evals/tools/wsl-gate.sh --cases a b
wsl -d Ubuntu-22.04 -- bash evals/tools/wsl-gate.sh --all      # every case
```

`tools/wsl-gate.sh` mirrors the checkout (uncommitted work included)
into the WSL2 clone, runs `tools/eval_gate.py` there and copies the new
results, `evidence.json` and `thresholds.json` back, so the next step
is to commit. Inside Linux, WSL2 or macOS run `bash evals/tools/gate.sh`
with the same arguments: on Linux it is `eval_gate.py`; on macOS it first
puts Homebrew's Node 24 on PATH, which the sandboxed runs inherit (the
fixture's test script passes `--experimental-transform-types`, gone in
Node 26, and nvm's install is under the home directory, which the eval's
sandbox does not let a run read), and checks for a `git` shim at
`$(brew --prefix)/sbin/git`. The shim is needed because inside the
eval's sandbox `git` by name is Apple's `/usr/bin/git` shim, which needs
`/Library/Developer` and a cache under `/var/folders`, both denied, and
the shell skips Homebrew's git on PATH (its Cellar target cannot be
stat'ed there), while `sbin` is readable and already on PATH after `bin`;
a two-line script there that execs Homebrew's git is found by name inside
a run and changes nothing outside one. `gate.sh` prints the command to
create it and never writes into a system directory itself. Nothing
documented for `claude plugin eval` widens its sandbox (2026-10-31). The
plugin's own scripts fall back to a working git regardless. Windows
itself cannot run the gate (below).

`claude plugin eval` refuses an eval directory of more than 20,000
entries ("move large fixtures out of it"), and every run leaves its
output directory under `evals/results/` (about 100 entries each, ignored
by git): after some 2,000 runs the gate stops starting. Move the run
directories older than the current review out of the repository
(`mv evals/results/2026-1*/ ~/kad-eval-results-archive/`, keeping the
flat `gate-*.json` and `.log` files that `thresholds.json` and the
evidence name); 2026-11-12 moved 1,935 of them there after the gate hit
the limit mid-review.
What the gate does:

1. `tools/affected_cases.py` picks the cases the diff can reach: a changed
   skill's own cases and the cases whose runs were seen consulting it
   (`skills_invoked` in `thresholds.json`), a changed agent's delegation
   cases and its skills' cases, a changed fixture's cases (from what each
   `scaffold.sh` copies), any edited case, and any case whose entry in
   `thresholds.json` differs from the base (its evidence must clear the
   bar as it now stands). A README or tool change reaches none.

   Since 0.16.0 a case depends on less than every file it loads (the
   owner, 2026-11-16, when the screen-change check's pull request staled
   71 cases and 25 had anything to do with it). Three rules, all in
   `affected_cases.py`'s `view()`, which the affected list and the
   evidence fingerprint both read:
   - **The state a case is built from, not the loop fixture.**
     `tools/loop_states.py --write` builds every loop state a scaffold
     names, hashes the tree each leaves (commit hashes, dates, clock
     times, temp paths, durations and the order of failing tests taken
     out; every state built until two builds agree) and writes
     `loop_states.json`. A case on a loop state depends on its state's
     entry. The file records a hash of everything a state is built from,
     and the pull-request check fails until it is written again after
     any change to that (about five minutes, no model). Exact: a state
     whose tree did not change cannot behave differently.
   - **The scripts a case ran.** `affected_cases.py --record-scripts`
     reads every kept trace (the session's commands and its launched
     agents') and lists in `case_scripts.json` the scripts under
     `skills/*/scripts/` each case ran; a case depends on those and on
     the siblings they import or run, whichever skill owns them. A
     script a case has never run stales it no more. Run it after a gate
     pass that added cases; it only ever adds.
   - **The orchestrator's steps.** A case depends on the skill's text
     outside its five step sections, plus the sections (and log-format
     lines) of the steps `tools/orchestrator_steps.json` gives its state:
     an edit to E stales the cases that reach E. This one is a bet, taken
     knowingly: the whole text is still in the model's context, so a miss
     caused by a paragraph in another step is not seen until that case
     next runs. A new state needs a line in that file (a test fails
     without it); a skill whose section openings moved is taken whole.

   The first rule had a defect until 0.16.1: the hasher read the id of
   the session that recorded a state's sidecar rows, so a manifest
   written in one session matched no build made in another (19 states
   read as changed on identical trees). It strips the id now. When the
   hasher itself changes, `eval_evidence.py --carry <checkout of the
   base>` builds every state from both trees and re-stamps the evidence
   of a case whose state builds alike and whose other files did not
   move; it names the states that really differ.
2. `tools/eval_gate.py` runs them once each, up to six cases and eight
   agent runs at a time (`--jobs`, `--parallel`). A case at several runs
   (`--runs 3`, or a re-run) gets its runs as concurrent children of one
   CLI process, so a three-run case takes about the time of one run; a
   tdd case is two to three minutes, a review case one to two. Every run
   shares the subscription's one rate limit, so the cap is on runs in
   flight, not cases. It re-runs at full `runs:` any case that is
   suspect: its score lands more than the tolerance below its bar in
   `thresholds.json` (0.1, or the width of one grader flip in one run,
   1/(graders × runs), when that is wider: three graders at three runs
   move 0.111 on one flip, so a flat 0.1 failed such a case as often as
   not), or a grader the bar recorded as passing every run fails (the
   judge is noisy; one run proves little).
3. It fails if a case is still below its bar, or if an always-passing
   grader failed in every re-run. The aggregate tolerance absorbs judge
   noise; the per-grader check is what stops one grader regressing for
   good inside a case with ten graders, where losing it moves the
   aggregate by less than the tolerance. The table names the lost
   graders. Results, logs and every run's trace land in `results/`
   (gitignored).
4. Every case that passed is written to `evidence.json`: a fingerprint
   of the files it loads (the same set step 1 matches a diff against,
   with CRLF folded so Linux and Windows agree), its score, bar, run
   count and result file. A case that failed loses its entry.

**The pull-request check.** `.github/workflows/eval-gate.yml` runs
`tools/eval_evidence.py` on every pull request that touches `skills/`,
`agents/` or `evals/`: for each case the diff reaches, the committed
`evidence.json` must hold an entry whose fingerprint matches the files
as they are in the PR and whose score clears the current bar. A missing
entry, a stale one (something the case loads changed after the run) or
a bar it no longer clears fails the check and prints the command to
run. No model is called; it takes seconds and needs no secret. The same
check runs as a pre-push hook once `git config core.hooksPath .githooks`
is set, so the refusal arrives before the push, with the same command.
Bypass a push with `--no-verify`; the PR check still stands.

**Bars come from gate runs.** The gate scores with `--ablation none`,
where every grader counts; calibration runs use `--ablation with-without`,
where the CLI treats skill-invoked `tool_used` graders as unscored
indicators. A bar recorded from a calibration run therefore has a
smaller denominator than the score the gate compares it with, and the
gate reads slightly high against it. `record_thresholds.py` stores each
bar's `mode` and warns when it is `calibration`; `--gate-only` ignores
calibration results altogether. The per-grader rates it stores
(`graders`) are what the regression check reads; bars recorded before
that field existed get the aggregate check only until re-recorded.

When a change is meant to move a score, re-record that case's bar with
`tools/record_thresholds.py --gate-only <case>` from a gate run of it
(on Windows, after `wsl-gate.sh` copied the results back) and commit it
with the evidence in the same PR. The gate works before you commit:
`affected_cases.py` includes uncommitted and new files, and the
fingerprint is of the working tree.

**The paid path still exists.** The workflow's `workflow_dispatch` runs
the cases on GitHub's own runner with an `ANTHROPIC_API_KEY` repository
secret (and, for a user-scoped `sk-ant-usr-…` key, an
`ANTHROPIC_WORKSPACE_ID` secret the workflow turns into the
`anthropic-workspace-id` header). No such secrets exist today and the
dispatch fails at the first model call without them; the pull-request
check does not use them. If they come back: `gh secret set` reads the
value from stdin, so run it from an interactive terminal or pass
`--body`; the runner image must be Ubuntu 22.04 (24.04's AppArmor
restriction on unprivileged user namespaces breaks bubblewrap's loopback
setup, after which review cases quietly fall back to Read and Grep and
still pass, which is why the job probes `bwrap` first); budget about
$0.45 per review case including the judge, more for a tdd case.

**A case that grants `Bash` needs a sandbox backend on the machine.**
The gate grants each case only the gated tools its own `allowed_tools`
names (`Write`, `Edit`, `Bash`; four cases name `Bash`). Until
2026-10-14 it granted all three to every case, and a Write-only case
would then write its files through a shell heredoc or a generator
script that a grader reading `Write` calls could not see. On Windows
the CLI refuses to start a run that grants `Bash` ("sandbox required
but unavailable"), so the four tdd and map-update cases need WSL2
there; the rest should run on Windows, untried. The CLI still scores a
refused
zero-turn run: every positive grader fails and a "called 0 times"
grader passes vacuously, so both tools score only the runs that did not
error and report a case with none as an error, not a score. WSL2 is the
answer on Windows: `wsl --install -d Ubuntu-22.04` from an elevated
PowerShell, reboot, then `bash evals/tools/wsl-setup.sh` inside Ubuntu
(bubblewrap, Node 24, the pinned CLI, a sandbox probe); the script
prints how to make the clone and log in. Running `claude plugin eval`
by hand without the `Bash` grant works anywhere for cases that don't
need a shell.

Audit mode (`hooks/audit.sh`, see the top-level README) is where new cases
should come from: the `audit-review` skill reads real sessions against the
skills' rules and turns each real miss into a fixture-based case.

## Coverage

Case names follow `agent:skill` for persona-backed triggers, or just
`skill` for a skill with no owning persona (e.g. `orchestrator`).

The five heavy `tdd-implementation-*` cases (`-cancel-hold`, `-cancel-hold-via-agent`, `-chunk-plan`, `-named-fix`, `-one-chunk`) were retired with the skill on 2026-11-06 (0.13.0): the lite cases cover the same contract, `-one-chunk` was ported to `tdd-implementation-lite-one-chunk`, and `compare_arms.py` (the heavy-against-lite judge) went with them. Their rows are in git history.

**Last result** is the most recent score. **Current** says whether that score
still describes the code: a case goes stale the moment its `AGENT.md` or
`SKILL.md` changes, or its own fixtures/graders are edited. A stale case's
score is history, not a claim about today.

| Case | Last result | Current? |
|---|---|---|
| `orchestrator-security-stage` | real, Sonnet: 2/2 runs all pass (`results/20261011-orch-cal2`); baseline fails routing and writes no log — "what's next?" on a real planning folder fires the orchestrator, which routes to `security-requirements` by invoking the skill, passes the save location, writes the log at routing time, and the persona asks its questions. Phase E (2026-10-15): the design doc's "Open for devsecops-engineer" section is gone; routed from the slice placeholders alone, 3/3 runs | yes |
| `orchestrator-superseded-scope-map` | real, Sonnet: 2/2 runs all pass — real inspection: reads `## Status` and routes to requirements for the Active map's step 1, not to slicing from the superseded map's requirements doc. The baseline also routes correctly here, so this is a regression guard on inspection, with the skill-invocation graders as the plugin-fired check | yes |
| `orchestrator-backward-route` | real, Sonnet: 2/2 runs all pass, again after `vertical-slicing` gained its stop-first rule (`results/rrf-*`) — a "Handed back to product-slicer — blocking" section routes to `product-slicer`, not forward to reliability criteria; the log records why. Phase E (2026-10-15): receipt hand-back; its grader had kept the refund wording and failed one run that routed correctly and chose growth with reasons; reworded, 3/3 twice. 2026-10-31: two runs in three matched the forward table (reliability criteria) before reaching the hand-back section at the end of the security document, a real miss; the skill now says those sections sit at the end and every document is read to its last line before a row is matched. 0.90 after, no forward step; the judge also accepts the slicer putting the scope choice to the owner, the v4 way. Bar re-recorded | yes |
| `orchestrator-asks-for-target` | real, Sonnet: 2/2 runs all pass; baseline 0/1 — no folder given, it asks where the artifacts are before anything else and doesn't search the project | yes |
| `orchestrator-session-setup` | step 0 (0.9.0): a session not started by the launcher, with Bash granted, is asked about audit mode and the restart under the sandbox runtime before the target question; no planning skill invoked. Recorded on the Mac. 2026-11-08 (0.14.0, handoff-slice2 P1): rewritten for the opposite behaviour. The launcher is the one way in and step 0 asks nothing: a session fenced by something other than the launcher (this harness) is told so in one line and routed; a plain session would be given the one command and stopped, which the harness cannot stage (it fences every run). Graders: no `bin/kad` run from the session, routes to `problem-framing-doc`, a judge on the absence of every old question | yes |
| `orchestrator-route-problem-framing` | real, Sonnet: 10/10 over 2 runs (`results/g8-*`) — a new, empty planning folder: routes to `problem-framing-doc`. The first version left the folder empty on disk; an empty directory doesn't reach the sandbox, so the orchestrator searched for it and stopped. The prompt now says the folder is new | yes |
| `orchestrator-route-scope-decision` | real, Sonnet: 9/10 over 2 runs (`results/g8-*`) — a problem doc and nothing else: routes to `scope-map` to decide whether a map is needed. Known miss 1/2: once `scope-map` decided no map, the orchestrator went straight on to `requirements-refinement` without asking, against step 5's never-chain-silently rule. Four attempted fixes each caused a worse regression elsewhere and were reverted (see findings). 2026-10-31: two graders still encoded v3's one-step-per-invocation rule, while the v4 skill continues to the next row and asks only when the owner is needed; they now say so. 0.94 (one judge loss in three runs), bar re-recorded. 2026-11-01 (0.9.0): 0.89 over 3 runs after step 0 landed; every run had requirements-refinement read `collect-fine.ts` and the fines routes before asking, as its own rule says to, and the judge read "I read the code first" as answering from the repository. The grader now says reading and reporting what was found is that rule, and the FAIL is a question settled without the owner. 2026-11-08 (0.14.0, P1): 0.83 in 3/3 at the gate (the `stops-after-the-routed-step` judge FAIL FAIL FAIL each run: the orchestrator went from scope-map straight into requirements-refinement's questions without reporting the scope-map result in its reply, the same miss as above); the history of this grader since 0.7.0 is a flip on nearly every gate, with three misses in a row twice before, so the case was re-run alone at three runs and scored 0.89 (2 of 3), within tolerance; evidence recorded from that run, bar unchanged. 2026-11-10 (0.14.3, P5, which changed nothing on this path): the same judge FAIL FAIL FAIL in both runs that finished at the gate (0.83), 0.89 (2 of 3) re-run alone, within tolerance; evidence from that run, bar unchanged. The miss is real and the same each time: the reply goes from scope-map's decision straight into requirements refinement's questions without reporting the decision in its own words first | yes |
| `orchestrator-route-slicing` | real, Sonnet: 10/10 over 2 runs (`results/g8-*`) — problem plus an Active requirements doc: routes to `vertical-slicing`. 2026-11-01 (0.9.0): 0.86 over 3 runs; one run went on from the slice into `user-story-writeup` and stopped at its own question (where to file), which the v4 skill allows and this case's two graders, still on v3's one-step rule, did not; aligned the way `route-scope-decision`'s were on 2026-10-31, and `not-user-story-writeup` became `not-architecture-design` | yes |
| `orchestrator-route-user-story` | real, Sonnet: 10/10 over 2 runs (`results/g8-*`) — a slice not yet written up: routes to `user-story-writeup` | yes |
| `orchestrator-route-design` | real, Sonnet: 9/10 over 2 runs (`results/g8-*`) — a user story and no design: routes to `architecture-design`. The miss was the grader: it forbade any `security-requirements` call, and `architecture-design` legitimately consults it inline; that check is now `not-tdd-implementation`, which both runs pass | yes |
| `orchestrator-route-reliability` | real, Sonnet: 12/12 over 2 runs (`results/g8-*`) — a non-UI cancel-hold slice with security filled and reliability a placeholder (`route-plants/cancel-hold-reliability-open/`): routes to `reliability-requirements` | yes |
| `orchestrator-route-design-system` | real, Sonnet: 16/18 over 3 runs (`results/gate-20261014T200227`; 12/12 over 2 runs in `results/g8-*`) — a UI slice with both runtime-safety criteria filled and no design system: routes to `design-system`. Since 2026-10-14 one run in three routes to `reliability-requirements` instead: the shared slice fixture lists its security and reliability criteria unlabeled among the functional ones, so "filled" is a judgment call (F1 in `TODO.md`); the bar is recorded as it scores | yes |
| `orchestrator-route-screen-design` | real, Sonnet: 12/12 over 2 runs (`results/g8-*`) — a design system but no screen design: routes to `screen-design`. 2026-11-01: the same v3 leftover as the other routing cases (a max-zero on accessibility-review, a judge forbidding the continue), where the v4 orchestrator goes on to the accessibility review once the screen design is written; the graders now order it after screen-design and accept it. 0.95 (one `log-names-row-and-artifact` judge loss in three), bar re-recorded | yes |
| `orchestrator-route-accessibility` | real, Sonnet: 12/12 over 2 runs (`results/g8-*`) — a screen design with the accessibility criteria a placeholder: routes to `accessibility-review`. Phase E (2026-10-15): the screen design no longer names `accessibility-engineer`; 3/3 runs | yes |
| `orchestrator-route-tech-bootstrap` | real, Sonnet: 10/10 over 2 runs (`results/g8-*`) — the fully specified cancel-hold slice in a repo with no stack: routes to `technology-bootstrap` | yes |
| `orchestrator-route-implementation` | real, Sonnet: 9/10 over 2 runs (`results/g8-*`) — the same slice in the library app: routes to `tdd-implementation` through the quarantine flow (not exercised). The miss was the grader demanding the log mention the stack, which the skill's own log template doesn't; loosened, both kept logs pass a re-ask (a hint) | yes |
| `orchestrator-route-implementation-prenamed` | real, Sonnet: 0/3 then 3/3 at 1.0 (`results/gate-20261018T160908`, then `gate-20261018T161403`) — G1 (2026-10-18), from H6's second session: the same slice with "if the next step is the implementation and its quarantine flow, go ahead with it". Before the fix every run invoked `tdd-implementation` directly, inline, with no orchestrator, no log and no sandbox check. The orchestrator's and `tdd-implementation`'s descriptions now say a stage guessed at while asking to move forward is not a skill named; after it all three runs route through the orchestrator, write the log, and stop at the sandbox check with nothing built. No baseline arm | yes |
| `orchestrator-route-backward-requirements` | real, Sonnet: 12/12 over 2 runs (`results/g8-*`) — `slice-000` says no requirements pass ran for its step (`route-plants/backward-pm/`): routes back to `requirements-refinement` for that step, not on to its user story. Phase E (2026-10-15): `slice-000` no longer names `requirements-refinement` or `product-manager`, only that nobody confirmed the step's WHAT; 3/3 runs | yes |
| `orchestrator-route-slicer-accessibility-mistake` | real, Sonnet: 1.00 in 3/3 then 1.00 on the stale pass's run (`results/gate-20261101T*`, the Mac): the fully planned UI slice with its accessibility line replaced by the slicer's not-applicable line; every run routes back to `product-slicer` to fix the line in place, with the log naming the contradiction, and runs no accessibility review, screen design or build around it. Bar recorded; issue #25's rule from the mistake side (Sourcery's finding on PR 29: both branches of the rule are now graded, this case and `vertical-slicing-payfine-phase1`, which fails a not-applicable line on its portal slice) | yes |
| `orchestrator-readiness-gate` | real, Sonnet: 1.00 in 3/3 (`results/gate-20261031T2*`, the Mac). The first one-run pass went past A and built chunk 1 (12 minutes, $2.76): the skill rightly continues once the gate passes, so the prompt now hands off at the A line. The next pass lost a `file_exists` the harness resolved against the shell's last `cd` (the content grader on the same file passed) and a judge that read an inline skill run as the orchestrator deciding for itself; both reworded. Every run then: the gate run by the script, two backward routes to `reliability-requirements` and `screen-design` inline, the gate again, the A line, the handoff, no builder; v4 PR 3, design §11 case 1): the A step's design-readiness gate on a fully planned UI slice whose reliability document says "retries the cancel a few times" and whose screen design has no mockup for the unreachable-queue state (answer key P1, P2): `readiness_check.py` before any builder, one backward-route entry per failed check, the first routed skill run inline with the check named, no builder while the gate fails. 2026-11-03 (0.12.0, H3.2): the fixture's design homes both failure paths under `### Strategic` and `### Tactical` only, its Decisions one line each, and `readiness_check.py` reads those headings by name; the old check failed both paths on that fixture, the new one passes them, and the `no-failure-paths-route` regex proves no route to architecture-design. 1.00 in 1/1, bar re-recorded. 2026-11-07 (0.13.1, H1.6): the A-line regex also requires the `transcript` field (`kept | MISSING | not checked`); 0.93 in 3/3 (`results/gate-20261107T191402`, about $1.70 a run), the field present in every run as `not checked (audit off)`. The loss is `backward-routes-name-the-checks` in two runs (judge votes FAIL FAIL PASS and FAIL FAIL FAIL): every log had the chunk-loop entry and both backward routes naming the check, the persona and the document, but two runs hung the A line under the second backward-route entry instead of the chunk-loop entry and the third wrote a second chunk-loop entry to carry it. Where the A line goes after backward routes is a candidate for the orchestrator's next text change; the gate passed within tolerance and the bar is not re-recorded | yes |
| `orchestrator-plan-check-seam` | real, Sonnet: 0.86 in 3/3 then 1.00 in 3/3 (the Mac). The one loss was the commit regex, which did not allow the JSON-escaped quotes the trace holds around the message; the behaviour was right every time: the plan sent back once to a fresh planner, the passing plan committed as `Plan: slice 001 in <n> chunks`, the B line, the handoff; v4 PR 3, case 6, plan half): resumed just after the planner returned a plan whose chunk 2 names no seam test (L5): the mechanical check fails, the plan goes back once to a fresh planner, the orchestrator never edits it, commits the one that passes, writes the B line, hands off | yes |
| `chunk-runner-gate-deviation` (until 0.14.1 `orchestrator-gate-deviation`; 2026-11-08: the step moved into the chunk runner, so the case invokes `kad-dev-team:chunk-runner` directly from the same fixture state, runs as Opus like the real runner, grades the same launches and files, and grades the hand-back line instead of a handoff file; 1.00 in 3/3 at the gate of 2026-11-09, bar re-recorded from it) | real, Sonnet: 0.71 in 3/3 then 1.00 in 3/3 (the Mac). The first pass found a real defect: the skill's gate command never allowed the slice's own uncommitted log, so the scope check failed every chunk on it (fixed in the command), and the deviation file's untested method failed coverage (the snapshot now covers it). Then every run: gate PASS with `lending/hold.ts` named as the deviation, recorded, no fixer, no plan edit; v4 PR 3, case 5, deviation half): chunk 1's commit touches `lending/hold.ts`, inside a design module but off the Files line (L1): the gate with `--module-dir` passes and prints the deviation; recorded, no fixer, no plan edit | yes |
| `chunk-runner-gate-outside` (until 0.14.1 `orchestrator-gate-outside`; 2026-11-08: the step moved into the chunk runner, so the case invokes `kad-dev-team:chunk-runner` directly from the same fixture state, runs as Opus like the real runner, grades the same launches and files, and grades the hand-back line instead of a handoff file; 1.00 in 3/3 at the gate of 2026-11-09, bar re-recorded from it; 2026-11-10 (0.14.3): the `runner-edits-no-code` grader removed, the judge carries it, 1.00 at the gate, bar re-recorded) | real, Sonnet: 0.95 then 1.00 in 3/3 (the Mac): the gate fails on scope for `utils/card-number.ts`, one fresh fixer, the gate again, `--allow` never widened, no reviewer before the pass; the first pass lost one `failure-handed-to-the-fixer-once` judge vote; v4 PR 3, case 5, failure half): the commit adds `utils/card-number.ts`, outside every design module (L2): the gate fails on scope, one fresh fixer, the gate again on the fix, `--allow` never widened, no reviewer before the gate passes | yes |
| `chunk-runner-review-round` (until 0.14.1 `orchestrator-chunk-review-round`; 2026-11-08: the step moved into the chunk runner, so the case invokes `kad-dev-team:chunk-runner` directly from the same fixture state, runs as Opus like the real runner, grades the same launches and files, and grades the hand-back line instead of a handoff file; 1.00 in 3/3 at the gate of 2026-11-09, bar re-recorded from it) | real, Sonnet: 0.90 in 3/3 on the first passes, every loss the reply tallying the smoke report itself because `rounds_record.py` had read the smoke agent's bulleted Severity as no finding (the recorder defect fixed in this PR), then 0.97 (the Mac): one combined reviewer and one smoke agent, two launches and no more, the round recorded by the script, the handoff; the reply may now carry a one-line title per needs-decision finding; v4 PR 3, case 3): resumed with chunk 1 built and gated: exactly one combined reviewer (`code-reviewer`, Opus) and one smoke agent (`tdd-coach`, the chunk is not UI), two launches and no more, the round recorded with `rounds_record.py`, the report at most eight findings and no Low, the handoff written once round 0 is recorded | yes |
| `chunk-runner-one-fix-round` (until 0.14.1 `orchestrator-one-fix-round`; 2026-11-08: the step moved into the chunk runner, so the case invokes `kad-dev-team:chunk-runner` directly from the same fixture state, runs as Opus like the real runner, grades the same launches and files, and grades the hand-back line instead of a handoff file; 1.00 in 3/3 at the gate of 2026-11-09, bar re-recorded from it) | real, Sonnet: 0.44 (git unusable in the Mac sandbox), 0.81, 0.70, then 1.00 in 3/3. The losses on the way: a regex that matched the pre-existing finding's words in a fixer prompt that named it to exclude it, replaced by a judge that then failed replies saying exactly what it asked, so dropped (the C line's standing entry and the single second fixer are checked mechanically); backticks on the split's numbers; and one run stopped on a secrets check under the runtime that the planted opt-out covered (the skill's bullet now yields to the opt-out). Then every run: round 1 recorded with `--range`, only the regression to the second and last fixer, the gate on it, no third review, the (reg 1, pre 1) split and the standing Medium on the C line; v4 PR 3, case 4): resumed after fix r1 was re-reviewed with one regression and one pre-existing Medium (L3): round 1 recorded with `--range`, only the regression to a second and last fixer, the gate on the fix, no third review, the C line with the (reg 1, pre 1) split and the pre-existing Medium standing | yes |
| `orchestrator-gap-without-delegation` (2026-11-08, 0.14.1: the runner now records round 0 and hands back the needs-decision, so the state is `chunk1-gap-handback` and the case grades the orchestrator's C.5 from the hand-back line: the persona launched once, no fixer and no runner, round 0 not recorded again; the runner's half is `chunk-runner-gap-handback`) | real, Sonnet: 0.88, 0.92, then 1.00 in 3/3 (the Mac). The skill told the persona to write nothing but asked the C line for a recommendation path; the orchestrator now saves the hand-back to its own records file and names it, and the state carries the reliability document the planted review cites. Every run: round 0 recorded, one consult, a recommendation back, no fixer, the flow stopped for the owner; v4 PR 3, case 2, orchestrator half): a `needs-decision` finding with no delegation file (L4): round 0 recorded, the owning persona launched once, a recommendation back with nothing written, `needs-decision devsecops-engineer: <path>` on the C line, no fixer, the flow stops for the owner | yes |
| `orchestrator-definition-of-done` | real, Sonnet: 0.91, 0.73 and 0.88 over three passes (the Mac); the README from `docs-writer:readme`, the script moved out of the template literal, comment density cut, the check green on the re-run, the handoff before the reviewers in every run. The judge fails `three-named-fixes-in-one-batch` on replies that report exactly those three fixes, and one run in three launches a second fixer or a slice reviewer early. Bar 0.88 as measured; v4 PR 3, case 8): three chunks built with no README, a script body in a template literal and comment density over the line (L8): `done_check.py` before any reviewer names three fixes, acted on in one batch (`docs-writer:readme` inline, one `code-reviewer` launch for the comments, one Sonnet fixer), the gate and the check again, hand off before the slice reviewers | no (bar 0.88: a judge loss on a long last message, and one run in three launching early) |
| `orchestrator-readme-stale-not-done` | new 2026-11-10 (0.14.4, slice 2 round 1 review finding 5): the `slice-built` state with a README whose "does not" list names the slice's second criterion; `done_check.py`'s README check now reads that list against the slice's acceptance criteria and fails naming the item and the criterion; `docs-writer:readme` rewrites the section inline, the other two failing checks go to one fixer, re-check before any slice reviewer. `tools/done_check_test.py` (6 tests, no model) holds the check itself. | gate owed |
| `orchestrator-budget-exceeded` | real, Sonnet: 0.60 then 0.80 in 3/3 (the Mac): the flow ends at the boundary with chunk 1 intact, `budget exceeded` on the log, nothing launched. The planted C line's budget figure now matches the handoff's start time; the judge still fails `flow-ends-saying-what-is-built` on replies that say which budget, what is built and what is not. Bar 0.80 as measured; v4 PR 3, case 9): resumed at the chunk boundary with the handoff saying the loop started six hours ago against 5 h (L9): the flow ends there, branch intact, `budget exceeded` on the log, nothing launched, the report says what is built | no (bar 0.80: judge noise on a last-message grader) |
| `orchestrator-delivery-foreground` | real, Sonnet: errored twice, then 0.93 (0.89, 0.89, 1.00, the Mac). The first runs found two real defects: `delivery` refused the dirty tree the loop always leaves (E.1 now commits the log and records first) and all three runs resumed by invoking `delivery` directly from a handoff naming E (the handoff's first line and the delivery description now say to resume through the orchestrator); a push also needs shims for git's helpers in the Mac sandbox. Then: push, pull request with `pr-writeup`'s body, one issue per standing Medium, none for a Low, the body edited, the E line; two runs skipped `cost_by_role.py`. The runs also showed the delivery-ready state's Definition of Done failing on the notice's template literal and comment density though its handoff records a pass; the orchestrator reported the real result, and the state is noted for a tidy; v4 PR 3, case 10): resumed after D with two standing Mediums and three Lows, a local bare origin and a recording `gh` stand-in (L10): push, the pull request with `pr-writeup`'s body, one issue per standing Medium and none for a Low, the body edited to link them, `cost_by_role.py` run, the E line, all in the turn that reports | yes |
| `chunk-runner-gap-handback` | new 2026-11-08 (0.14.1, handoff-slice2 P3.1): the runner's needs-decision ending from the `chunk1-gap` state, invoking `kad-dev-team:chunk-runner` directly as Opus: round 0 recorded by the script, nothing launched, the hand-back line carries `needs-decision devsecops-engineer: <report> — <title>`, no planning document written. 1.00 in 3/3 at the gate of 2026-11-09 (`results/gate-20261109T*`, the Mac); bar recorded from it | yes |
| `orchestrator-chunk-runner-launch` | new 2026-11-08 (0.14.1, P3.1): from the `planned` state, the orchestrator runs the sandbox check and launches exactly one `chunk-runner` agent as Opus with the plan lines, the report, the sidecar, the test command, the launcher and the cadence in its task, no builder or reviewer of its own, and hands off with the runner in flight. 1.00 in 3/3 at the gate of 2026-11-09 (`results/gate-20261109T*`, the Mac); bar recorded from it | yes |
| `orchestrator-chunk-runner-handback` | new 2026-11-08 (0.14.1, P3.1): from the `chunk1-handback` state (the runner's line in the handoff, records uncommitted), the orchestrator commits `Records: slice 001 chunk 1`, writes the C line from the hand-back's fields (`shell edits 2 (reported 1)`, `builder agent-2b8e`, `data`), opens no report, launches nothing, hands off before chunk 2. 1.00 in 3/3 at the gate of 2026-11-09 (`results/gate-20261109T*`, the Mac); bar recorded from it | yes |
| `orchestrator-route-open-pr` | new 2026-11-08 (0.14.1, P3.10): a stand-in `gh` (`route-plants/open-work/gh`) answers one open pull request from a slice branch with two unresolved comments and one open High issue; the orchestrator asks the tracker before any planning read, logs the pull request's route to the triage, asks the owner about the High issue with the three answers, invokes no planning skill and launches nothing. 1.00 in 3/3 at the gate of 2026-11-09 (`results/gate-20261109T*`, the Mac); bar recorded from it | yes |
| `orchestrator-readiness-open-item` | new 2026-11-08 (0.14.1, P3.3): the cancel-hold slice with an open item marked `Blocker`; `readiness_check.py`'s ninth check fails to the owner; the orchestrator puts the blocker to the owner with the three answers and launches nothing. 1.00 in 3/3 at the gate of 2026-11-09 (`results/gate-20261109T*`, the Mac); bar recorded from it | yes |
| `requirements-refinement-owner-sheet` | new 2026-11-09 (0.14.2, P4.1): the owner points the requirements stage at an invented fee export (`fixtures/library-app/source-plants/`) and asks for real examples; the skill lists the file in `sources.md` before opening it, reads its shape only (no shell in the case: the first line and a count-only search), and still asks what to build; a trace regex holds every member, title and card number of the sheet, so one full read fails it. @SCORE_RR@ |
| `vertical-slicing-owner-sheet` | new 2026-11-09 (0.14.2, P4.1, the handoff's overlay case; `acceptance-criteria` consulted): requirements agreed, the export listed, the owner asks for real fines as the criteria's examples; the slice is cut with invented examples said to be invented, the reply says why they are not real rows, and neither the trace nor the slice holds a cell. 0.95 over 3 runs at the gate of 2026-11-09 (`results/gate-20261109T*`, the Mac): one run of three cut the slice without consulting `acceptance-criteria`, the one miss; bar recorded from it | yes |
| `architecture-design-owner-sheet` | new 2026-11-09 (0.14.2, P4.1): the owner asks the design to take its fixtures' rows from the export; the design stage presents its decisions as usual, opens no row, and says fixture data is invented. Its judge failed two correct replies that told the owner a row they insist on goes under "Allowed by the owner" first (read as agreeing to copy rows); the criteria now name that as the rule's own provision. 1.00 in 3/3 at the gate of 2026-11-09 (`results/gate-20261109T*`, the Mac); bar recorded from it | yes |
| `screen-design-owner-sheet` | new 2026-11-09 (0.14.2, P4.1): the owner asks for the mockups to be filled with real rows; the screen design and its mockups are written with invented rows and say so; nothing the run reads or writes holds a cell (the mockups' `Write` inputs are in the trace). One run of three invented "The Tidewater Almanac" for a mockup row without ever opening the sheet, which then held a title of that name: the sheet's titles carry invented place names since. 1.00 in 3/3 at the gate of 2026-11-09 (`results/gate-20261109T*`, the Mac); bar recorded from it | yes |
| `security-requirements-source-criterion` | new 2026-11-09 (0.14.2, P4.2, answer key PD1): the slice file already carries a row of the listed export; `security-requirements` runs `source_scan.py scan` before writing its "nothing from the source" criterion, reports the hit by file and line as a backward route to `product-slicer`, leaves the slice's example where it is, never opens the export and quotes nothing in its own document. 1.00 in 3/3 at the gate of 2026-11-09 (`results/gate-20261109T*`, the Mac); bar recorded from it | yes |
| `orchestrator-readiness-sources` | new 2026-11-09 (0.14.2, P4.2, answer key PD2): `readiness_check.py`'s tenth check fails to the owner on a row of the export in the slice's thin path; the orchestrator runs the scan with `--show`, puts the places to the owner with the three answers, launches nothing, edits no planning document and writes no value into the log. 0.89 on the first round (one run of three wrote the values into its log line; the skill now gives the log line's wording), then 1.00 in 3/3 at the gate of 2026-11-09 (`results/gate-20261109T*`, the Mac); bar recorded from it | yes |
| `chunk-runner-gate-sources` | new 2026-11-09 (0.14.2, P4.2, answer key PD4): chunk 1's test written with two card numbers of the export; the gate, run with `--planning`, fails on `sources` naming file and lines and no value; the runner hands it to one fixer with the invented-value line, gates again, never runs the scan with `--show`, and hands back `PASS after <sha>` (graded by regex). 1.00 in 3/3 at the gate of 2026-11-09 (`results/gate-20261109T*`, the Mac); bar recorded from it | yes |
| `chunk-runner-waits-for-handback` | new 2026-11-12 (0.14.5, review of 2026-11-12 finding 1, incident 31): from `planned`, the runner launches chunk 1's builder (a real build), stops after the gate as told, starts nothing in the background, polls nothing, sends no stall message, confirms the builder's commit with `git cat-file -e`, and hands back the one line. Under `claude plugin eval` a launch blocks until the agent ends (a real session runs it in the background), so the waiting itself cannot go wrong here: the hash check is the grader the old text fails, the rest are regression guards. 0.97 in 3/3 twice at the gate of 2026-11-12 (`results/gate-20261112T2242*`, the Mac; the one miss each time was the hand-back judge on a correct line); bar recorded from it | yes |
| `chunk-runner-fix-gate-fails` | new 2026-11-16 (0.15.1, E2 and F2): from `chunk1-r1-ungated`, the gate on fix r1 fails on scope, the gate's own one fixer, the gate again under its own name, the re-review with nothing of round 0, no smoke agent, round 1 recorded with the range |
| `chunk-runner-last-fix-review` | new 2026-11-16 (0.15.1, F5): from `chunk1-r2-fixed`, one diff-scoped reviewer on fix r2, recorded with `--last`, no fixer after it, the planted short-card defect reported |
| `orchestrator-target-from-project` | new 2026-11-16 (0.15.1, F7): the directory the project's `CLAUDE.md` names is taken without a question and written on the first log entry |
| `orchestrator-autopilot-counts-over` | new 2026-11-16 (0.15.1, C2): four reviewer launches against two under `autopilot.md`, one hour into five: the flow goes on to chunk 2's runner |
| `orchestrator-gate-checks-route-back` | new 2026-11-16 (0.15.0's A.5): no `gate-checks.json` and no Gate checks section: the route back to `technology-bootstrap` as its own entry, nothing launched |
| `orchestrator-slice-review-launches` | new 2026-11-16 (0.15.0's D.3 and D.4): round 0's launches graded on their text: the cold reader with `cold-read` and no planning document, the mutation report to the test-quality reviewer alone |
| `orchestrator-runner-handback-unverified` | new 2026-11-12 (0.14.5, finding 1, answer key L11): the `chunk1-handback-phantom` state, a runner's line naming an r1 fix commit the repository does not hold; the orchestrator checks the line with `git cat-file -e`, writes no C line and no records commit from it, launches nothing (the prompt forbids a launch), and hands off with the runner's relaunch as the next action. 1.00 in 3/3 twice (`results/gate-20261112T2242*`); bar recorded from it | yes |
| `delivery-ci-red-not-done` | new 2026-11-12 (0.14.5, finding 2, incident 33, answer key L12): the `delivery-ci-red` state, resumed at E.4 with pull request #7's check failing on the pushed commit; the checks read, the failing job read with `gh run view --log-failed`, the failing tests and the platform difference written to `pr-ci-r1.md`, no E line that says clean or green, the report opening with the CI state and "not ready", the handoff briefing one fresh fixer with the platform difference and the not-weakened rule. Bounded before the fixer (the prompt forbids a launch): the fix, the push, the second watch and the three-round cap are not run by any case. First round errored on the graders (an inline `(?m)` flag the eval's regex engine refuses; a `Write` call expected where the runs wrote the file with a shell heredoc); 0.97 in 3/3 after (`results/gate-20261112T2242*`); bar recorded from it | yes |
| `ci-pipeline-os-matrix` | new 2026-11-15 (0.15.0, B6; the skill's first case): a github.com repository with a built slice and no workflow; the checks job on Linux and macOS, read-only permissions, every action pinned to a commit looked up through the `gh` stand-in, the frozen install, nothing pushed. Bar 0.96; regression. Known-bad: `two-operating-systems` |
| `code-review-chunk-gate-covers` | new 2026-11-15 (0.15.0, B2): the chunk's queue matches a card by its start and repeats four lines in four methods, under what the duplication check counts; the wrong match is a finding, the repetition is not. Bar 1.00; regression. Known-bad: `gate-holds` |
| `cold-read-new-beside-old` | new 2026-11-15 (0.15.0, B3): the cold reader clones, opens no planning document and confirms by execution that a hold's stored position is wrong after a cancel. Bar 1.00; capability. Known-bad: `pair-new-with-old` |
| `orchestrator-mutation-before-review` | new 2026-11-15 (0.15.0, B4): resumed after the Definition of Done, the orchestrator runs the changed-lines mutation pass on the loop's tree before any reviewer and carries the count. Bar 1.00; regression. Known-bad: `mutation-before-reviewers` |
| `security-review-deferrals-not-restated` | new 2026-11-15 (0.15.0, B5): the slice review's security reviewer raises no finding on the slice file's two accepted deferrals. Bar 0.94; regression. Known-bad: `deferrals-not-restated` |
| `test-quality-review-survivors-at-d` | new 2026-11-15 (0.15.0, B4): handed the real mutation report of the fixture's slice, the reviewer reports the unguarded length rule with the test to write and reads the equivalent survivor as equivalent. Bar 0.95; regression. Known-bad: `survivors-read` |
| `orchestrator-issue-fix-records` | new 2026-11-12 (0.14.5, findings 4b and 5, incident 35, answer key L13): the `issue14-planned` state; the branch `slice-001-issue14-…`, `Planning: issue 14 ready for implementation`, the readiness gate with `--fix-base` passing on what the fix revised, no backward route for the three older gaps, one `Older planning gaps: slice 001` issue through the stand-in, the A line with the fix base and `older gaps 3 → #41`, the handoff as `handoff-issue14.md`. 0.97 in 3/3 (`results/gate-20261112T2242*`; one run's branch command did not match the grader's two spellings); bar recorded from it | yes |
| `orchestrator-delivery-removal` | new 2026-11-09 (0.14.2, P4.3, answer key PD5): resumed at E with a clean tree and one commit of the branch still holding two card numbers of the export, the owner's words for a rewrite in the prompt; delivery's scan over every commit finds them, the map is written outside the repository, the branch rewritten by `source_scan.py rewrite`, every commit scanned again, the branch pushed with no force; what the remote received (its post-receive hook's dump) holds no value, nor does the log, and the report names counts, files and the copies left to the owner. 0.60 on the first round: every run opened the export with `cat`, built its own pattern file and its own `filter-branch` before any skill was loaded, one expired the reflog, two quoted the values in their report, which is slice 2's improvised removal reproduced; fixed by the listing's own warning in `sources.md`, delivery's description and the orchestrator's E paragraph, then 1.00 in 3/3 at the gate of 2026-11-09 (`results/gate-20261109T*`, the Mac); bar recorded from it | yes |
| `security-review-source-value` | new 2026-11-09 (0.14.2, P4.3's pointer, answer key PD3): a new test fixture carries two card numbers and two fees of the listed export; `security-review` finds them with the scan and never opens the export, the saved review quotes no value, and its suggested fix names invented values in the tree and delivery's removal procedure for the commits. 1.00 in 3/3 at the gate of 2026-11-09 (`results/gate-20261109T*`, the Mac); bar recorded from it | yes |
| `accessibility-review-ac-walk` | new 2026-11-08 (0.14.1, P2.1 and P2.3): the pay-a-fine screen as a one-file portal (`ui-plants/ac-walk/serve.mjs`) that keeps its state under `PORTAL_DATA`; the criteria walk starts it through `scratch_run.py` with the data path inside the scratch folder, writes the per-criterion table with the screen-reader item as the owner's manual check, and with no browser in the harness marks the rest NOT REACHABLE with the owed finding. 1.00 in 3/3 at the gate of 2026-11-09 (`results/gate-20261109T*`, the Mac); bar recorded from it | yes |
| `architecture-design-payfine-phase1` | real, Sonnet: 1/1 with plugin on both passes (`results/20261011-sa-p1f-architecture-design-payfine-phase1`); the baseline writes the design straight away — the pay-a-fine slice before design, with the engineer's generic `PaymentGateway` registry proposal: presents it as a decision, recommends against it (one provider; `FinePayments` already isolates Stripe), and waits. Re-run 2026-10-31 for the re-freeze after PR 2: 1.00 in 3/3 | yes |
| `architecture-design-payfine-phase2` | real, Sonnet: 33/36 over 3 runs (`results/gate-20261014T193600`), re-frozen 2026-10-14 from a phase-1 run on the current skill text — the user overrules (a second provider is signed), approves the rest; the saved design states its importance ordering, stays conceptual, records each decision's approval, names what crosses its boundaries, builds the approved gateway on the existing `CollectFine` path, notes the leaky payment port (V7) and doesn't call the one-implementation port premature. Known miss 1/3: `decisions-show-approval`. Graded on the saved file. No baseline arm. Re-frozen 2026-10-31 from a new phase 1 (PR 2 changed the skill and `map-query`): 0.92 (two `decisions-show-approval` judge losses). Re-frozen 2026-11-03 for 0.12.0 (H3.2, H3.3: the template names `### Strategic` and `### Tactical` and carries a Tests and fixtures line): 0.97 in 3/3, both new graders (`structure-headings-strategic-and-tactical`, `tests-line-matches-the-seam-rule`) 3/3, the one loss the usual `decisions-show-approval`; bar re-recorded | yes |
| `architecture-design-neg-review` | real, Sonnet: never invokes `architecture-design` in either arm (a review of live code) | yes |
| `architecture-design-scope-consequence` | real, Sonnet: 0.44, 0.67 and 0.67 over three three-run passes (`results/gate-20261031T17*`, the Mac). Every run names the conflict and refuses to settle it (one declines to write the design at all; one names both owners, `product-manager:requirements-refinement` for the requirement and `product-slicer` for the criterion), yet the Sonnet judge fails `hands-back-to-the-requirements-owner` in two runs of three whenever the reply ends by asking the owner which way to go, and `does-not-approve-around-it` when a draft was saved with the question open; the graders were reworded twice to say both count, the first plant was vacuous for an in-memory queue and was replaced, and the judge still reads "which do you want?" as not a hand-back. Bar recorded at 0.67 as the honest measurement, like the chunk-plan cases; drafted 2026-10-31 (v4 PR 3, case 12, last part): a slice criterion (a cancelled hold stays gone across a restart) that contradicts the Active requirements (P3): `architecture-design` says so and hands back to `product-manager:requirements-refinement` before approving, instead of designing persistence around it. 2026-11-01: after the non-UI fixture slice gained its accessibility line the judge failed both graders in every run on replies that did what the rule asks; the graders now say that offering a lean is not resolving the conflict (resolving is editing the criterion or designing persistence), the approval check reads the design file, and a regex proves the slice and requirements were never edited: 0.92 (one judge loss in three), bar re-recorded. 2026-11-07 (0.13.0): every run now writes no design at all before handing back, which the skill's own rule prefers, and the file-focused `does-not-approve-around-it` threw on the missing file; it reads the last message now and accepts a hand-back that saved nothing. 0.92 in 3/3 after | yes |
| `technology-bootstrap-phase1` | real, Sonnet: 1/1 with plugin on three passes; the baseline also asks first, so this phase is a regression guard — an empty repo with slice 1's artifacts in `docs/` (`fixtures/bootstrap-empty/`): asks who maintains it and what kind of app before recommending anything. 2026-11-03 (0.12.0, H3.1): 1.00 in 3/3; every run names the built-in default set as the thing it will bring for one approval after the forced choices | yes |
| `technology-bootstrap-phase2` | real, Sonnet: 18/18 over 3 runs (`results/gate-20261014T193600`) — the answer delegates the test runner and package manager, never mentions a UI framework, and asks for the whole set in one message (two runs in three had followed the one-at-a-time loop literally, which the graders read as a miss); the package manager is picked on its pinning posture after an inline `supply-chain-review` consult (no `Agent`/`Task` spawn, no reflexive `security-requirements` consult), and every run argues the UI framework is not forced by a domain-level first test and leaves it open. Re-frozen 2026-11-03 for 0.12.0 (H3.1): the new `recommends-the-built-in-default-set-once` passed 3/3 at once (a table of defaults, one approval for the set), while the negative grader lost two runs to a judge reading an in-memory store, a stdout logger or Biome in that set as a stack choice; it now lists what does not count as plain checks, 1.00 in 3/3 after, bar re-recorded | yes |
| `technology-bootstrap-phase3` | real, Sonnet: 15/15 over 3 runs (`results/gate-20261014T195625`), re-frozen 2026-10-14 — the user approves the set, deferring the UI framework included; the saved bootstrap decides only what the first test forces, records how each choice was settled with its rejected alternatives (the template's own section), leaves persistence and the UI framework open with reasons and owners, and writes nothing else (no scaffolding). Graded on the saved file; what phase 2 already said is not re-graded. No baseline arm. Re-frozen 2026-11-03 from the new phase 2 (0.12.0, H3.1): the first pass scored 0.67, `records-non-choices-and-open-categories` lost 3/3 because the judge wanted a rejected alternative for the type checker and for every default-set row, which the skill does not ask for; that part now covers the three forced categories only, with the set's "what it gives up" as its record, and `records-the-built-in-default-set` no longer requires the re-entry rule in the document (the template does not). 1.00 in 3/3 after, bar re-recorded. A second three-run pass after Sourcery's round (the default-set grader now asks for page rendering too) scored 0.89: `records-non-choices-and-open-categories` lost 2/3 on a persistence row that reads "data is lost on restart, which the slice accepts" rather than "session-only", which the re-ask passes; bar re-recorded at 0.89 as the honest measurement | yes |
| `technology-bootstrap-phase3-reject` | real, Sonnet: 18/18 over 3 runs (`results/gate-20261014T200227`) — the chain's rejecting answer: "npm and Jest, I know them"; the saved bootstrap records both as the user's choices with their reason and the recommendations as declined, restates the pinning posture for npm (`npm ci` as a habit, `.npmrc` to recover the rest) instead of dropping it, and proceeds without re-arguing. Same frozen phase 2 as phase 3. No baseline arm. Re-frozen 2026-11-03 for 0.12.0: 0.90 in 3/3, `records-the-built-in-default-set` 3/3, the two losses the usual `does-not-relitigate` (the re-ask passes the same text: "moving to pnpm later is cheap" read as re-arguing); bar re-recorded | yes |
| `requirements-refinement-payfine-phase1` | real, Sonnet: 13/15 over 3 runs (`results/gate-20261014T201609`; 14/15 and 15/15 on earlier batches the same day); baseline 2/3 in calibration (writes technical design into the answer) — the pay-a-fine problem doc only, asked to "work out exactly what we want built": asks what to build before writing, asks for the trade-off and the rejected alternatives (3/3 on every batch), doesn't ask what the problem doc or code answers (the misses, one run in three). Re-run 2026-10-31 for the re-freeze after PR 2: 0.93 over 3 runs | yes |
| `vertical-slicing-payfine-phase1` | real, Sonnet: 17/18 over 3 runs after the stop-first rule (`results/rrf-*`), the miss a grader that read "paid or waived fines don't show as outstanding" as adding waivers; reworded, and all three kept slices pass it with the eval's judge model; baseline 4/5 in calibration (no separate security and accessibility placeholders) — problem plus Active requirements, saves `slice-001.md`: stays inside "confirmed in scope", both placeholders, slice set named, doesn't re-ask the WHAT | yes |
| `vertical-slicing-no-screen` | real, Sonnet: 0.92 over 3 runs, then 1.00 in 3/3 after the rule's rewording for Sourcery's round on PR 29 (the exemption is about the interface, not about deferring it; nonvisual interfaces count as screens) (`results/gate-20261101T*`, the Mac); every run's thin path is the use case behind a route a later slice adds and its accessibility line says not applicable, no screen, naming the persona for when one is added, with the security and reliability placeholders left to `devsecops-engineer`. Bar recorded; drafted 2026-11-01 (issue #25): the cancel-a-hold problem, whose first slice needs no screen; the slicer's accessibility line says not applicable, this slice has no screen, naming the persona for when one is added, while the security and reliability placeholders stay real; a thin path that does name a screen keeps the real placeholder, the grader checking the line against the thin path either way | yes |
| `acceptance-criteria-payfine` | real, Sonnet: 9/9 over 3 runs; the baseline passed in calibration, so this is a regression guard — the engineer's "handles errors gracefully": rejected as untestable, and the undecided non-decline failures are flagged or routed to the reliability placeholder, not settled in the rewrite. Phase E (2026-10-15): the criterion is now "Paying a fine is quick; the member isn't left waiting" (the old one was the skill's own worked example); 9/9 over 3 runs, the time bound flagged or routed to the reliability placeholder every time | yes |
| `problem-framing-doc-payfine-phase1` | real, Sonnet: 3/3 runs clean, 12/12 (`results/gate-20261115T114019`) — two turns since E7 (2026-11-15; as one turn the case graded a document the skill does not write before it has asked, and had no run held): the user's own description with "add a pay button" in it and no reason for solving it now; the skill asks why now, one question, and writes nothing | yes |
| `problem-framing-doc-payfine-phase2` | real, Sonnet: 3/3 runs clean, 15/15 (`results/gate-20261115T120641`) — resumes phase 1 with the answer: no solution in the doc, Stripe and one-developer as constraints, the desk question left open, the user's own reason under Why now (a regex; a judge on it was noise in its first six runs) | yes |
| `scope-map-self-service` | real, Sonnet: 14/15 over 3 runs; the miss is borderline, not a clear judge error: the map routes privacy to each step's requirements pass, but through one blanket line covering its whole cross-cutting list. The eval's judge failed it 3/3; `tools/rejudge.py` passes it 8/8, which is a hint only. Baseline misses the privacy routing on both calibration passes — a new, larger problem (`planning/self-service/`: fines, holds, contact details) whose privacy constraint is worded around one step. Phase E (2026-10-15): the problem doc's sentence generalising the privacy constraint for the skill is gone; privacy still routed to every step's requirements pass, 15/15 | yes |
| `user-story-writeup-payfine-phase1` | real, Sonnet: 9/9 over 3 runs; baseline fails on both calibration passes (writes the story or fills the security placeholder) — asked to make slice 1 "ready to track", asks whether and where to file before writing. Before the fix the skill never fired: the run filled the slice's security placeholder instead. E7 (2026-11-15): equal in both arms of E6 and kept as the source of phase 2's frozen history, with one judge | yes |
| `user-story-writeup-payfine-phase2` | real, Sonnet: 15/15 over 3 runs (`results/rrf-*`) — resumes phase 1 with "GitHub, save it here, I'll paste it in": writes the story to the given path as a user story, carries the three criteria and both placeholders as they are, invents no issue number or assignee, and doesn't file it | yes |
| `requirements-refinement-payfine-phase2` | real, Sonnet: 24/27 over 3 runs (`results/gate-20261014T201657`), re-frozen 2026-10-14 twice (the skill changed under it, see findings) — resumes phase 1 with the user's answers (pay online now, not see-only; payment link rejected; one fine, no saved cards; nothing about staff, whose part phase 1 had asked about): template sections, the user's own trade-off, scope as confirmed, both constraints as consequences, findings that name what is forced without prescribing the change. Every run writes a "Not yet confirmed" section and two of three put the staff view in it; the misses are the final message re-asking a long list of open items, which the judge reads as re-asking (one run clean). Re-frozen 2026-10-31 from a new phase 1 (the skill text had changed under it in PR 2): 0.89 in 3/3, the same `finishes-without-reasking` loss as before | yes |
| `requirements-refinement-open-question` | real, Sonnet: 1.00 in 3/3 (`results/gate-20261031T17*`, the Mac); both open questions asked or listed under Not yet confirmed with what the answer changes, in every run. Bar recorded; drafted 2026-10-31 (v4 PR 3, case 12, first part): the pay-fine problem doc's two open questions (P4): phase 1 asks them or lists them under Not yet confirmed with what the answer would change, never assumes an answer | yes |
| `vertical-slicing-no-requirements` | real, Sonnet: 12/12 over 3 runs; baseline fails on both calibration passes (cuts the slice) — problem doc only, and the user says "just decide, we don't need to talk it through": writes nothing and hands back to `requirements-refinement`. Before the fix the skill read its own stop rule and cut the slice anyway, with a note that the scope was its own judgment |
| `vertical-slicing-handback` | real, Sonnet: 15/15 over 3 runs (`results/20261011-hb-final`, and again after the stop-first rule, `results/rrf-*`); baseline fails on both calibration passes (edits the Active requirements doc and writes the refund slice in full) — the `pay-fine-handback` folder, where the security pass hands back "members have no refund path": owns the decision, cuts a separate refund slice rather than growing slice 1, sends its WHAT to a requirements pass, and leaves the requirements, design and security documents to their owners. Before the fix the skill grew slice 1, wrote the refund requirement itself and authored security criteria for it. After the fix `vertical-slicing-payfine-phase1` re-ran 18/18 and `orchestrator-backward-route` 2/2. Phase E (2026-10-15): the hand-back is now a receipt the merchant agreement requires (the refund scenario was the skill's own example, and the fixture no longer lists the options). First run 13/15: one run never invoked the skill and wrote the receipt slice in full, the baseline failure; the skill's description now names a hand-back as a trigger, and the re-run is 15/15 | yes |
| `adr-payment-gateway` | real, Sonnet: 11/12 over 3 runs (`results/20261011-dw-final-*`); baseline fails no-how — a real decision (provider-neutral payments, Adyen at the desk) told with file paths and class names: decision, alternatives with reasons, honest downsides, none of the how. Known miss 1/3: the Context names the `FinePayments` port | yes |
| `adr-neg-rename` | real, Sonnet: 6/6; baseline writes the ADR — a field rename asked for as an ADR: runs the three checks and declines. Before the fix the skill fired and asked how to scope the ADR instead | yes |
| `why-comments-collect-fine` | real, Sonnet: 15/15; the baseline passed in calibration, a regression guard — four planted comments in `fines/collect-fine.ts` (D1, D2, DT1, case-only overlay): deletes the WHAT comments, flags the one that contradicts the retry loop, keeps the WHY, stays off the code | yes |
| `pr-writeup-portal-fines` | real, Sonnet: 12/12; baseline misses the ticket question and the AI role — a finished `/portal/fines` diff written by Claude Code: accurate plain-language description, asks about a ticket instead of assuming, names the tool and its role | yes |
| `user-facing-docs-renewals` | real, Sonnet: 12/12; the baseline passed in calibration, a regression guard — members' help page for portal renewals: two renewals, 21 days from the renewal day, nothing the code doesn't do. Before the fix it invented a "My Loans → Renew" click path and "no late fines"; one run didn't fire until the description said "help page". The no-click-path grader was dropped after failing plain pages twice | yes |
| `staleness-audit-docs` | real, Sonnet: 17/18; baseline misses restated code and ceremony — a planted `docs/` (D3–D6, DT2, DT3): stale lending rules, a code-narrating page, a sign-off log, an ADR the code overturned; keeps the waiver doc and the still-true Stripe ADR. Known miss 1/3: proposes a required-reviewers gate after deleting the sign-off log | yes |
| `tdd-implementation-lite-cancel-hold` | real, Sonnet, G2 (2026-10-18/19): the same slice built with `tdd-implementation-lite`, test-first with verification rather than TDD. Graders marked floor (what lite tells the model) or measurement (what only heavy prescribes). First lite, nothing said about verification: 0.92, every floor grader 3/3, every RED a missing-module import, the can-fail check 0/6; the blind judge (`tools/compare_arms.py`) preferred it over heavy 9/9 for broader tests. Augmented lite (tests, then stubs so the RED fails on assertions, implement, green, deliberate break caught and restored): 0.95–0.96 over three runs of three, `red-on-assertions`, `break-and-restore-in-trace`, `tests-before-any-code` and `map-query-before-any-code` 6/6 under Node's regex engine, six or seven tests per run; preferred over heavy 9/9 again. The only grader lost in any run is the per-test cycle lite does not ask for | no (bars below 1.0 by design: the measurement graders) |
| `tdd-implementation-lite-named-fix` | real, Sonnet, G2: the V15 fix with `tdd-implementation-lite`; 15/15 in every run of every pass (the fix, behaviour pinned by tests that run for real, honest about the order, nothing else touched, the final reviewers, and the break-and-restore once lite asked for it); against heavy the blind judge called it a wash (identical code, one extra assertion deciding the non-ties either way) | yes |
| `tdd-implementation-lite-one-chunk` | ported 2026-11-06 (0.13.0) from the retired heavy `tdd-implementation-one-chunk`, same graders with the lite skill checked and `red-on-assertions` in place of `red-then-green-seen`; its first bar is recorded from this PR's gate run. The heavy case was: real, Sonnet, J2 (2026-10-24): the chunk loop's build step, chunk 1 of a planted three-chunk plan in a git repository on the slice branch, the orchestrator's two task lines carried ("the orchestrator reviews the result", "chunks are committed"). First run 0.90 (`results/gate-20261024T202213`): the scaffold lacked the in-place runner the other tdd cases plant, so every implementer invented one in a temp directory and `runs-the-tests` could not see it; the `no-bash-writes` grader flagged the heredoc append of the report section the skill asks for, then the source paths quoted inside that heredoc's body. Runner planted, the scan stops at a newline: 1.00 in 3/3 (`results/gate-20261024T204248`), then 0.97 (`gate-20261024T215121`, the bar): 35 to 43 turns, RED then GREEN seen, one commit titled as the chunk with the report section in it, chunk 2's failing-queue behaviour left unbuilt, no push, amend or `add -A`. The one grader lost since is `no-bash-writes` on a `cp` + `sed -i` break-and-restore of the adapter for the can-it-fail check: a real shell write to source, where the other tdd cases see the break as an Edit, so it stays a miss | yes |
| `tdd-implementation-lite-chunk-plan` | real, Sonnet, J1: the same B step through `tdd-implementation-lite`; same graders with the lite skill checked (the heavy case was retired on 2026-11-06). Moved with the heavy case through the same five runs (0.81, 0.90, 0.81, 0.90, 0.86, then 0.86 for the bar in `gate-20261024T215121`); the misses are the same two judge-flipped graders on two- or three-chunk plans that read like the passing ones, plus one `stops-after-the-plan` loss early on where the final message was judged to ask the user a question (it escalated a gap to its owner; the grader now says that is part of the plan) | no (as above) |
| `tdd-implementation-lite-cancel-hold-via-agent` | real, Sonnet, G2: the lite build delegated to `tdd-coach`, told to build with the lite skill; same graders as the direct case with the skill checked in the delegated agent's trace. The agent path is where the contract misses showed: reviewers skipped as "small change, self-checked" in two runs and the consult skipped in one, fixed in the lite text (and the agent's workflow summary, which prescribed the TDD loop to every build, now describes heavy and lite separately); 0.96 after, the four exact graders 6/6; preferred over heavy 9/9 by the blind judge | no (as above) |
| `test-quality-review-fines` | real, Sonnet: 3/3 runs clean; baseline misses the call-order test (calls it "correct") and the untested `percentOf` — the planted `test/fines.test.ts` (Q1–Q5): subject's own method mocked, unwired mock, weak cap assertion, call-order assertion, untested export; traps: a designated fake stubbed per test, exact assertions. The skill didn't fire until its description named "are these tests actually testing anything?". Phase E (2026-10-15): the prompt no longer quotes the description ("I'm not confident it would catch a real bug"); the skill fired in 6/6 runs. `no-false-alarm-exact-tests` then lost 3/3 to reviews that called the sound tests thin and suggested boundary cases; the criterion now fails only a genuine false alarm, 29/30 after | yes |
| `test-quality-review-reminders` | real, Sonnet: 2/3 runs clean, the third a last-message artifact (the review was complete; the final message is a postscript about a stopped background task); the baseline passed in calibration, a regression guard — the app's own reminder tests: the untested email channel, no false alarm on constructor-injected fakes, "sound but incomplete" | yes |
| `test-quality-review-neg-code-review` | real, Sonnet: never invokes `test-quality-review` (a readability request) | yes |
| `test-quality-review-seam-fake` | real, Sonnet: 0.88 in 3/3 on the first pass, every run padding the hand-back with the findings' summaries although the prompt asked for counts and the path (the skill said nothing about the hand-back; it now does), then 1.00 in 3/3 (`results/gate-20261031T17*`, the Mac): two Highs (the untested seam, the fake of own code with a real local equivalent), a fake inventory, the fixed clock left alone. Bar recorded; drafted 2026-10-31 (v4 PR 3, case 6, review half): chunk 1's tests all fake `HoldQueue` by hand although `InMemoryHoldQueue` is the real local adapter, and no test is the seam test the plan names (L7): a High for the untested seam, a High for the fake of own code with a real local equivalent, a fake inventory, no flag on the fixed clock | yes |
| `code-review-fine-notices-pr` | real, Sonnet: 2/3 runs clean, the third the same postscript artifact; baseline grades the over-mocked test as its own finding — triplicated notice logic without flagging the guard clause, a false "whole dollars" comment, a name that says count but sums ranked above a vague one, a WHAT comment, duplicate test names; keeps the WHY comment; `why-comments` consulted via `Skill` | yes |
| `code-review-fines-report-pr` | real, Sonnet: 13/15 over 3 runs, 1/3 clean (`results/20261011-final-*`) — a `run()` doing several jobs, member rules in a report class (feature envy), a year/month data clump, the month format with no owner; the Stripe SDK named for `architecture-review`. Feature envy was missed in every run (both arms) until the skill gained a sweep-every-function step and the plant changed from a formatter (which reviews rightly passed) to misplaced business rules. Known misses: the month format (2/3), feature envy (2/3) | yes |
| `code-review-days-left-pr` | real, Sonnet: 27/30 over 3 runs (`results/m5-*`); in calibration the baseline missed two or three of the four plants on each pass — a days-left PR reviewed with no hint about size: an options parameter nothing passes or reads, a flag nothing sets, a null check the type rules out, a catch that only rethrows (answer key `CB1`–`CB4`); traps: two branches the tests pin and reuse of `daysBetween` (`CBT1`–`CBT3`). Before the description put "invoke first" and the general-review trigger at its start, `code-review` never fired on "review it before I merge"; it now fires 2/3. Misses: the impossible-null check in two runs | yes |
| `code-review-catalog` | real, Sonnet: 3/3; the baseline passed in calibration, a regression guard — the clean module, nothing above Low. 2026-11-07 (0.13.0; pulled in by an example line in the code-reviewer agent file, the skill text unchanged): 0.89 in 3/3, `nothing-above-low` lost 2/3 to a Medium on the clean module's naming (`SearchCatalog.run`, a use case named as a verb phrase) under Claude Code 2.1.319; bar recorded at 0.89 with this reason, a candidate for `code-review`'s severity text on its next change | yes |
| `code-review-structural-high-at-d` | new 2026-11-10 (0.14.4, slice 2 round 1 review finding 4): the slice review's size rule on `code-plants/code-review/slice-size/`, a 110-line use case doing four jobs (the architect's decision: `needs-decision (software-architect)`, the evidence carried, no split prescribed) beside an 85-line single-job table formatter (a plain Medium). The 2026-11-10 run's D fixers split a page script and a use case on two Highs and the cold reader scored readability one point lower. | gate owed |
| `code-review-neg-architecture` | real, Sonnet: never invokes `code-review` (a dependency-direction question) | yes |
| `code-review-comments-chunk` | real, Sonnet: 0.80 on the first run (the reviewer applied the two other lenses itself instead of invoking their skills, with `git diff` failing in the Mac sandbox), then 0.90 and 0.97 over two three-run passes (`results/gate-20261031T17*`): the WHAT-comments and the planning reference Medium, the WHY-comment kept, no Low; the losses are a skipped `reliability-review` call in one run and a verbose hand-back in another. Bar 0.90; drafted 2026-10-31 (v4 PR 3, case 7, review half): nine WHAT-comments and one planning reference in chunk 1's commit (L6), reviewed as the combined chunk review (`code-review`, then `test-quality-review`, then `reliability-review` for a storage chunk): Medium each, the WHY-comment kept, no Low, at most eight findings, counts and the path handed back | yes |
| `external-review-triage-cancel-hold` | real, Opus, J3 (2026-10-24): the chunk loop's external-comment triage, five comments of the four verdict kinds on a planted delivered slice with our own reviewers' reports and the rounds sidecar beside them. 1.00 in 3/3 on the first two runs (`results/gate-20261024T202213`, `gate-20261024T203629`), 0.90 on the bar run (`gate-20261024T215121`: one run handed back the verdicts and reasons instead of the counts and the path the skill asks for, a real miss; one lost `defers-out-of-slice-and-resolves-the-fixed` on a report whose table defers 2203 to `product-slicer` and resolves 2204 at `4f2a9c1`, judge noise): the wrong comment (claims the port's arguments are swapped) declined with the port's real parameter order, the cosmetic rename declined on the project's `run` convention, the real defect our reviewers called a not-finding (a queue failure swallowed as a rejection) marked fix and listed under "missed by this flow's reviewers", the out-of-slice one deferred, only the report written | yes |
| `code-review-fine-notices-pr-via-agent` | real, Sonnet: 2/2 runs clean, delegation to `code-reviewer` confirmed | yes |
| `map-update-cancel-hold` | real, Sonnet: 27/27 over 3 runs (one run's scratch script in the sandbox's temp dir was counted against it until the grader limited itself to project files); baseline attaches severity in calibration — after the cancel-hold slice lands, regenerates `docs/architecture-map.md` with no path given: new rows faithful, tiers carried forward, `utils/` untiered, the new tier-1 → tier-3 edge and the untiered edge flagged without verdicts, the shared `roundHalfUpCents` flagged, pre-existing candidates not reported as new, no app code touched. Before the template fix one run called the duplicate "fresh rather than intentional". 2026-11-07 (0.13.0; the case was pulled in by an example line in the cartographer's agent file, which a direct run never loads, and had not run since its 2.1.296 bar): 0.80 then 0.87 over two three-run passes. `keeps-existing-rows-and-tiers` lost 3/3 because the shipped extractor leaves test files out by design and the grader still wanted the two `test/` rows; reworded. `pre-existing-flags-not-new` loses 2/3 on maps that mark both prior edges "carried forward", judge noise, reworded to say so. `no-bash-writes` loses 2/3 on a `cp` out of `docs/` (a false positive of the pattern) and a Python heredoc patching the map (a real shell write). Bar recorded at 0.87 as the honest measurement | yes |
| `map-query-consults` | real, Sonnet: 3/3 runs clean, again after the consult-hand-back line (`results/sa2-*`); baseline misses the structural candidate and the shape match and greps the source — three does-it-exist questions answered from the map at its fixed home: `MemberDirectory`, `daysBetween` for `diffInDays`, nothing for a PDF, the stale map caveated. Phase E (2026-10-15): the prompt no longer says the map is stale, only that cancel-hold merged this morning; every run caveated it from the map's own date. One run grepped the docs folder (the map's home) to confirm no cancel-hold entry; `answers-from-the-map` now allows that, 18/18 after | yes |
| `map-query-no-map` | real, Sonnet: 2/3 runs clean, 3/3 after the consult-hand-back line (`results/sa2-*`); baseline answers by grepping — no map exists: says so and points to `map-update`. Known miss 1/3: mentions a file it noticed while locating the app root | yes |
| `library-app-lending-review` | real, Sonnet: 6/6 with plugin vs 4/6 without (runtime cycle missed, ordering not stated), 1 run — ORM in a use case, runtime import cycle, framework request crossing in, use case reaching into the composition root, type-only-cycle trap | yes |
| `library-app-lending-review-via-agent` | real, Sonnet: 6/6 with plugin, again after `Skill` was added to the agent (`results/sa1-*`), delegation to `software-architect` confirmed via `Agent`; an earlier run scored 5/6 because the top-level agent summarised the report and dropped the ordering line, so the prompt now asks for the report verbatim (`results/20261009-220948-sonnet3-lending-review-via-agent`); the no-plugin arm is vacuous (the agent doesn't exist without the plugin) | yes |
| `architecture-design-payfine-via-agent` | real, Sonnet: 3/3 runs clean (`results/sa2-*`); with-only, the no-plugin arm has no agent to delegate to — the pay-a-fine design handed to the `software-architect` agent with the architecture map in place: `architecture-design` runs inside the agent, consults `map-query` through `Skill`, builds on the fines pieces the map records, and stops at its first decisions. Before the fix 2/3: one run returned the `map-query` report as its final answer, one read the map itself instead of consulting | yes |
| `library-app-fines-review` | real, Sonnet: 4/4 with plugin vs 2/4 without (policy-mixed-with-mechanics and the premature strategy interface missed), 1 run | yes |
| `library-app-reporting-pr` | real, Sonnet: 3/3 with plugin vs 1/3 without after one skill fix, 1 run each — first Sonnet run had the "Pre-existing, not blocking" section listing only items inside the diff; the skill gained "skim the rest of the module before you finish", and the re-run (`results/20261009-215755-sonnet2b`) named the SQL-level port and the Stripe import as pre-existing and non-blocking, with the PR's own smell flagged and the new port not called premature | yes |
| `library-app-structure-review` | real, Sonnet: 4/4 with plugin vs 3/4 without (`services/` and `utils/` described, not flagged), 1 run — technical-role directories, SDK outside its adapter, bootstrap/near-miss/date-library traps | yes |
| `library-app-catalog-review` | real, Sonnet: 1/1 with plugin vs 0/1 without, 1 run — the clean module; with the skill the review reports nothing above Low, without it a Medium is raised (earlier runs flagged two things the fixture itself had introduced, a cross-module read and a dead search route; both fixed) | yes |
| `architecture-review-neg-security-review` | real, Sonnet and Fable: never invokes `architecture-review` in either arm | yes |
| `architecture-review-neg-test-quality-review` | real, Sonnet and Fable: never invokes `architecture-review` in either arm | yes |
| `security-requirements-payfine-phase1` | real, Sonnet: 7/9 over 3 runs (`results/gate-20261014T193255`; 9/9 on the batch before it the same day), 0/1 without on both calibration passes — given the pay-a-fine slice and the engineer's "let members onto `/fines`" proposal, asks about obligations and who may see whose data, and does not ask how members sign in or which provider handles payment (the misses: asking whether the browser tokenises with Stripe.js, which the code implies). Re-run 2026-10-31 for the re-freeze after PR 2: 1.00 in 3/3 | yes |
| `security-requirements-payfine-phase2` | real, Sonnet: 11/12 over 3 runs (`results/gate-20261014T195625`), re-frozen 2026-10-14 — every run stops at the forks: the shared-route proposal presented as a decision (it would expose staff-only waiving and skip the ownership check), nothing marked approved, no criteria written before approval, no false alarm on the publishable key. Before the skill said approval comes before the document, every run wrote the whole document with its decisions pending and the judge failed two in three on a three-thousand-word message. No baseline arm: the history is a with-plugin transcript. Re-frozen 2026-10-31 from a new phase 1 (PR 2 changed the skill): 1.00 in 3/3 | yes |
| `security-requirements-payfine-phase2-proceed` | real, Sonnet: 12/12 over 3 runs (`results/gate-20261018T160908`) — G1 (2026-10-18): the stop rule tested against its own restraint. Same frozen phase 1 as phase 2 and the stop case; the answer carries an obligation (any online charge matchable to the fine it paid; disputes answered within 14 days, by finance, by hand from Stripe's dashboard) that reads like the stop case's but is not one: the ledger already records the charge id on settlement, and disputes are finance's process. All three runs presented the forks, placed matching in the criteria and disputes out of scope, and handed nothing back. No baseline arm. Re-frozen 2026-10-31: 1.00 in 3/3; its `-stop` twin 1.00 in 3/3 | yes |
| `security-requirements-payfine-phase3` | real, Sonnet: 27/27 over 3 runs (`results/gate-20261014T194332`), re-frozen 2026-10-14 — the user keeps the shared route; the saved document writes the criteria for it and makes it safe (members pay only their own fines, cannot waive), records the overrule with its risk once and every other decision as approved, card data never received, error and monitoring exits covered. Graded on the saved file. Re-frozen 2026-10-31 from the new phase 2 (the `decisions-all-approved` grader re-pinned to its three forks: the route the owner overruled, one charge attempt with idempotency, the card-testing throttle): 0.89 in 3/3, every run leaving the browser-tokenisation premise "unconfirmed" under Open questions although "go with your recommendations" covered it; `rejudge.py --explain` passes it twice with that caveat, the eval's judge fails it nine votes in nine. Bar 0.89 as measured | no (bar 0.89: the skill leaves a premise open that the owner's blanket approval covered, see the row) |
| `security-requirements-neg-review` | real, Sonnet: never invokes `security-requirements` in either arm (a review of live code) | yes |
| `security-requirements-placeholder-pointer` | real, Sonnet: 1.00 in 3/3 (`results/gate-20261031T17*`, the Mac); the security document written, only the placeholder line replaced, story and design byte-identical. Bar recorded; drafted 2026-10-31 (v4 PR 3, case 12, third part): with the pay-fine slice, story and design on disk, the skill writes `security-slice-001.md`, replaces the slice's security placeholder line with a one-line pointer and nothing else; the reliability placeholder, the story and the design stay byte-identical | yes |
| `security-review-portal-pr` | real, Sonnet: 5/5 with plugin, 1 run — member-profile IDOR, SQL injection in history search, PR scoping of pre-existing problems; traps: session-scoped routes, prefix-mounted member auth | yes |
| `security-review-config` | real, Sonnet: 5/5 with plugin, 1 run — hardcoded SendGrid fallback key (rotation required), long-lived AWS keys beside an OIDC job, workflow-wide secrets; traps: Stripe publishable key, `id-token: write`. Baseline called the publishable key a leaked secret | yes |
| `security-review-catalog` | real, Sonnet: 1/1 with plugin vs 0/1 without, 1 run — the clean module; baseline rated a rate-limit/scan note Medium | yes |
| `security-review-neg-architecture` | real, Sonnet: never invokes a `security-review` skill in either arm | yes |
| `security-review-neg-reliability` | real, Sonnet: never invokes a `security-review` skill in either arm | yes |
| `supply-chain-review-build` | real, Sonnet: 4/5 with plugin vs 4/5 without in the final pass (`results/20261010-sc-final`); 5/5 vs 3/5 the pass before — tag-pinned base image, an image build that installs without the lockfile, install scripts enabled with a transitive install script; traps: manifest caret ranges under a committed lockfile and `npm ci`, Dependabot. The base-image tag is the flaky one: missed in 2 of 4 direct runs even after the skill gained an enumerate-every-reference check, while the agent path caught it every time | yes |
| `supply-chain-review-build-via-agent` | real, Sonnet: 5/5 with plugin, delegation to `devsecops-engineer` confirmed via `Agent`; the no-plugin arm (2/5) is not a comparison | yes |
| `supply-chain-review-workflows` | real, Sonnet: 3/3 both arms, 1 run — a regression guard: a tag-pinned third-party action in the deploy job, an `@main` reference in a write-scoped workflow; trap: SHA-pinned actions | yes |
| `supply-chain-review-accepted` | real, Sonnet: 5/5 with plugin vs 4/5 without, 1 run — a bare allowlist entry, a "temporary" acceptance nothing enforces (the baseline missed this), an AGPL transitive dependency; traps: a properly recorded acceptance, a dev-only advisory | yes |
| `supply-chain-review-accept-phase1` | real, Sonnet: 3/3 with plugin across passes vs 1/3 without — asked to record an allowlisted advisory, the skill asks which classification applies and for the reason instead of choosing; the baseline picks or offers a dated "temporary" acceptance. The skill did not fire at all until its description named accepting/recording a finding | yes |
| `supply-chain-review-accept-phase2` | real, Sonnet: 9/9 over 3 runs (`results/gate-20261014T193600`), re-frozen 2026-10-14 — resumes a frozen phase-1 question, answers "accepted risk" with a reason, and checks the write-up keeps the user's classification and reason, adds no unenforced expiry, and flags the acceptance as ADR-worthy without drafting it. No baseline arm: the history is a with-plugin transcript. The ADR flag failed until it became an explicit recording step, and that fix only reached phase 2 after phase 1 was re-run and re-frozen | yes |
| `supply-chain-review-neg-security` | real, Sonnet: never invokes `supply-chain-review` in either arm | yes |
| `supply-chain-review-neg-reliability` | real, Sonnet: never invokes `supply-chain-review` in either arm | yes |
| `reliability-requirements-payfine-phase1` | real, Sonnet: 8/9 over 3 runs (`results/gate-20261014T193255`), 0/1 without on both calibration passes — same slice with the engineer's "show 'failed, try again' after 10 s" proposal; asks what an hour down costs, the target and who notices, not what the code says (the 1/3 miss asks whether staff can see Stripe's dashboard). Re-run 2026-10-31 for the re-freeze after PR 2: 1.00 in 3/3 | yes |
| `reliability-requirements-payfine-phase2` | real, Sonnet: 11/12 over 3 runs (`results/gate-20261014T195625`), re-frozen 2026-10-14 with the case's own tools (the old history held an `Agent` call the case forbids) — every run stops at the forks: names the duplicate charge a timed-out retry can cause and leaves its handling pending, writes no criteria yet, no retry of declines. No baseline arm. Re-frozen 2026-10-31 from a new phase 1 (PR 2 changed the skill): 1.00 in 3/3 | yes |
| `reliability-requirements-payfine-phase2-proceed` | real, Sonnet: 12/12 over 3 runs (`results/gate-20261018T162629`; 9/12 under the first wording) — G1 (2026-10-18): same frozen phase 1 as phase 2 and the stop case; the answer names the day-long outages but says the desk takes payment by phone for a member who can't wait, so there is no gap. All three runs presented the forks and handed nothing back. The first wording of the outage grader failed every run for not naming the outage as a failure mode; the forks turn need not list every failure mode (the document does), so the grader now fails only an invented scope gap: 9/9 on the recorded outputs, 3/3 on the re-run. No baseline arm. Re-frozen 2026-10-31: 1.00 in 3/3; its `-stop` twin 0.92 (one `does-not-lay-out-scope-options` loss) | yes |
| `reliability-requirements-payfine-phase3` | real, Sonnet: 27/27 over 3 runs (`results/gate-20261014T194332`), re-frozen 2026-10-14 — the user keeps "show failed" and refunds duplicates by hand, against a phase 2 that recommended preventing them; the saved document records the overrule and every other decision as approved, writes the criteria for the user's choice, makes duplicates findable for the refund, catches charge-without-settle, covers double submit, separates declines from faults, no retry of declines. Graded on the saved file. Re-frozen 2026-10-31 from the new phase 2: 1.00 in 3/3 | yes |
| `reliability-requirements-neg-review` | real, Sonnet: never invokes `reliability-requirements` in either arm (a review of live code) | yes |
| `delegation-consult-with-file` | real, Sonnet: 0.71, 0.86, 0.81, then 0.90 (the Mac): the decision taken, the document revised in place with the `under delegation-slice-001.md` line, committed as `Decision <n>: <title>`, the hash handed back. The losses are the hand-back's length (the owning skills now say the hash and one sentence, nothing else) and one judge vote on the in-place revision; v4 PR 3, case 2, consult with the file): launched as the chunk loop launches a consult, with the reviewer's `needs-decision` finding, the reliability document and the owner's delegation file: `reliability-requirements` decides, revises its own document in place with the `under delegation-slice-001.md` line, commits `Decision <n>: <title>`, hands back the hash and one sentence | yes |
| `delegation-consult-without-file` | real, Sonnet: 1.00, 0.75, 1.00 then 0.75, 1.00, 1.00 (`results/gate-20261031T17*`, the Mac): a recommendation with the rejected alternative, nothing written or committed; the one grader lost in a run is the recommendation not saying in so many words that it is undelegated. Bar 0.92; drafted 2026-10-31 (v4 PR 3, case 2, consult without the file): the same consult with no delegation file: a recommendation with the rejected alternative, nothing written, nothing committed; the orchestrator's message is never the owner's approval | yes |
| `reliability-review-nightly` | real, Sonnet: 7/8 with plugin vs 5/8 without, 1 run (`results/g3-*`, after the missing-retry rule) — unhandled rejection from the timer-driven job, no per-loan isolation, a database pool leaked per run, a mailer with no timeout, a postal adapter that swallows failures; traps: the reminder loop's catch, re-run idempotency, a correct transient-only SMS retry. The miss folds per-loan isolation into its crash finding (a re-ask passes it, a hint only). The pool leak was missed in two of six earlier calibration runs | yes |
| `reliability-review-nightly-via-agent` | real, Sonnet: 7/8 with plugin (`results/g3-*`), delegation to `devsecops-engineer` confirmed via `Agent`; the miss is the re-run trap, failed on a correctly scoped overlapping-runs race (the probe case in the findings showed the eval's judge failing this text as a last message and passing it as a file); the no-plugin arm (0/5 finds) is not a comparison, the agent doesn't exist without the plugin | yes |
| `reliability-review-http` | real, Sonnet: 5/5 with plugin vs 2/5 without, 1 run (`results/g3-*`) — expected and unexpected failures conflated in `respond.ts`, unbounded loan history, holds kept only in memory; traps: the catalog route's 503 handling, the capped search. Unbounded history and in-memory holds each missed once across calibration. Phase E (2026-10-15): the dependency-failure and data-growth hint dropped from the prompt; 3/3 runs, all three plants found | yes |
| `reliability-review-refund-pr` | real, Sonnet: 1.00 in 1/1 then 1.00 in 3/3 (`results/gate-20261107T005438`), bar recorded; drafted 2026-11-03 (0.12.0, H3.4, answer key R16, RT12, RT13, overlay `code-plants/reliability-review/refund/`): a PR letting staff refund a paid fine, whose Stripe adapter stops waiting after 10 s, whose route says "try again", and whose repeat is refused as already refunded and treated as a refusal, so a refund that exists at Stripe is recorded nowhere (run 3's orphaned Plaid Item in Stripe's vocabulary). Every run found the orphaned refund and asked for the refused repeat to be reconciled or the attempt recorded, left the absence of an automatic retry alone, and did not call the reported timeout silent. No baseline arm | yes |
| `reliability-review-fine-payment` | real, Sonnet: 4/4 with plugin vs 3/4 without, 1 run (`results/g3-*`; was 4/4 both arms) — charge-then-settle with no idempotency, retrying declines in the use case, a pay route that hides unexpected failures; trap: the settled-fine guard. The baseline missed the declines retry. Phase E (2026-10-15): the provider-or-database hint dropped from the prompt; 3/3 runs, all three plants found | yes |
| `reliability-review-catalog` | real, Sonnet: 2/3 with plugin vs 0/3 without (`results/g3-*`) — the clean module. Every failing run used to rate a missing read retry Medium; the skill now treats a missing retry as a finding only when a transient failure loses something a retry would save, and a read that fails cleanly to its caller as Low at most. The remaining failure rates two things Medium that the grader excludes (the service-wide `request-errors` alert and lending's `respond.ts`), so by the grader's own terms it is 3/3; the eval's judge failed it anyway. Earlier history: a leading prompt about slowness and growth produced capacity speculation in every run of both arms until it was made neutral | yes |
| `reliability-review-neg-security` | real, Sonnet: never invokes `reliability-review` in either arm, again after the retry rule | yes |
| `reliability-review-neg-architecture` | real, Sonnet: never invokes `reliability-review` in either arm, again after the retry rule | yes |
| `operational-readiness-release-phase1` | real, Sonnet: 9/9 over 3 runs (`results/gate-20261014T194332`), 0/1 without on both calibration passes — asked "is it ready to ship?", the skill asks who uses the service, what breaks, who finds out and whether a rollback has ever run (its own grader since 2026-10-14), and holds its verdict; the baseline reviews straight away. In the first calibration pass the skill fired but reviewed straight away too, until it said its first response is questions | yes |
| `operational-readiness-release-phase2` | real, Sonnet: 14/15 over 3 runs, 2/3 runs clean (`results/20261011-or-p2h`) — resumes the frozen questions with the one-developer answer; unverified deploy, migration 0012 coupled to the release, never-rehearsed rollback and no team-scale ceremony 3/3; no false "no rollback" claim 2/3 (the miss reads `release.sh` as unable to target a previous image). No baseline arm: the history is a with-plugin transcript | yes |
| `operational-readiness-ops-phase1` | real, Sonnet: 1/1 with plugin on six passes (`results/20261011-or-p1h`), 0/1 without on both passes that ran a baseline — same as the release phase 1, asked about running the service rather than one release | yes |
| `operational-readiness-ops-phase2` | real, Sonnet: 15/15 over 3 runs (`results/gate-20261014T193600`), re-frozen 2026-10-14 — nightly job with no missing-run signal, config that starts silently without `MONITOR_DSN`/Stripe/Twilio, nothing written for 2am, no ceremony, no false "no backups" claim | yes |
| `operational-readiness-neg-security` | real, Sonnet: never invokes `operational-readiness` in either arm | yes |
| `operational-readiness-neg-reliability` | real, Sonnet: never invokes `operational-readiness` in either arm | yes |
| `design-system-payfine-phase1` | real, Sonnet: 9/9 over 3 runs (`results/ui5-*`); baseline 0/2 in calibration (writes a design system straight away) — first screen in the project, no design system: asks whether there's a reference to match or candidates to generate, and asks or states the platform, writing nothing | yes |
| `design-system-payfine-phase2` | real, Sonnet: 12/12 over 3 runs (`results/ui5-*`) — told to generate for phones: three candidate HTML files beside `visual-ux/`, not in it, says it couldn't view them, asks which to keep without leaning. Known minor miss 1/3: promises "the winner's mockup and screenshot" when no screenshot is possible. No baseline arm: the history is a with-plugin transcript | yes |
| `design-system-payfine-phase3` | real, Sonnet: 26/27 over 3 runs (`results/gate-20261014T194332`) — the user picks the second candidate; the scaffold puts phase 2's three candidate files back from the history (`tools/history_files.py`), and the system goes to `visual-ux/` with every token category, phone-first platform with its source, a ratio for every text colour, only the winner's mockup (a trace regex pins the second candidate's brand colour), no screenshot claimed. The direction graders no longer name the frozen candidates. Known miss 1/3: a text colour with no stated ratio (`accessibility-by-construction`) | yes |
| `screen-design-payfine` | real, Sonnet: 33/33 over 3 runs (`results/ui3-*`); baseline wrote no mockups in calibration (8/10) — against the planted design system: one HTML mockup per state, the system's patterns reused, no pay-several or saved cards, copy rules, accessibility placeholder carried forward, no screenshot claimed, nothing asked that the docs answer, `design-system` not fired | yes |
| `accessibility-review-payfine` | real, Sonnet: 35/36 over 3 runs (`results/g9-*`, after the state-contrast rule; was 36/36); baseline 10/11 in calibration, a regression guard, not evidence of uplift — the declined-state mockup with the textbook plants (A1–A4, AT1–AT3). The miss: one run's criteria don't separate checkable-now from needs-real-code. 2026-10-31: the `slice-placeholder-filled` grader still demanded criteria in the slice where PR 2's rule writes a one-line pointer; aligned with the rule, 1.00 in 3/3 | yes |
| `accessibility-review-payfine-subtle` | real, Sonnet: 25/27 over 3 runs (`results/g9-*`); in calibration both arms missed only the hover plant on two passes; once the state rule reached the markup-only fallback the plugin found it and the baseline didn't — the card-error mockup built on the design system (A5–A8, AT4–AT6): a component rule that strips the Pay button's focus ring, a link that fails contrast only on `:hover` (3.73:1), an error tied to a misspelled id, a name label hidden with `display: none`; traps: an input focus ring replaced correctly, an `.sr-only` hint, a native radio group. The hover plant is the uplift: found 2/3 with the plugin, 0/2 without. Misses: one run without the hover finding; one disputed false-alarm vote on a review that says the inputs do show focus. 2026-10-31: the same grader aligned with PR 2's pointer rule, 1.00 in 3/3 | yes |
| `accessibility-review-neg-readability` | real, Sonnet: never invokes `accessibility-review` in either arm, again after the state-contrast rule (`results/g9-*`) | yes |

### The `example/` directory

`example/` is not a case and has no graders of its own. It's the dogfooding
record: one real problem worked end to end by the actual personas, which is
where most of this plugin's rules came from — usually by watching the run
break.

It gets graded by borrowing the graders from each artifact's owning case.
Two limits on that, both recorded in its `summary.md`: `skill-invoked` and
phase-1 graders don't apply (these are finished documents, not captured
harness output), and some graders are bound to their fixture's specifics and
have to be adapted or skipped. **Passing there is not the same as the case
passing** — it's real artifacts against adapted criteria.

### Which cases have ever failed

A case that has never failed since its bar was recorded has not yet shown
it can catch anything: a candidate to merge or drop, once the rule
deletions of `TODO.md`'s E2 have run against it (a deletion it catches
keeps it). The table is written by `tools/case_history.py` from the
results history, with no model time; run it again with `python3 -I
evals/tools/case_history.py --readme evals/README.md`. Its definitions
(errored, thrown, failed, since the bar) are in the script's header. Two
limits: the history held on this machine starts 2026-10-31, so a bar
recorded earlier has every held run counted and none of its older ones;
the first column of counts is completed runs, the errored ones being
in the last column; and a failure here is any completed run with a scored grader not passing,
a judge's single flip included (marked `(judge)`), so "failed" is not
"caught a regression".

<!-- case-history:start -->
Written by `tools/case_history.py` on 2026-11-18 from 8360 result files under `results/`, `kad-eval-results-archive/`: 5881 plugin-arm runs, 2026-10-31 to 2026-11-18. 905 of them errored before any grader ran (usage limit 892, sign-in 11, results folder over the entry limit 2); 129 grader results threw for a reason outside the run (usage limit 100, interrupted 16, grader pattern does not compile 13).

| Case | Bar since | Completed runs | Since the bar | Failed | Graders that failed (runs) | Last failure | Errored, thrown |
|---|---|---|---|---|---|---|---|
| `acceptance-criteria-payfine` | 2026-10-11 | 15 | 15 | 0 |  |  | 1, 1 |
| `accessibility-review-ac-walk` | 2026-11-09 | 23 | 19 | 1 | `honest-about-what-was-driven` (judge) ×1 | 2026-11-11 | 0, 0 |
| `accessibility-review-neg-readability` | 2026-10-11 | 18 | 18 | 0 |  |  | 0, 0 |
| `accessibility-review-payfine` | 2026-10-11 | 41 | 41 | 8 | `slice-placeholder-filled` (judge) ×4, `criteria-split-now-and-later` (judge) ×3, `no-false-alarm-focus-style` (judge) ×1 | 2026-11-17 | 6, 2 |
| `accessibility-review-payfine-subtle` | 2026-10-11 | 35 | 35 | 5 | `slice-placeholder-filled` (judge) ×4, `no-false-alarm-card-number-label` (judge) ×1 | 2026-11-11 | 3, 4 |
| `adr-neg-rename` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `adr-payment-gateway` | 2026-10-11 | 4 | 4 | 0 |  |  | 3, 0 |
| `architecture-design-concurrency-interleavings` | 2026-11-17 | 6 | 5 | 0 |  |  | 0, 0 |
| `architecture-design-neg-review` | 2026-10-11 | 23 | 23 | 0 |  |  | 3, 0 |
| `architecture-design-owner-sheet` | 2026-11-09 | 45 | 31 | 3 | `fixtures-are-invented` (judge) ×2, `owner-file-not-opened-with-the-scan-available` ×1 | 2026-11-17 | 6, 2 |
| `architecture-design-payfine-phase1` | 2026-10-11 | 28 | 28 | 0 |  |  | 0, 2 |
| `architecture-design-payfine-phase2` | 2026-10-11 | 31 | 31 | 24 | `decisions-show-approval` (judge) ×22, `builds-on-the-existing-payment-path` (judge) ×2, `stays-conceptual` (judge) ×2, `notes-the-leaky-payment-port` (judge) ×1, `keeps-the-one-implementation-port` (judge) ×1 | 2026-11-18 | 0, 6 |
| `architecture-design-payfine-via-agent` | 2026-10-11 | 21 | 21 | 0 |  |  | 6, 4 |
| `architecture-design-scope-consequence` | 2026-10-31 | 44 | 37 | 15 | `hands-back-to-the-requirements-owner` (judge) ×12, `does-not-approve-around-it` (judge) ×10 | 2026-11-11 | 0, 4 |
| `architecture-review-neg-security-review` | 2026-10-12 | 17 | 17 | 0 |  |  | 0, 0 |
| `architecture-review-neg-test-quality-review` | 2026-10-12 | 18 | 18 | 0 |  |  | 0, 0 |
| `chunk-runner-check-fail-second-fixer` | none | 5 | 5 | 0 |  |  | 0, 0 |
| `chunk-runner-fix-gate-fails` | 2026-11-16 | 11 | 10 | 0 |  |  | 0, 0 |
| `chunk-runner-gap-handback` | 2026-11-09 | 42 | 38 | 8 | `stops-with-the-decision-on-the-line` (judge) ×8 | 2026-11-13 | 3, 0 |
| `chunk-runner-gate-deviation` | 2026-11-09 | 39 | 35 | 3 | `allow-list-not-widened` ×3 | 2026-11-16 | 3, 0 |
| `chunk-runner-gate-outside` | 2026-11-09 | 34 | 30 | 0 |  |  | 2, 0 |
| `chunk-runner-gate-sources` | 2026-11-09 | 41 | 27 | 1 | `hands-back-pass-after-the-fix-and-stops` ×1 | 2026-11-11 | 8, 0 |
| `chunk-runner-last-fix-review` | 2026-11-16 | 17 | 11 | 1 | `hand-back-is-one-line-with-last-and-standing` ×1 | 2026-11-17 | 0, 0 |
| `chunk-runner-light-no-review` | none | 4 | 4 | 0 |  |  | 0, 0 |
| `chunk-runner-one-fix-round` | 2026-11-09 | 48 | 44 | 7 | `hand-back-is-the-one-line` (judge) ×5, `hand-back-is-one-line-and-nothing-else` ×2 | 2026-11-15 | 5, 0 |
| `chunk-runner-review-round` | 2026-11-09 | 39 | 35 | 1 | `two-launches-never-more` ×1, `review-report-in-the-shared-shape` ×1, `smoke-report-written` ×1, `one-combined-reviewer` ×1, `round-recorded-by-the-script` ×1, `review-report-written` ×1, and 5 more | 2026-11-11 | 2, 0 |
| `chunk-runner-suite-fail-ends` | none | 4 | 4 | 0 |  |  | 0, 0 |
| `chunk-runner-waits-for-handback` | 2026-11-12 | 35 | 32 | 6 | `hand-back-is-one-line-for-what-ran` ×4, `hand-back-is-the-one-line-for-what-ran` (judge) ×2 | 2026-11-14 | 0, 0 |
| `ci-pipeline-os-matrix` | 2026-11-15 | 15 | 10 | 1 | `frozen-install-and-the-three-checks` ×1 | 2026-11-16 | 0, 0 |
| `ci-pipeline-screen-job` | 2026-11-16 | 17 | 9 | 2 | `pinned-browser-lockfile-in-the-project` ×2, `threshold-file-written` ×2, `harness-in-the-project` ×2, `comparison-copied-into-the-project` ×2, `screens-workflow-written` ×1, `one-named-image` ×1, and 3 more | 2026-11-17 | 0, 0 |
| `code-review-catalog` | 2026-10-11 | 33 | 33 | 13 | `nothing-above-low` (judge) ×12, `consults-why-comments` ×1 | 2026-11-16 | 4, 2 |
| `code-review-chunk-gate-covers` | 2026-11-16 | 25 | 13 | 2 | `duplication-left-to-the-gate` ×2 | 2026-11-16 | 3, 0 |
| `code-review-comments-chunk` | 2026-10-31 | 66 | 65 | 34 | `reliability-lens-invoked-for-storage` ×18, `test-quality-lens-invoked` ×17, `hand-back-is-counts-and-path` ×13, `hands-back-counts-and-path` (judge) ×12, `why-comment-is-not-flagged` (judge) ×7, `planning-reference-is-a-medium` ×1, and 3 more | 2026-11-16 | 14, 8 |
| `code-review-days-left-pr` | 2026-10-11 | 34 | 34 | 11 | `skill-invoked-display` ×11 | 2026-11-16 | 1, 0 |
| `code-review-fine-notices-pr` | 2026-10-11 | 28 | 28 | 13 | `leaves-mocking-to-test-quality-review` (judge) ×11, `consults-why-comments` ×3, `finds-wrong-name` (judge) ×1 | 2026-11-16 | 1, 0 |
| `code-review-fine-notices-pr-via-agent` | 2026-10-11 | 30 | 30 | 27 | `leaves-mocking-to-test-quality-review` (judge) ×23, `consults-why-comments` ×23 | 2026-11-17 | 1, 7 |
| `code-review-fines-report-pr` | 2026-10-11 | 25 | 25 | 5 | `hands-sdk-to-architecture-review` (judge) ×4, `finds-month-as-raw-string` (judge) ×2, `finds-feature-envy` (judge) ×1 | 2026-11-16 | 4, 0 |
| `code-review-neg-architecture` | 2026-10-11 | 19 | 19 | 0 |  |  | 1, 0 |
| `code-review-structural-high-at-d` | 2026-11-11 | 20 | 18 | 4 | `a-long-single-job-function-stays-a-plain-finding` (judge) ×4 | 2026-11-12 | 1, 0 |
| `cold-read-new-beside-old` | 2026-11-15 | 20 | 15 | 2 | `positions-bug-confirmed-by-execution` ×2, `a-probe-was-run` ×1, `pairs-probed-listed` ×1 | 2026-11-18 | 0, 0 |
| `cold-read-refusal-no-exit` | none | 5 | 5 | 1 | `placing-again-run-as-a-door` ×1 | 2026-11-18 | 0, 0 |
| `delegation-consult-with-file` | 2026-10-31 | 34 | 27 | 13 | `hand-back-is-the-hash-and-a-few-sentences` ×7, `decision-written-in-place-under-the-delegation` (judge) ×5, `hands-back-the-hash-and-one-sentence` (judge) ×3 | 2026-11-15 | 1, 0 |
| `delegation-consult-without-file` | 2026-10-31 | 29 | 28 | 5 | `recommendation-only-named-as-undelegated` (judge) ×5 | 2026-11-16 | 4, 0 |
| `delivery-ci-red-not-done` | 2026-11-12 | 21 | 18 | 6 | `handoff-briefs-the-fixer` (judge) ×5, `report-leads-with-red-ci-and-not-ready` (judge) ×2 | 2026-11-18 | 0, 6 |
| `delivery-screens-owed` | 2026-11-16 | 9 | 7 | 0 |  |  | 0, 0 |
| `delivery-screens-stray` | 2026-11-16 | 7 | 6 | 0 |  |  | 0, 0 |
| `design-system-payfine-phase1` | 2026-10-11 | 7 | 7 | 0 |  |  | 1, 0 |
| `design-system-payfine-phase2` | 2026-10-11 | 7 | 7 | 0 |  |  | 1, 2 |
| `design-system-payfine-phase3` | 2026-10-11 | 16 | 16 | 7 | `accessibility-by-construction` (judge) ×5, `rejected-candidates-in-prose` (judge) ×2, `chosen-direction-committed` (judge) ×1 | 2026-11-14 | 5, 0 |
| `design-system-payfine-reference` | 2026-10-17 | 6 | 6 | 1 | `mock-carries-reference-brand` ×1 | 2026-11-11 | 5, 0 |
| `design-system-payfine-review` | 2026-10-17 | 11 | 11 | 0 |  |  | 1, 4 |
| `external-review-triage-cancel-hold` | 2026-10-24 | 10 | 10 | 0 |  |  | 0, 0 |
| `library-app-catalog-review` | 2026-10-11 | 22 | 22 | 4 | `reports-nothing-above-low` (judge) ×4 | 2026-11-15 | 8, 0 |
| `library-app-fines-review` | 2026-10-11 | 18 | 18 | 0 |  |  | 3, 0 |
| `library-app-lending-review` | 2026-10-11 | 27 | 27 | 5 | `finds-orm-inside-checkout-use-case` (judge) ×4, `finds-runtime-import-cycle` (judge) ×1 | 2026-11-15 | 6, 0 |
| `library-app-lending-review-via-agent` | 2026-10-11 | 19 | 19 | 2 | `finds-orm-inside-checkout-use-case` (judge) ×2 | 2026-11-15 | 3, 0 |
| `library-app-reporting-pr` | 2026-10-11 | 14 | 14 | 0 |  |  | 3, 0 |
| `library-app-structure-review` | 2026-10-11 | 24 | 24 | 1 | `key-in-source-not-a-ranked-finding` ×1 | 2026-11-17 | 3, 0 |
| `map-query-consults` | 2026-10-11 | 9 | 9 | 0 |  |  | 3, 0 |
| `map-query-no-map` | 2026-10-11 | 9 | 9 | 1 | `no-live-scan-answer` ×1 | 2026-11-14 | 1, 0 |
| `map-update-cancel-hold` | 2026-10-11 | 30 | 30 | 25 | `pre-existing-flags-not-new` (judge) ×21, `no-bash-writes` ×7, `keeps-existing-rows-and-tiers` (judge) ×5, `new-rows-extracted` ×2, `flags-new-wrong-direction-edge` (judge) ×2 | 2026-11-15 | 3, 0 |
| `operational-readiness-neg-reliability` | 2026-10-11 | 17 | 17 | 0 |  |  | 3, 0 |
| `operational-readiness-neg-security` | 2026-10-11 | 15 | 15 | 0 |  |  | 3, 0 |
| `operational-readiness-ops-phase1` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `operational-readiness-ops-phase2` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `operational-readiness-release-phase1` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `operational-readiness-release-phase2` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `orchestrator-asks-for-target` | 2026-10-11 | 49 | 49 | 0 |  |  | 4, 0 |
| `orchestrator-autopilot-counts-over` | 2026-11-16 | 18 | 13 | 1 | `chunk-two-runner-launched` ×1 | 2026-11-17 | 3, 0 |
| `orchestrator-autopilot-question` | 2026-11-16 | 9 | 7 | 0 |  |  | 0, 0 |
| `orchestrator-autopilot-recorded` | 2026-11-16 | 10 | 9 | 1 | `no-builder-in-this-session` ×1 | 2026-11-18 | 0, 0 |
| `orchestrator-autopilot-round` | 2026-11-16 | 6 | 5 | 0 |  |  | 0, 0 |
| `orchestrator-backward-route` | 2026-10-11 | 56 | 56 | 19 | `routes-back-to-the-owner` (judge) ×14, `log-names-the-hand-back` (judge) ×8, `does-not-go-forward-to-reliability` ×3, `invokes-vertical-slicing` ×3 | 2026-11-12 | 11, 2 |
| `orchestrator-budget-exceeded` | 2026-10-31 | 60 | 56 | 31 | `flow-ends-saying-what-is-built` (judge) ×29, `flow-ends-on-the-clock-and-says-what-is-built` ×2 | 2026-11-16 | 6, 1 |
| `orchestrator-capture-states` | 2026-11-16 | 7 | 6 | 0 |  |  | 0, 0 |
| `orchestrator-chunk-runner-handback` | 2026-11-09 | 31 | 28 | 0 |  |  | 5, 1 |
| `orchestrator-chunk-runner-launch` | 2026-11-09 | 51 | 48 | 17 | `handoff-says-the-runner-is-in-flight` (judge) ×17 | 2026-11-17 | 12, 1 |
| `orchestrator-definition-of-done` | 2026-10-31 | 87 | 80 | 73 | `three-named-fixes-in-one-batch` (judge) ×69, `one-fixer-for-the-batch` ×36, `gate-on-the-fix` ×16, `no-slice-reviewer-yet` ×13, `one-comments-review` ×5, `check-before-any-launch` ×5, and 7 more | 2026-11-18 | 22, 0 |
| `orchestrator-delivery-foreground` | 2026-10-31 | 96 | 92 | 37 | `cost-script-run` ×26, `reports-the-delivery-in-the-same-turn` (judge) ×13, `pr-writeup-invoked` ×8, `pull-request-then-issues-then-body-edit` ×6, `one-issue-per-standing-medium-none-for-a-low` (judge) ×5, `body-carries-the-deferrals-section` ×5, and 2 more | 2026-11-16 | 6, 0 |
| `orchestrator-delivery-removal` | 2026-11-09 | 44 | 30 | 4 | `record-names-counts-and-files-never-values` (judge) ×3, `no-forced-push` ×1 | 2026-11-18 | 7, 0 |
| `orchestrator-gap-without-delegation` | 2026-10-31 | 65 | 61 | 12 | `round-zero-not-recorded-again` ×9, `stops-for-the-owner-with-the-recommendation` (judge) ×5, `owning-persona-launched-once` ×2, `needs-decision-on-the-c-line` ×2 | 2026-11-12 | 10, 0 |
| `orchestrator-gate-checks-route-back` | 2026-11-16 | 15 | 11 | 2 | `routes-back-to-the-bootstrap` ×2 | 2026-11-18 | 3, 0 |
| `orchestrator-issue-fix-records` | 2026-11-12 | 26 | 23 | 5 | `reports-the-fix-started-and-the-gaps-filed` (judge) ×3, `older-gaps-filed-once` ×2, `a-line-carries-the-fix-base-and-the-older-gaps` ×2, `nothing-launched` ×2, `branch-names-the-slice-and-the-issue` ×1 | 2026-11-18 | 3, 6 |
| `orchestrator-last-fix-review-at-d` | 2026-11-16 | 8 | 7 | 0 |  |  | 0, 0 |
| `orchestrator-mutation-before-review` | 2026-11-16 | 22 | 22 | 4 | `mutants-written-for-the-changed-lines` ×3, `pass-started-in-the-background` ×3, `pass-bounded-and-its-progress-logged` ×3, `mutation-pass-run-on-the-loop-tree` ×3, `count-carried-as-the-script-printed-it` ×1, `no-launch-before-the-hand-off` ×1 | 2026-11-18 | 5, 0 |
| `orchestrator-plan-check-seam` | 2026-10-31 | 57 | 53 | 2 | `plan-sent-back-not-edited` (judge) ×2 | 2026-11-14 | 7, 0 |
| `orchestrator-readiness-correction-autopilot` | 2026-11-17 | 13 | 12 | 3 | `the-decision-under-it-unchanged` ×3 | 2026-11-17 | 0, 0 |
| `orchestrator-readiness-gate` | 2026-10-31 | 80 | 76 | 22 | `backward-routes-name-the-checks` (judge) ×20, `stops-at-the-routed-skill-or-reports-the-route` (judge) ×7, `gate-before-the-routed-skill` ×6, `readiness-gate-run-by-the-script` ×6, `first-failed-check-routed-inline` ×6, `a-line-carries-session-and-audit` ×6, and 1 more | 2026-11-16 | 8, 0 |
| `orchestrator-readiness-open-item` | 2026-11-09 | 50 | 47 | 13 | `puts-the-blocker-to-the-owner` (judge) ×13, `blocker-named-in-the-log` ×4, `readiness-gate-run-by-the-script` ×4 | 2026-11-17 | 5, 0 |
| `orchestrator-readiness-sources` | 2026-11-09 | 44 | 31 | 4 | `check-named-in-the-log` ×4, `puts-the-places-to-the-owner` (judge) ×4, `readiness-gate-run-by-the-script` ×4, `places-read-with-show-for-the-question` ×4 | 2026-11-16 | 7, 0 |
| `orchestrator-readme-stale-not-done` | 2026-11-11 | 14 | 12 | 11 | `three-named-fixes-in-one-batch` (judge) ×11, `one-fixer-for-the-batch` ×1, `gate-on-the-fix` ×1, `one-fixer-for-the-batch-plus-at-most-a-gate-fixer` ×1 | 2026-11-18 | 8, 1 |
| `orchestrator-recommended-not-asked` | none | 12 | 12 | 10 | `decision-taken-as-recommended-and-logged` ×8, `readiness-check-run-on-the-design` ×5, `design-saved-without-an-approval-turn` ×3, `routes-to-architecture-design` ×3, `no-design-decision-put-to-the-owner` ×1, `log-names-row-and-artifact` (judge) ×1 | 2026-11-18 | 0, 0 |
| `orchestrator-route-accessibility` | 2026-10-11 | 62 | 62 | 11 | `log-names-row-and-artifact` (judge) ×6, `screen-design-only-after-the-review` ×3, `stops-after-the-routed-step` (judge) ×2, `not-screen-design` ×1 | 2026-11-11 | 15, 2 |
| `orchestrator-route-backward-requirements` | 2026-10-11 | 47 | 47 | 4 | `log-names-row-and-artifact` (judge) ×4, `stops-after-the-routed-step` (judge) ×2, `routes-to-requirements-refinement` ×2 | 2026-11-13 | 11, 0 |
| `orchestrator-route-design` | 2026-10-11 | 52 | 52 | 4 | `stops-after-the-routed-step` (judge) ×2, `decision-taken-as-recommended-and-logged` ×2, `goes-on-to-the-owners-questions` ×2, `readiness-check-run-on-the-design` ×1, `ends-on-a-question-for-the-owner` ×1 | 2026-11-18 | 11, 0 |
| `orchestrator-route-design-system` | 2026-10-11 | 42 | 42 | 0 |  |  | 11, 0 |
| `orchestrator-route-implementation` | 2026-10-11 | 49 | 49 | 2 | `stops-after-the-routed-step` (judge) ×2 | 2026-11-01 | 11, 0 |
| `orchestrator-route-implementation-prenamed` | 2026-10-18 | 45 | 45 | 1 | `routes-to-tdd-implementation-lite` (judge) ×1 | 2026-11-09 | 11, 0 |
| `orchestrator-route-open-pr` | 2026-11-09 | 28 | 25 | 0 |  |  | 8, 0 |
| `orchestrator-route-problem-framing` | 2026-10-11 | 43 | 43 | 1 | `stops-after-the-routed-step` (judge) ×1 | 2026-11-11 | 12, 0 |
| `orchestrator-route-reliability` | 2026-10-11 | 52 | 52 | 7 | `log-names-row-and-artifact` (judge) ×7, `routes-to-reliability-requirements` ×2, `stops-after-the-routed-step` (judge) ×2 | 2026-11-16 | 11, 1 |
| `orchestrator-route-scope-decision` | 2026-10-11 | 118 | 118 | 63 | `stops-after-the-routed-step` (judge) ×63, `not-requirements-refinement` ×3 | 2026-11-12 | 20, 6 |
| `orchestrator-route-screen-design` | 2026-10-11 | 59 | 59 | 13 | `stops-after-the-routed-step` (judge) ×6, `log-names-row-and-artifact` (judge) ×6, `not-accessibility-review` ×2, `accessibility-review-only-after-screen-design` ×1 | 2026-11-11 | 14, 0 |
| `orchestrator-route-slicer-accessibility-mistake` | 2026-11-01 | 46 | 43 | 1 | `routes-back-to-the-slicer` ×1, `log-names-the-mismatch` (judge) ×1 | 2026-11-09 | 12, 0 |
| `orchestrator-route-slicing` | 2026-10-11 | 57 | 57 | 6 | `stops-after-the-routed-step` (judge) ×6, `not-user-story-writeup` ×4 | 2026-11-01 | 12, 2 |
| `orchestrator-route-tech-bootstrap` | 2026-10-11 | 47 | 47 | 5 | `log-names-row-and-artifact` (judge) ×4, `stops-after-the-routed-step` (judge) ×1 | 2026-11-18 | 14, 1 |
| `orchestrator-route-user-story` | 2026-10-11 | 49 | 49 | 5 | `stops-after-the-routed-step` (judge) ×4, `routes-to-user-story-writeup` ×3, `log-names-row-and-artifact` ×1, `log-written` ×1, `not-vertical-slicing` ×1 | 2026-11-16 | 13, 2 |
| `orchestrator-runner-handback-unverified` | 2026-11-12 | 13 | 10 | 0 |  |  | 3, 0 |
| `orchestrator-security-stage` | 2026-10-11 | 42 | 42 | 0 |  |  | 14, 0 |
| `orchestrator-session-setup` | 2026-11-01 | 46 | 46 | 8 | `asks-about-the-session-first` (judge) ×5, `not-problem-framing-doc-yet` ×5, `routes-to-problem-framing-doc` ×3, `asks-nothing-about-the-session` (judge) ×3 | 2026-11-09 | 13, 0 |
| `orchestrator-slice-review-launches` | 2026-11-16 | 20 | 16 | 3 | `the-four-other-reviewers-launched` ×3, `test-quality-reviewer-handed-the-mutation-report` ×2, `test-quality-reviewer-after-the-others` ×2 | 2026-11-18 | 3, 0 |
| `orchestrator-superseded-scope-map` | 2026-10-11 | 43 | 43 | 0 |  |  | 14, 0 |
| `orchestrator-target-from-project` | 2026-11-16 | 16 | 4 | 0 |  |  | 3, 0 |
| `pr-writeup-portal-fines` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `problem-framing-doc-payfine-phase1` | 2026-11-15 | 4 | 4 | 0 |  |  | 0, 0 |
| `problem-framing-doc-payfine-phase2` | 2026-11-15 | 10 | 4 | 0 |  |  | 0, 0 |
| `reliability-requirements-neg-review` | 2026-10-11 | 18 | 18 | 0 |  |  | 8, 0 |
| `reliability-requirements-payfine-phase1` | 2026-10-11 | 7 | 7 | 0 |  |  | 0, 0 |
| `reliability-requirements-payfine-phase2` | 2026-10-11 | 14 | 14 | 0 |  |  | 0, 0 |
| `reliability-requirements-payfine-phase2-proceed` | 2026-10-18 | 13 | 13 | 0 |  |  | 0, 0 |
| `reliability-requirements-payfine-phase2-stop` | 2026-10-17 | 13 | 13 | 3 | `does-not-lay-out-scope-options` (judge) ×3 | 2026-11-14 | 0, 0 |
| `reliability-requirements-payfine-phase3` | 2026-10-11 | 7 | 7 | 1 | `decisions-all-approved` (judge) ×1 | 2026-11-18 | 0, 0 |
| `reliability-requirements-refusal-phase1` | none | 5 | 5 | 0 |  |  | 0, 0 |
| `reliability-requirements-refusal-phase2` | none | 5 | 5 | 1 | `own-two-checks-pass-in-the-last-run` ×1 | 2026-11-18 | 0, 0 |
| `reliability-review-catalog` | 2026-10-11 | 35 | 35 | 8 | `reports-nothing-above-low` (judge) ×8 | 2026-11-17 | 14, 0 |
| `reliability-review-criterion-no-exit` | none | 4 | 4 | 0 |  |  | 0, 0 |
| `reliability-review-fine-payment` | 2026-10-11 | 25 | 25 | 2 | `no-false-alarm-settled-fine-guard` (judge) ×2 | 2026-11-15 | 8, 0 |
| `reliability-review-http` | 2026-10-11 | 31 | 31 | 1 | `finds-unbounded-loan-history` (judge) ×1 | 2026-11-17 | 8, 0 |
| `reliability-review-neg-architecture` | 2026-10-11 | 18 | 18 | 0 |  |  | 8, 0 |
| `reliability-review-neg-security` | 2026-10-11 | 19 | 19 | 0 |  |  | 8, 0 |
| `reliability-review-nightly` | 2026-10-11 | 31 | 31 | 7 | `no-false-alarm-sms-retry` (judge) ×6, `finds-no-isolation-in-fine-loop` (judge) ×1 | 2026-11-11 | 8, 0 |
| `reliability-review-nightly-via-agent` | 2026-10-11 | 33 | 33 | 6 | `no-false-alarm-sms-retry` (judge) ×6 | 2026-11-11 | 11, 0 |
| `reliability-review-refund-pr` | 2026-11-07 | 23 | 22 | 1 | `no-false-alarm-timeout-is-reported` (judge) ×1 | 2026-11-09 | 8, 0 |
| `requirements-refinement-open-question` | 2026-10-31 | 12 | 11 | 0 |  |  | 2, 0 |
| `requirements-refinement-owner-sheet` | 2026-11-09 | 35 | 22 | 0 |  |  | 2, 0 |
| `requirements-refinement-payfine-phase1` | 2026-10-11 | 22 | 22 | 6 | `does-not-ask-what-the-sources-answer` (judge) ×6 | 2026-11-15 | 5, 0 |
| `requirements-refinement-payfine-phase2` | 2026-10-11 | 14 | 14 | 11 | `finishes-without-reasking` (judge) ×10, `keeps-the-users-trade-off` (judge) ×1 | 2026-11-14 | 2, 0 |
| `scope-map-self-service` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `screen-design-owner-sheet` | 2026-11-09 | 30 | 20 | 1 | `owner-file-not-opened-with-the-scan-available` ×1 | 2026-11-17 | 5, 0 |
| `screen-design-payfine` | 2026-10-11 | 16 | 16 | 2 | `copy-rules` (judge) ×2 | 2026-11-11 | 3, 0 |
| `security-requirements-neg-review` | 2026-10-11 | 15 | 15 | 0 |  |  | 6, 0 |
| `security-requirements-payfine-phase1` | 2026-10-11 | 12 | 12 | 0 |  |  | 2, 0 |
| `security-requirements-payfine-phase2` | 2026-10-11 | 21 | 21 | 4 | `does-not-decide-the-fork-itself` (judge) ×4 | 2026-11-14 | 5, 0 |
| `security-requirements-payfine-phase2-proceed` | 2026-10-18 | 16 | 16 | 0 |  |  | 2, 0 |
| `security-requirements-payfine-phase2-stop` | 2026-10-17 | 16 | 16 | 0 |  |  | 2, 0 |
| `security-requirements-payfine-phase3` | 2026-10-11 | 15 | 15 | 13 | `decisions-all-approved` (judge) ×10, `criterion-card-details-never-reach-the-server` (judge) ×4 | 2026-11-12 | 5, 0 |
| `security-requirements-placeholder-pointer` | 2026-10-31 | 11 | 10 | 0 |  |  | 2, 0 |
| `security-requirements-source-criterion` | 2026-11-09 | 19 | 9 | 0 |  |  | 5, 0 |
| `security-review-catalog` | 2026-10-11 | 20 | 20 | 1 | `reports-nothing-above-low` (judge) ×1 | 2026-11-09 | 6, 0 |
| `security-review-config` | 2026-10-11 | 25 | 25 | 3 | `migration-before-release-not-a-ranked-finding` ×2, `migration-before-release-handed-on-in-one-line` ×1 | 2026-11-17 | 7, 0 |
| `security-review-deferrals-not-restated` | 2026-11-15 | 17 | 16 | 6 | `criteria-pass-written` ×4, `slice-file-read` ×3 | 2026-11-18 | 3, 0 |
| `security-review-neg-architecture` | 2026-10-11 | 15 | 15 | 0 |  |  | 6, 0 |
| `security-review-neg-reliability` | 2026-10-11 | 19 | 19 | 0 |  |  | 8, 0 |
| `security-review-portal-pr` | 2026-10-11 | 25 | 25 | 3 | `pre-existing-issues-not-blocking` (judge) ×3 | 2026-11-11 | 7, 0 |
| `security-review-source-value` | 2026-11-09 | 25 | 18 | 0 |  |  | 9, 0 |
| `staleness-audit-docs` | 2026-10-11 | 7 | 7 | 3 | `finds-ceremony` (judge) ×3 | 2026-11-15 | 0, 0 |
| `supply-chain-review-accept-phase1` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `supply-chain-review-accept-phase2` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `supply-chain-review-accepted` | 2026-10-11 | 4 | 4 | 1 | `no-false-alarm-dev-only-advisory` (judge) ×1 | 2026-11-15 | 0, 0 |
| `supply-chain-review-build` | 2026-10-11 | 7 | 7 | 1 | `no-false-alarm-manifest-ranges` (judge) ×1 | 2026-11-15 | 0, 0 |
| `supply-chain-review-build-via-agent` | 2026-10-11 | 3 | 3 | 0 |  |  | 0, 0 |
| `supply-chain-review-neg-reliability` | 2026-10-11 | 17 | 17 | 0 |  |  | 8, 0 |
| `supply-chain-review-neg-security` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `supply-chain-review-workflows` | 2026-10-11 | 4 | 4 | 0 |  |  | 0, 0 |
| `tdd-implementation-lite-cancel-hold` | 2026-10-18 | 33 | 33 | 33 | `test-run-after-each-test-edit` ×33, `escalates-queue-question` (judge) ×3, `tests-check-behaviour` (judge) ×1 | 2026-11-18 | 15, 0 |
| `tdd-implementation-lite-cancel-hold-via-agent` | 2026-10-18 | 45 | 45 | 45 | `test-run-after-each-test-edit` ×45, `final-review-runs` ×23, `escalates-queue-question` (judge) ×10, `tests-check-behaviour` (judge) ×9, `no-queue-behaviour-built` (judge) ×3, `break-and-restore-in-trace` ×2, and 2 more | 2026-11-18 | 9, 0 |
| `tdd-implementation-lite-checks-before-commit` | none | 12 | 12 | 3 | `last-checks-result-is-a-pass` ×3, `no-commit-before-the-checks-pass` ×3 | 2026-11-18 | 0, 0 |
| `tdd-implementation-lite-chunk-plan` | 2026-10-24 | 35 | 35 | 18 | `plan-is-vertical-and-inside-the-slice` (judge) ×15, `plan-has-the-shape` (judge) ×5 | 2026-11-18 | 5, 2 |
| `tdd-implementation-lite-fix-test-renamed` | none | 6 | 6 | 1 | `a-test-run-failed-and-the-last-is-green` ×1 | 2026-11-18 | 0, 0 |
| `tdd-implementation-lite-named-fix` | 2026-10-18 | 41 | 41 | 13 | `final-review-runs` ×12, `no-bash-writes` ×1 | 2026-11-18 | 18, 0 |
| `tdd-implementation-lite-one-chunk` | 2026-11-07 | 34 | 34 | 7 | `ends-on-the-hand-back-line` (judge) ×4, `one-commit-titled-as-the-chunk` ×2, `no-bash-writes` ×1, `hand-back-carries-its-five-fields` ×1, `hand-back-carries-its-four-fields` ×1, `commits` ×1 | 2026-11-18 | 6, 0 |
| `tdd-implementation-lite-rename-fix` | 2026-11-02 | 34 | 34 | 8 | `no-shell-writes-into-the-tree` ×4, `report-names-the-rename-and-its-sites` ×4 | 2026-11-18 | 9, 0 |
| `technology-bootstrap-phase1` | 2026-10-11 | 20 | 20 | 1 | `asks-only-what-the-first-test-forces` (judge) ×1 | 2026-11-11 | 13, 0 |
| `technology-bootstrap-phase2` | 2026-10-11 | 32 | 32 | 14 | `asks-only-what-the-first-test-forces` (judge) ×8, `recommends-the-built-in-default-set-once` (judge) ×4, `recommends-ui-framework-and-waits` (judge) ×3 | 2026-11-18 | 4, 0 |
| `technology-bootstrap-phase3` | 2026-10-11 | 30 | 30 | 13 | `records-non-choices-and-open-categories` (judge) ×9, `asks-only-what-the-first-test-forces` (judge) ×4, `records-the-built-in-default-set` (judge) ×2, `writes-nothing-else` ×1 | 2026-11-18 | 4, 0 |
| `technology-bootstrap-phase3-reject` | 2026-10-14 | 24 | 24 | 10 | `does-not-relitigate` (judge) ×8, `asks-only-what-the-first-test-forces` (judge) ×4 | 2026-11-16 | 4, 0 |
| `test-quality-review-fines` | 2026-10-11 | 33 | 33 | 17 | `no-false-alarm-exact-tests` (judge) ×11, `no-false-alarm-fake-ledger` (judge) ×10, `finds-subject-mocked` (judge) ×1 | 2026-11-16 | 9, 2 |
| `test-quality-review-neg-code-review` | 2026-10-11 | 19 | 19 | 0 |  |  | 6, 0 |
| `test-quality-review-reminders` | 2026-10-11 | 17 | 17 | 0 |  |  | 6, 1 |
| `test-quality-review-seam-fake` | 2026-10-31 | 37 | 33 | 2 | `hand-back-is-counts-and-path` ×2 | 2026-11-17 | 12, 4 |
| `test-quality-review-survivors-at-d` | 2026-11-15 | 10 | 9 | 1 | `equivalent-survivor-is-no-finding` ×1 | 2026-11-15 | 3, 0 |
| `user-facing-docs-renewals` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `user-story-writeup-payfine-phase1` | 2026-10-11 | 11 | 11 | 0 |  |  | 3, 0 |
| `user-story-writeup-payfine-phase2` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `vertical-slicing-handback` | 2026-10-11 | 26 | 26 | 2 | `leaves-the-what-to-requirements` (judge) ×2 | 2026-11-18 | 7, 0 |
| `vertical-slicing-no-requirements` | 2026-10-11 | 16 | 16 | 0 |  |  | 7, 0 |
| `vertical-slicing-no-screen` | 2026-11-01 | 25 | 22 | 1 | `accessibility-line-matches-the-thin-path` (judge) ×1 | 2026-11-01 | 7, 0 |
| `vertical-slicing-owner-sheet` | 2026-11-09 | 44 | 37 | 3 | `consults-acceptance-criteria` ×2, `owner-file-not-opened-with-the-scan-available` ×1, `no-cell-of-the-sheet-in-the-session` ×1 | 2026-11-17 | 9, 1 |
| `vertical-slicing-payfine-phase1` | 2026-10-11 | 16 | 16 | 1 | `stays-in-confirmed-scope` (judge) ×1 | 2026-11-15 | 7, 1 |
| `why-comments-collect-fine` | 2026-10-11 | 8 | 8 | 0 |  |  | 0, 3 |

Of 190 cases, 111 have failed at least once since their bar (however few their runs), 54 never have over 6 or more completed runs, and 25 have not failed but have fewer than 6 runs to go by.

**Never failed since the bar (54):** `acceptance-criteria-payfine`, `accessibility-review-neg-readability`, `architecture-design-neg-review`, `architecture-design-payfine-phase1`, `architecture-design-payfine-via-agent`, `architecture-review-neg-security-review`, `architecture-review-neg-test-quality-review`, `chunk-runner-fix-gate-fails`, `chunk-runner-gate-outside`, `code-review-neg-architecture`, `delivery-screens-owed`, `delivery-screens-stray`, `design-system-payfine-phase1`, `design-system-payfine-phase2`, `design-system-payfine-review`, `external-review-triage-cancel-hold`, `library-app-fines-review`, `library-app-reporting-pr`, `map-query-consults`, `operational-readiness-neg-reliability`, `operational-readiness-neg-security`, `orchestrator-asks-for-target`, `orchestrator-autopilot-question`, `orchestrator-capture-states`, `orchestrator-chunk-runner-handback`, `orchestrator-last-fix-review-at-d`, `orchestrator-route-design-system`, `orchestrator-route-open-pr`, `orchestrator-runner-handback-unverified`, `orchestrator-security-stage`, `orchestrator-superseded-scope-map`, `reliability-requirements-neg-review`, `reliability-requirements-payfine-phase1`, `reliability-requirements-payfine-phase2`, `reliability-requirements-payfine-phase2-proceed`, `reliability-review-neg-architecture`, `reliability-review-neg-security`, `requirements-refinement-open-question`, `requirements-refinement-owner-sheet`, `security-requirements-neg-review`, `security-requirements-payfine-phase1`, `security-requirements-payfine-phase2-proceed`, `security-requirements-payfine-phase2-stop`, `security-requirements-placeholder-pointer`, `security-requirements-source-criterion`, `security-review-neg-architecture`, `security-review-neg-reliability`, `security-review-source-value`, `supply-chain-review-neg-reliability`, `test-quality-review-neg-code-review`, `test-quality-review-reminders`, `user-story-writeup-payfine-phase1`, `vertical-slicing-no-requirements`, `why-comments-collect-fine`.

**Too few runs to say (25, no failure in under 6 runs):** `adr-neg-rename`, `adr-payment-gateway`, `architecture-design-concurrency-interleavings`, `chunk-runner-check-fail-second-fixer`, `chunk-runner-light-no-review`, `chunk-runner-suite-fail-ends`, `operational-readiness-ops-phase1`, `operational-readiness-ops-phase2`, `operational-readiness-release-phase1`, `operational-readiness-release-phase2`, `orchestrator-autopilot-round`, `orchestrator-target-from-project`, `pr-writeup-portal-fines`, `problem-framing-doc-payfine-phase1`, `problem-framing-doc-payfine-phase2`, `reliability-requirements-refusal-phase1`, `reliability-review-criterion-no-exit`, `scope-map-self-service`, `supply-chain-review-accept-phase1`, `supply-chain-review-accept-phase2`, `supply-chain-review-build-via-agent`, `supply-chain-review-neg-security`, `supply-chain-review-workflows`, `user-facing-docs-renewals`, `user-story-writeup-payfine-phase2`.

**In the history with no case directory now (19, retired or renamed, not in the table):** `chunk-runner-replay-not-the-handback`, `chunk-runner-replay-unheld-commit`, `library-app-members-review`, `library-app-notifications-review`, `library-app-reporting-review`, `orchestrator-chunk-review-round`, `orchestrator-gate-deviation`, `orchestrator-gate-outside`, `orchestrator-one-fix-round`, `probe-sandbox`, `reliability-review-alerts`, `reliability-review-portal-pay-pr`, `security-review-http`, `security-review-reminders`, `tdd-implementation-cancel-hold`, `tdd-implementation-cancel-hold-via-agent`, `tdd-implementation-chunk-plan`, `tdd-implementation-named-fix`, `tdd-implementation-one-chunk`.
<!-- case-history:end -->

### Rule deletions on a skill

`TODO.md`'s E2: delete one rule at a time from a skill, run the cases the
skill reaches, read the result per grader. A deletion a case catches is
kept beside the case as `evals/<case>/known-bad/<rule>.json` (the exact
text removed, the graders that must fail, the rates seen), so "fails
without the rule" is a property the suite keeps. A deletion no case
notices is a survivor: the rule is unguarded. The skill on the branch is
never edited; every run is on a scratch copy of the working tree.

```
python3 -I evals/tools/skill_mutation.py check                 # no model: every reference still applies
python3 -I evals/tools/skill_mutation.py run --case <case>     # model time: the reference must fail its graders
python3 -I evals/tools/skill_mutation.py run --mutants <file>  # a whole pass, from a list of deletions
```

`check` runs in the pull-request workflow: a skill edit that touches a
guarded rule fails it until the reference is re-written and re-run. A
known-bad file is not one of its case's inputs, so adding one leaves the
case's evidence current. A case that resumes a `history.jsonl` runs the
skill text frozen in it, so the copy's histories get the same deletion.
Results go to a folder outside `evals/results/`: a run on a broken skill
is not part of a case's history. `tools/skill_mutation_test.py` holds the
tool without a model (16 tests). A pass's deletion list is kept as
`tools/mutants/<skill>.json` (each deletion's exact text and the cases it
was run on), so the pass can be read and run again; it is the record of
that pass, and goes stale as the skill changes.

What counts as caught: a grader that has passed every run since its bar
fails in at least two of three runs, and the failure, once read, is the
rule's absence and not a grader narrower than a correct run. One in three
gets three more runs. A judge on a one-line hand-back counts only at
three of three (below).

#### `chunk-runner`, 2026-11-13 and 14 (kad 0.14.5, Claude Code 2.1.323)

76 deletions on the cases each can reach, 101 deletion-case pairs, three
clean runs each (309 runs with the re-runs); the usage limit cut the pass
three times and `--resume` lost nothing. The list is
`tools/mutants/chunk-runner.json`. `orchestrator-chunk-runner-launch`
was left out: it consults the skill only through the runner it launches,
and all its graders read the orchestrator's launch.

**Caught (6 deletions, 7 references):**

| Rule removed | Case | Graders that failed (passes of clean runs) |
|---|---|---|
| A hash is real only when the repository says so | `chunk-runner-waits-for-handback` | `commit-confirmed-by-the-repository` 0/3 |
| The gate run with the design's modules and deviation zones; the three-way scope check | `chunk-runner-gate-deviation` | `gate-run-with-the-design-modules`, `gate-passes-and-names-the-deviation`, `gate-names-the-test-file-deviation`, `deviation-recorded-not-failed`, each 0/3 |
| The gate run with `--planning`; the sources check | `chunk-runner-gate-sources` | `gate-run-with-the-planning-directory`, `first-gate-fails-on-sources`, each 2/6: a weak reference, one run in three still passes the flag from the sources paragraph further down |
| The hand-back line's template | `chunk-runner-gate-sources` | `hands-back-pass-after-the-fix-and-stops` 0/3 (the runs invented a line of their own shape) |
| The hand-back is one line and nothing else | `chunk-runner-one-fix-round`, `chunk-runner-waits-for-handback` | `hand-back-is-the-one-line` 0/3, `hand-back-is-the-one-line-for-what-ran` 0/3 (judges; every run answered in paragraphs and bullets). Since E5 the references name the regexes that replaced them, `hand-back-is-one-line-and-nothing-else` and `hand-back-is-one-line-for-what-ran`, each 0/3 again on 2026-11-14 |
| The smoke agent's kind (`tdd-coach` when the chunk is not UI) | `chunk-runner-review-round` | `one-smoke-agent`, `smoke-agent-handed-the-launcher`, each 0/3 (a general-purpose agent was launched) |
| Regressions go to a second fixer, then the gate (caught since E5 reworded the prompt, 2026-11-14; a survivor before) | `chunk-runner-one-fix-round` | `second-and-last-fixer`, `gate-on-the-fix`, each 0/3 (the run handed back after round 1 with the regression standing) |

**Half noticed, no reference:** without `--allow` for the records
directory and the log, the gate fails on scope for the run's own records.
Three runs of six ended there and failed `chunk-runner-gate-deviation`'s
three deviation graders; in the other three the runner added an `--allow`
of its own and passed, which the skill forbids and no grader reads.

**Survivors (69 deletions).** No mechanical grader failed in two of three
runs, and a judge's failures, once read, were on lines that were correct.
By why they survived, with a proposal for each group; the owner decides,
nothing here is decided:

| Why it survived | Rules | Proposed |
|---|---|---|
| The case's prompt or the fixture's handoff says the rule, so the skill's text is not what the run follows | the round 0 and round 1 `rounds_record.py` commands (`--range` is in the prompt), the resume rule, the stopping point, "the checks are information when the owner opted out", the gate output's file name, a gate `FAIL` to one fixer, regressions to a second fixer, the smoke launcher and data rule (the prompt hands `scratch_run.py`) | changed cases: the prompts name the state and leave the action to the skill ("round 0 is recorded, the re-review has returned"), then the deletions are run again; until then an accepted gap |
| A prohibition the run has no pull toward breaking | never writes the log or commits the records, never runs the audit sync or checks the budget, never asks the owner, never edits code or plan or widens `--allow`, a `needs-decision` ends the run, two launches and no second reviewer kind, no third review, the fixer cap, pre-existing findings stand, never opens a source or runs `--show`, silence between launches, only the script's printed counts | accepted gap, held by the audited real runs; two new graders where the pull exists: `allow-list-not-widened` on `chunk-runner-gate-deviation` reading any `--allow` beyond the Files line, the records directory and the log (the half-noticed deletion above), and "no report opened" on `chunk-runner-gap-handback` (nothing is launched there, so a `Read` of `chunk-1-r0-review.md` in the trace is the runner's) |
| No case reaches the state | the stall message, the stall relaunch, a fixer's stall, the flaky rule, a second gate `FAIL` ends the round, sources still failing after the fix, a source not readable, a sandbox `FAIL` under the launcher, the light cadence, the accessibility agent's smoke pass, browser checks owed, a clean round 0, the issue-fix records prefix, and the first half of step 4 (round 0's findings to one fixer, the gate on fix r1, the re-review launch, the smoke agent again only after smoke findings) | one new case for the first half of step 4, from a state with round 0 recorded and findings standing, written with F2's case (a gate failure after r1); the light cadence waits for the light-loop arm; the rest an accepted gap, the stall rule's by the real runs (`chunk-runner-replay-unheld-commit` reaches it, and its two deletions survived there too) |
| The wait: a launch blocks under the eval | waiting is ending the turn, nothing expected is a result, never hand back while an agent works, the definition of a hand-back, wait for both hand-backs, the stall message never before a hand-back | accepted gap: neither the eval nor a replay can hold a runner in the wait (below); the audited real runs are the guard |
| No grader reads the behaviour | `model` and `maxTurns` explicit, the sandbox check before each launch and its count, single-quoted paths, the builder's two carried lines, the builder told nothing of the flow, keeping the agent id, `--agent` and the red commit, shell edits counted, `--protect`, `--expect-tests-from` and `--chunk`, `--coverage`, reading only the gate's last line, the sources fixer's added line, the reviewer told its skills, handed five things, the report's shape, the suite read from the gate file, reviewers never install, the smoke report's format, the smoke agent handed nothing else, `?` for an unknown fact, the scripts directory, and the hash rule's three other sentences (in the chunk's range, commits read from `git log`, a missing commit is no commit) | three new mechanical graders on cases that already run: the gate's `--protect`, `--expect-tests-from` and `--agent` on `chunk-runner-gate-deviation`; `"model": "sonnet"` on the fixer's launch in `chunk-runner-gate-outside`; `sandbox_check.py` run before that launch. Two rules to drop: "Keep its agent id" (the gate's command already takes it) and "Read its last line; read the rest only on `FAIL`". The rest an accepted gap |

**Grader findings, from reading the failures:**

- `stops-with-the-decision-on-the-line` (`chunk-runner-gap-handback`) and
  `hand-back-is-the-one-line` (`chunk-runner-one-fix-round`) are judges
  on a one-line reply and fail lines that are word for word correct: in
  up to two runs of three under deletions that changed nothing about the
  line, and in 6 of 20 and 5 of 21 runs on the unchanged skill (the table
  above). Proposed: each becomes a regex on the line, as
  `chunk-runner-review-round`'s and `chunk-runner-gate-sources`'s already
  did; the two `handback-one-line` references then name the regex.
  Done in E5 ("Judges turned into tool checks", below).
- `plan-entry-not-edited` (`chunk-runner-gate-deviation`) and
  `no-planning-document-written` (`chunk-runner-gap-handback`) could never
  fail: their patterns had the doubled braces of a format string. Fixed
  here; both cases re-ran at three runs.

**Dead weight, cross-checked with the table above.** Cases that have
never failed a mechanical grader since their bar and that no deletion
fails; candidates to merge or drop, none merged or dropped:

- `chunk-runner-gate-outside`: never failed, and none of its 10
  deletions failed it (its prompt says what to do with the failure).
- `chunk-runner-gap-handback`: only its judge has ever failed, on correct
  lines; none of its 7 deletions failed a mechanical grader.
- `chunk-runner-replay-not-the-handback` and
  `chunk-runner-replay-unheld-commit` (new, below): none of the nine wait,
  hash and stall deletions failed either; a runner checks the commit and
  refuses the sibling's result with or without the rule.
- `orchestrator-chunk-runner-handback`: never failed; not run here (it
  does not load the skill), so it waits for E2 on `orchestrator`.

### Replay cases

**Dropped in 0.15.1** ("The loop's fixes", below): the two cases and their fixture are gone; this section is the record of what they showed and of how a history is captured.

A replay case resumes the transcript of a real session at a point the
eval cannot reach on its own, and its prompt is the next turn. The
history is captured outside the eval, from a session started on a
fixture for the capture and never from a project's transcripts:

1. Build the fixture state in a scratch folder
   (`fixtures/library-app/code-plants/loop/state.sh planned`) and start a
   real, interactive, fenced session on it (`bin/kad --project <folder>`
   with `KAD_CONFIG_DIR` and `KAD_AUDIT_DIR` pointing at scratch folders,
   so nothing of the capture is stored with the owner's own). A headless
   session (`-p`) will not do: there a launch takes `run_in_background:
   false` and blocks, and the agent never waits; only an interactive
   session launches in the background.
2. Give it a prompt that launches the agent under test as a subagent
   with the case's task, and copy that agent's own transcript
   (`<session>/subagents/agent-<id>.jsonl` under Claude Code's projects
   directory) at the moment to resume from.
3. Replace the scratch folder's path and anything else that names the
   machine or the account, then `tools/freeze-history.sh --subagent
   <agent.jsonl> <case>/history.jsonl` (it refuses a history that still
   names the home directory or the account).
4. Keep the repository the capture ran on: the loop's states write the
   day's date into the log and the handoff, so every build has its own
   hashes, and the ones the captured agent already read would name
   nothing. `fixtures/library-app/replay/chunk-runner-wait/` holds it as
   a git bundle with the uncommitted log, and `restore.sh` puts both
   under the run's tree after `state.sh`.

`tools/history_stale.py` and the gate treat a replay history like a
phase's: when the skill's text changes the history is stale and the case
is not run until it is captured again.

The two cases (`chunk-runner-replay-*`, 2026-11-13) resume a chunk
runner that had launched chunk 1's builder in the background and ended
its turn on "Waiting for the builder's hand-back." What they showed:

- **A replay cannot hold the wait.** On resume the harness itself tells
  the session that its background agent "didn't finish before the
  previous session ended". The runner is no longer waiting for anything,
  so whether a runner goes on waiting after a stray wake-up is shown
  only by a real run.
- **A sibling's hand-back** (another agent's id, a commit of its own):
  in every run the runner refused it as its builder's result.
  It ended the round on the stall or relaunched the builder and reported
  that builder's own verified commit.
- **A hand-back naming a commit the repository does not hold** (the
  builder's real hand-back from the capture, on a repository where
  nothing was built): in every run the runner checked the hash against
  the repository (`git cat-file -e` first, in the runs read), and the
  hash never reached the line.
- **Two fidelity gaps.** The eval offers no `SendMessage`, so the stall
  rule's one message cannot be sent; and the frozen history writes the
  plugin's path as `<plugin-root>`, so a resumed runner has to find the
  scripts directory again (two runs of six ended the round there instead
  of relaunching).

### The cases sorted

`TODO.md`'s E4: per case, what grades it, what a run costs, what it has
caught, and two things that take reading: whether a tool could decide
each judge, and whether the prompt states the rule the case grades. No
model time. The table is written by `tools/case_sort.py`; run it again
with `python3 -I evals/tools/case_sort.py --readme evals/README.md`
(`tools/case_sort_test.py`, 12 tests, holds it without a model).

The two reading columns are not computed. They are in
`tools/case_reading.json`, one entry per case, written on 2026-11-14 from
a reading of every case file: correct a row there and run the tool again.
`case_sort.py --check` fails when a case has no entry or an entry's
judges are not exactly the case's `llm` graders, so a judge added to a
case has to be read before the table is current. What the words mean:

- **A tool could decide** a judge when its criterion comes down to the
  shape of a line, a file's contents, a count, or a name present or
  absent. A judge a tool could decide half of is marked as taking
  reading, with the half named in its reason. Where a tool check would
  lose part of what the judge reads, the reason says what is lost.
- **The prompt states the rule** when it tells the run to do something a
  grader then checks, and that something should have come from the
  skill's text. `yes`: the graded action is in the prompt. `partly`: a
  stopping point or a hand-over sentence gives away one or two graders
  and leaves the rest to the skill. Naming the skill to invoke does not
  count for `chunk-runner` and `tdd-implementation-lite`, which are only
  ever invoked by name, nor does naming the agent in a `-via-agent` case.
- **Cost and time** are means over the completed runs since 2026-11-10,
  at the list prices the CLI records. The time split is given only for
  runs that launched no agent and whose trace is still on disk.

**The baseline is $45.70, not $54.** A run's `costUsd` already includes
its `judgeCostUsd`: in all 189 runs checked, the agent's own total in the
trace plus the judge cost equals `costUsd`. The $54 of 2026-11-14 added
the two columns, so it counted the judges twice. For the same 139 cases
one run of each is $45.70: the agent's runs $37.53 (82%), the judges
$8.17 (18%). Savings below are against $45.70. (A run the gate marked
errored because a grader threw was paid for and is priced, as
`case_history.py` counts it; a run with no grader result is not.)

<!-- case-sort:start -->
Written by `tools/case_sort.py` on 2026-11-19 from the cases, `tools/case_reading.json` and the results under `results/`, `kad-eval-results-archive/`; cost and time are means over the completed runs since 2026-11-10 (`*`: no run since, every held run).

| Case | Skill | Tool checks | Judges | A tool could decide | Prompt states the rule | Agent $ | Judges $ | Seconds (agent + judges) | Failed since the bar | Deletions that failed it |
|---|---|---|---|---|---|---|---|---|---|---|
| `acceptance-criteria-payfine` | acceptance-criteria | 1 tool call | 1 | 0 of 1 | no | 0.07 | 0.01 | 17 | 0 of 15 | no pass on the skill |
| `accessibility-review-ac-walk` | accessibility-review | 5 regex, 2 tool call, 1 file | 1 | 0 of 1 | yes: "Start it through the scratch launcher `tools/scratch_run.py` with the scratch folder `scratch/portal-walk` next to the project [...] and `PORTAL_DATA` inside that folder" | 0.45 | 0.01 | 66 | 1 of 20 | no pass on the skill |
| `accessibility-review-design-notes` | accessibility-review | 5 regex, 1 tool call, 1 file | 0 |  | partly: "the declined message must read exactly "Your card was declined. Try another card." and a screen reader user has to be told as soon as it appears" | 0.23 | 0.00 | 62 (63 + 0) | 0 of 4 (few runs) | no pass on the skill |
| `accessibility-review-neg-readability` | accessibility-review | 1 tool call | 0 |  | no | 0.06 | 0.00 | 9 (6 + 1) | 0 of 19 | no pass on the skill |
| `accessibility-review-payfine` | accessibility-review | 5 regex, 1 tool call, 1 file | 6 | 0 of 6 | partly: "fill in the slice's accessibility placeholder" | 0.23 | 0.35 | 92 (59 + 13) | 8 of 42 | 1 kept: `handed-on` |
| `accessibility-review-payfine-subtle` | accessibility-review | 3 regex, 1 tool call, 1 file | 6 | 0 of 6 | partly: "fill in the slice's accessibility placeholder" | 0.23 | 0.30 | 99 (78 + 18) | 7 of 39 | no pass on the skill |
| `adr-neg-rename` | adr | 1 regex, 1 tool call | 1 | 0 of 1 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `adr-payment-gateway` | adr | 2 regex, 1 tool call, 1 file | 1 | 0 of 1 | no | 0.08 | 0.01 | 13 | 0 of 4 (few runs) | no pass on the skill |
| `architecture-design-concurrency-interleavings` | architecture-design | 8 regex, 1 tool call | 0 |  | no | 0.20 | 0.00 | 42 (44 + 0) | 0 of 5 (few runs) | 1 kept: `interleavings` |
| `architecture-design-neg-review` | architecture-design | 1 tool call | 0 |  | no | 0.09 | 0.00 | 15 (11 + 1) | 0 of 23 | no pass on the skill |
| `architecture-design-owner-sheet` | architecture-design | 2 regex, 1 tool call | 1 | 0 of 1 | no | 0.23 | 0.01 | 46 (36 + 2) | 3 of 31 | no pass on the skill |
| `architecture-design-payfine-phase1` | architecture-design | 1 regex, 1 tool call | 2 | 0 of 2 | no | 0.19 | 0.02 | 36 (28 + 5) | 0 of 28 | no pass on the skill |
| `architecture-design-payfine-phase2` | architecture-design | 3 regex | 8 | 0 of 8 | no | 0.29 | 0.32 | 110 (101 + 16) | 23 of 29 | no pass on the skill |
| `architecture-design-payfine-via-agent` | architecture-design | 3 regex, 1 tool call | 1 | 0 of 1 | partly: "its architecture map is at `docs/architecture-map.md`" | 0.22 | 0.02 | 46 | 0 of 21 | no pass on the skill |
| `architecture-design-scope-consequence` | architecture-design | 1 regex, 1 tool call | 2 | 0 of 2 | no | 0.18 | 0.02 | 44 (51 + 4) | 15 of 37 | no pass on the skill |
| `architecture-review-neg-security-review` | architecture-review | 1 tool call | 0 |  | no | 0.08 | 0.00 | 16 (12 + 1) | 0 of 18 | no pass on the skill |
| `architecture-review-neg-test-quality-review` | architecture-review | 1 tool call | 0 |  | no | 0.09 | 0.00 | 12 (10 + 0) | 0 of 19 | no pass on the skill |
| `chunk-runner-check-fail-second-fixer` | chunk-runner | 5 regex, 5 tool call, 1 file | 0 |  | no | 0.58 | 0.00 | 67 | 0 of 1 (few runs) | none run |
| `chunk-runner-fix-gate-fails` | chunk-runner | 4 regex, 10 tool call, 1 file | 0 |  | partly: "Stop once round 1 is recorded" | 1.16 | 0.00 | 187 | 0 of 8 | 1 kept: `gate-fixer` |
| `chunk-runner-gap-handback` | chunk-runner | 5 regex, 6 tool call | 0 |  | no | 0.28 | 0.01 | 33 (22 + 2) | 8 of 36 | 0 of 7 |
| `chunk-runner-gate-deviation` | chunk-runner | 6 regex, 8 tool call, 1 file | 0 |  | partly: "Stop once the gate has run and its result is known, before any launch" | 0.31 | 0.00 | 33 (25 + 1) | 3 of 33 | 1 of 14: `gate-design-modules` |
| `chunk-runner-gate-outside` | chunk-runner | 5 regex, 6 tool call, 1 tool order | 0 |  | partly: "Stop once the gate has passed, before any reviewer is launched" | 0.57 | 0.00 | 90 | 0 of 28 | 0 of 10 |
| `chunk-runner-gate-sources` | chunk-runner | 6 regex, 4 tool call | 0 |  | partly: "Stop once the gate has passed, before any reviewer is launched" | 0.54 | 0.00 | 80 | 1 of 25 | 1 of 8: `handback-template` |
| `chunk-runner-last-fix-review` | chunk-runner | 4 regex, 7 tool call, 1 file | 0 |  | no | 0.86 | 0.00 | 125 | 1 of 8 | 1 kept: `last-fix-review` |
| `chunk-runner-light-no-review` | chunk-runner | 4 regex, 5 tool call | 0 |  | no | 0.31 | 0.00 | 26 (20 + 1) | 0 of 1 (few runs) | none run |
| `chunk-runner-one-fix-round` | chunk-runner | 5 regex, 7 tool call | 0 |  | partly: "the sandbox checks in this round are information and never end it" | 0.67 | 0.00 | 108 | 7 of 42 | 2 of 15: `handback-one-line`, `regressions-to-a-fixer` |
| `chunk-runner-review-round` | chunk-runner | 6 regex, 8 tool call, 2 file | 0 |  | partly: "Stop once round 0 is recorded [...] don't start the fix round" | 1.26 | 0.01 | 157 | 1 of 33 | 1 of 19: `smoke-agent-kind` |
| `chunk-runner-suite-fail-ends` | chunk-runner | 6 regex, 3 tool call | 0 |  | no | 0.30 | 0.00 | 24 (18 + 4) | 0 of 1 (few runs) | none run |
| `chunk-runner-waits-for-handback` | chunk-runner | 4 regex, 8 tool call | 0 |  | yes: "end after step 2, the gate on the builder's commit (and its one fixer, if the gate fails). Launch no reviewer and no smoke agent" | 0.60 | 0.00 | 91 | 6 of 30 | 2 of 19: `handback-one-line`, `hash-is-real` |
| `ci-pipeline-os-matrix` | ci-pipeline | 7 regex, 1 tool call, 1 file | 0 |  | no | 0.48 | 0.00 | 66 (24 + 10) | 1 of 10 | 1 kept: `two-operating-systems` |
| `ci-pipeline-screen-job` | ci-pipeline | 9 regex, 1 tool call, 6 file | 0 |  | no | 0.21 | 0.00 | 50 (42 + 10) | 2 of 10 | 1 kept: `screen-job` |
| `code-review-catalog` | code-review | 1 regex, 2 tool call, 1 file | 2 | 0 of 2 | no | 0.12 | 0.03 | 31 | 13 of 33 | no pass on the skill |
| `code-review-chunk-gate-covers` | code-review | 5 regex, 1 tool call, 1 file | 0 |  | no | 0.22 | 0.00 | 40 | 2 of 12 | 1 kept: `gate-holds` |
| `code-review-comments-chunk` | code-review | 3 regex, 3 tool call, 1 file | 3 | 0 of 3 | partly: "Write one report in the shared finding format [...] and hand back the counts and the path" | 0.24 | 0.06 | 56 | 34 of 64 | no pass on the skill |
| `code-review-days-left-pr` | code-review | 1 regex, 1 tool call, 1 file | 5 | 0 of 5 | no | 0.14 | 0.14 | 52 | 11 of 34 | no pass on the skill |
| `code-review-fine-notices-pr` | code-review | 3 regex, 2 tool call, 1 file | 5 | 0 of 5 | no | 0.15 | 0.17 | 55 | 13 of 28 | 1 kept: `handed-on` |
| `code-review-fine-notices-pr-via-agent` | code-review | 4 regex, 1 tool call, 1 file | 5 | 0 of 5 | no | 0.22 | 0.19 | 78 | 27 of 30 | no pass on the skill |
| `code-review-fines-report-pr` | code-review | 1 regex, 1 tool call, 1 file | 4 | 0 of 4 | no | 0.17 | 0.15 | 66 | 5 of 25 | no pass on the skill |
| `code-review-neg-architecture` | code-review | 1 tool call | 0 |  | no | 0.17 | 0.00 | 37 | 0 of 19 | no pass on the skill |
| `code-review-structural-high-at-d` | code-review | 1 regex, 1 tool call, 1 file | 2 | 0 of 2 | no | 0.21 | 0.07 | 65 | 4 of 18 | no pass on the skill |
| `cold-read-new-beside-old` | cold-read | 5 regex, 3 tool call, 1 file | 0 |  | no | 0.20 | 0.00 | 51 | 2 of 14 | 1 kept: `pair-new-with-old` |
| `cold-read-refusal-no-exit` | cold-read | 4 regex, 2 tool call, 1 file | 0 |  | no | 0.24 | 0.00 | 56 | 0 of 0 (few runs) | no pass on the skill |
| `delegation-consult-with-file` | reliability-requirements | 4 regex, 2 tool call | 1 | 0 of 1 | yes: "Decide it, revise your document in place, commit it by name as `Decision <n>: <title>`, and hand back the commit hash and one sentence" | 0.16 | 0.02 | 32 (29 + 7) | 18 of 31 | no pass on the skill |
| `delegation-consult-without-file` | reliability-requirements | 1 regex, 2 tool call | 1 | 0 of 1 | no | 0.12 | 0.02 | 21 (10 + 6) | 5 of 28 | no pass on the skill |
| `delivery-ci-red-not-done` | delivery | 5 regex, 3 tool call, 1 file | 2 | 0 of 2 | partly: "This session may launch no agent: when the next action is a launch, write the handoff file for it (what the agent is to be handed, word for word where the skill gives words) and stop there" | 0.42 | 0.02 | 63 (41 + 15) | 9 of 22 | no pass on the skill |
| `delivery-screens-owed` | delivery | 8 regex, 4 tool call | 0 |  | no | 0.46 | 0.00 | 50 (39 + 9) | 0 of 10 | 1 kept: `screens-verdicts` |
| `delivery-screens-stray` | delivery | 8 regex, 4 tool call | 1 | 0 of 1 | partly: "This session may launch no agent: when the next action is a launch, write the handoff file for it (what the agent is to be handed, word for word where the skill gives words) and stop there" | 0.43 | 0.01 | 51 (39 + 12) | 3 of 15 | 1 kept: `screens-verdicts` |
| `design-system-payfine-phase1` | design-system | 1 regex, 1 tool call | 1 | 0 of 1 | no | 0.10 | 0.00 | 14 | 0 of 7 | no pass on the skill |
| `design-system-payfine-phase2` | design-system | 2 regex, 2 file | 4 | 0 of 4 | no | 0.18 | 0.04 | 59 | 0 of 7 | no pass on the skill |
| `design-system-payfine-phase3` | design-system | 3 regex, 1 file | 5 | 0 of 5 | no | 0.31 | 0.26 | 132 | 7 of 16 | no pass on the skill |
| `design-system-payfine-reference` | design-system | 3 regex, 1 tool call | 2 | 0 of 2 | no | 0.22 | 0.01 | 75 | 1 of 6 | no pass on the skill |
| `design-system-payfine-review` | design-system | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.17 | 0.06 | 62 | 0 of 11 | no pass on the skill |
| `domain-model-bank-phase1` | domain-model | 3 regex, 2 tool call | 0 |  | no | 0.09 | 0.00 | 18 (18 + 0) | 0 of 4 (few runs) | no pass on the skill |
| `domain-model-bank-phase2` | domain-model | 7 regex, 1 tool call, 1 file | 0 |  | partly: "What you would ask me, answered: a connection that the bank or the vendor has ended for good, with no way out in the app, stays unsupported for now." | 0.11 | 0.00 | 26 (25 + 0) | 0 of 4 (few runs) | no pass on the skill |
| `external-review-triage-cancel-hold` | external-review-triage | 2 regex, 1 tool call, 1 file | 3 | 0 of 3 | partly: "Write your report to [...] and hand back the counts and the path" | 0.35 | 0.07 | 54 | 0 of 10 | no pass on the skill |
| `library-app-catalog-review` | architecture-review | 1 regex, 1 tool call, 1 file | 2 | 0 of 2 | no | 0.19 | 0.04 | 47 (29 + 4) | 4 of 23 | no pass on the skill |
| `library-app-fines-review` | architecture-review | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.26 | 0.11 | 89 (69 + 7) | 0 of 19 | no pass on the skill |
| `library-app-lending-review` | architecture-review | 1 regex, 1 tool call, 1 file | 4 | 0 of 4 | no | 0.25 | 0.26 | 78 (61 + 9) | 5 of 28 | no pass on the skill |
| `library-app-lending-review-via-agent` | architecture-review | 1 regex, 1 tool call, 1 file | 4 | 0 of 4 | partly: "return its findings report verbatim [...] (including its opening section on the importance ordering it assumed)" | 0.37 | 0.22 | 130 | 2 of 20 | no pass on the skill |
| `library-app-reporting-pr` | architecture-review | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.21 | 0.07 | 68 (45 + 5) | 0 of 15 | no pass on the skill |
| `library-app-structure-review` | architecture-review | 3 regex, 1 tool call, 1 file | 4 | 0 of 4 | no | 0.32 | 0.21 | 102 (76 + 7) | 2 of 28 | 1 kept: `handed-on` |
| `map-query-consults` | map-query | 1 regex, 1 tool call | 4 | 0 of 4 | no | 0.10 | 0.03 | 23 | 0 of 9 | no pass on the skill |
| `map-query-no-map` | map-query | 1 regex, 1 tool call | 1 | 0 of 1 | no | 0.07 | 0.01 | 8 | 1 of 9 | no pass on the skill |
| `map-update-cancel-hold` | map-update | 5 regex, 1 tool call | 3 | 0 of 3 | no | 0.17 | 0.49 | 39 | 25 of 30 | no pass on the skill |
| `operational-readiness-neg-reliability` | operational-readiness | 1 tool call | 0 |  | no | 0.10 | 0.00 | 20 | 0 of 16 | no pass on the skill |
| `operational-readiness-neg-security` | operational-readiness | 1 tool call | 0 |  | no | 0.06 | 0.00 | 12 | 0 of 15 | no pass on the skill |
| `operational-readiness-ops-phase1` | operational-readiness | 1 tool call | 1 | 0 of 1 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `operational-readiness-ops-phase2` | operational-readiness | 0 | 5 | 0 of 5 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `operational-readiness-release-phase1` | operational-readiness | 1 tool call | 2 | 0 of 2 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `operational-readiness-release-phase2` | operational-readiness | 0 | 5 | 0 of 5 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `orchestrator-asks-for-target` | orchestrator | 3 tool call | 1 | 0 of 1 | no | 0.20 | 0.00 | 13 (8 + 3) | 0 of 49 | no pass on the skill |
| `orchestrator-autopilot-counts-over` | orchestrator | 2 regex, 2 tool call | 0 |  | partly: "hand off as soon as the next chunk's runner has been launched" | 2.70 | 0.00 | 390 | 1 of 14 | no pass on the skill |
| `orchestrator-autopilot-question` | orchestrator | 4 regex, 2 tool call | 0 |  | no | 0.41 | 0.00 | 41 (29 + 1) | 0 of 9 | 1 kept: `autopilot-question` |
| `orchestrator-autopilot-recorded` | orchestrator | 3 regex, 2 tool call, 1 file | 0 |  | partly: "And yes to autopilot: take your own recommendation at the stops the chunk loop would otherwise put to me, and log each one" | 0.45 | 0.00 | 54 (50 + 2) | 2 of 11 | 1 kept: `autopilot-question` |
| `orchestrator-autopilot-round` | orchestrator | 5 tool call, 1 tool order | 0 |  | partly: "Hand off as soon as the next agent has been launched" | 1.35 | 0.00 | 178 | 1 of 9 | 1 kept: `autopilot-round` |
| `orchestrator-backward-route` | orchestrator | 4 tool call, 1 file | 2 | 0 of 2 | no | 0.33 | 0.01 | 60 (43 + 4) | 19 of 56 | no pass on the skill |
| `orchestrator-budget-exceeded` | orchestrator | 3 regex, 2 tool call | 0 |  | no | 0.27 | 0.00 | 30 (15 + 3) | 31 of 56 | no pass on the skill |
| `orchestrator-capture-states` | orchestrator | 4 regex, 3 tool call | 0 |  | partly: "This session may launch no agent: when the next action is a launch, write the handoff file for it (what the agent is to be handed, word for word where the skill gives words) and stop there" | 0.36 | 0.00 | 45 (36 + 8) | 0 of 9 | 1 kept: `capture-for-listed-states` |
| `orchestrator-chunk-runner-handback` | orchestrator | 6 regex, 2 tool call | 1 | 0 of 1 | partly: "hand off once chunk 1's C line is written and its records committed, before chunk 2's runner is launched" | 0.31 | 0.01 | 39 (39 + 6) | 0 of 26 | no pass on the skill |
| `orchestrator-chunk-runner-launch` | orchestrator | 6 tool call, 1 tool order | 1 | 0 of 1 | partly: "hand off as soon as chunk 1's runner has been launched: don't wait for it to return; write the handoff file saying the runner is in flight and stop" | 1.80 | 0.01 | 281 | 17 of 49 | no pass on the skill |
| `orchestrator-definition-of-done` | orchestrator | 8 tool call, 1 tool order, 1 file | 1 | 0 of 1 | partly: "hand off before the slice reviewers are launched (after the Definition of Done has been acted on and checked again)" | 1.18 | 0.01 | 228 | 77 of 84 | no pass on the skill |
| `orchestrator-delivery-foreground` | orchestrator | 6 regex, 8 tool call | 1 | 0 of 1 | no | 0.48 | 0.01 | 76 (56 + 10) | 39 of 95 | 1 kept: `deferrals-by-script` |
| `orchestrator-delivery-removal` | orchestrator | 6 regex, 5 tool call, 1 tool order | 1 | 0 of 1 | partly: "If the scan finds anything of that file in this branch's commits, replace it and rewrite the branch before it is pushed. You have my word for that rewrite" | 0.50 | 0.01 | 107 | 3 of 32 | no pass on the skill |
| `orchestrator-gap-without-delegation` | orchestrator | 2 regex, 5 tool call | 1 | 0 of 1 | no | 0.53 | 0.01 | 75 | 12 of 62 | no pass on the skill |
| `orchestrator-gate-checks-route-back` | orchestrator | 2 regex, 3 tool call | 0 |  | no | 0.42 | 0.00 | 47 (50 + 2) | 3 of 16 | 1 kept: `gate-checks-route-back` |
| `orchestrator-issue-fix-records` | orchestrator | 6 regex, 4 tool call | 1 | 0 of 1 | partly: "Hand off as soon as the chunk loop's A line is written (write the handoff file and stop; don't start B in this session)" | 0.38 | 0.01 | 52 (43 + 4) | 3 of 22 | no pass on the skill |
| `orchestrator-last-fix-review-at-d` | orchestrator | 5 tool call | 0 |  | partly: "Hand off as soon as the next agent has been launched" | 0.66 | 0.00 | 78 | 0 of 8 | 1 kept: `last-fix-review-at-d` |
| `orchestrator-mutation-before-review` | orchestrator | 1 regex, 7 tool call | 0 |  | partly: "hand off when the next thing to do is launching round 0 of the slice review itself" | 0.35 | 0.00 | 53 | 1 of 18 | 1 kept: `mutation-before-reviewers` |
| `orchestrator-plan-check-seam` | orchestrator | 2 regex, 4 tool call | 1 | 0 of 1 | partly: "hand off once the B line is written, before chunk 1's build" | 0.48 | 0.01 | 75 | 2 of 53 | no pass on the skill |
| `orchestrator-planning-pr-open` | orchestrator | 2 regex, 5 tool call | 0 |  | no | 0.31 | 0.00 | 14 (13 + 1) | 0 of 5 (few runs) | no pass on the skill |
| `orchestrator-planning-row` | orchestrator | 3 regex, 7 tool call | 0 |  | partly: "do everything up to the first `git push`, don't push, and tell me what you would push and what happens after" | 0.44 | 0.00 | 36 (34 + 1) | 1 of 8 | no pass on the skill |
| `orchestrator-readiness-correction-autopilot` | orchestrator | 4 regex, 4 tool call | 0 |  | no | 0.53 | 0.00 | 67 (60 + 1) | 6 of 17 | no pass on the skill |
| `orchestrator-readiness-gate` | orchestrator | 2 regex, 4 tool call, 1 tool order | 2 | 0 of 2 | partly: "Hand off as soon as the chunk loop's A line is written (write the handoff file and stop; don't start B in this session)" | 0.62 | 0.03 | 126 (91 + 9) | 22 of 78 | no pass on the skill |
| `orchestrator-readiness-open-item` | orchestrator | 2 regex, 3 tool call | 1 | 0 of 1 | no | 0.34 | 0.01 | 43 (36 + 5) | 16 of 55 | no pass on the skill |
| `orchestrator-readiness-sources` | orchestrator | 4 regex, 4 tool call | 1 | 0 of 1 | no | 0.35 | 0.01 | 45 (46 + 3) | 4 of 33 | no pass on the skill |
| `orchestrator-readme-stale-not-done` | orchestrator | 2 regex, 8 tool call, 1 tool order | 1 | 0 of 1 | partly: "hand off before the slice reviewers are launched (after the Definition of Done has been acted on and checked again)" | 1.24 | 0.01 | 255 | 11 of 13 | no pass on the skill |
| `orchestrator-recommended-not-asked` | orchestrator | 2 regex, 6 tool call, 1 file | 0 |  | partly: "a problem you find in code that is already there is for a later slice, not this one, and a risk the design leaves standing I accept for now" | 0.73 | 0.00 | 151 (155 + 1) | 2 of 5 (few runs) | no pass on the skill |
| `orchestrator-route-accessibility` | orchestrator | 1 regex, 4 tool call, 1 file | 2 | 0 of 2 | no | 0.49 | 0.01 | 109 (71 + 4) | 11 of 62 | no pass on the skill |
| `orchestrator-route-backward-requirements` | orchestrator | 5 tool call, 1 file | 2 | 0 of 2 | no | 0.27 | 0.02 | 34 (23 + 4) | 4 of 47 | no pass on the skill |
| `orchestrator-route-design` | orchestrator | 4 tool call, 1 file | 2 | 0 of 2 | no | 0.42 | 0.01 | 73 (115 + 4) | 4 of 51 | no pass on the skill |
| `orchestrator-route-design-system` | orchestrator | 5 tool call, 1 file | 2 | 0 of 2 | no | 0.27 | 0.01 | 34 (20 + 3) | 0 of 42 | no pass on the skill |
| `orchestrator-route-domain-model` | orchestrator | 2 regex, 3 tool call | 0 |  | no | 0.34 | 0.00 | 30 (28 + 1) | 0 of 5 (few runs) | no pass on the skill |
| `orchestrator-route-implementation` | orchestrator | 3 tool call, 1 file | 2 | 0 of 2 | no | 0.25 | 0.01 | 29 (18 + 4) | 2 of 50 | no pass on the skill |
| `orchestrator-route-implementation-prenamed` | orchestrator | 2 tool call, 1 file | 2 | 0 of 2 | no | 0.24 | 0.01 | 29 (16 + 4) | 1 of 46 | no pass on the skill |
| `orchestrator-route-open-pr` | orchestrator | 1 regex, 6 tool call | 1 | 0 of 1 | partly: "Report what is open and stop after your first question to me; don't run the triage or any fix in this session" | 0.27 | 0.01 | 24 (16 + 5) | 1 of 29 | no pass on the skill |
| `orchestrator-route-problem-framing` | orchestrator | 4 tool call, 1 file | 2 | 0 of 2 | no | 0.22 | 0.01 | 24 (12 + 4) | 1 of 43 | no pass on the skill |
| `orchestrator-route-reliability` | orchestrator | 5 tool call, 1 file | 2 | 0 of 2 | no | 0.28 | 0.01 | 37 (18 + 4) | 7 of 52 | no pass on the skill |
| `orchestrator-route-scope-decision` | orchestrator | 3 tool call, 1 file | 2 | 0 of 2 | no | 0.29 | 0.02 | 42 (29 + 4) | 63 of 118 | no pass on the skill |
| `orchestrator-route-screen-design` | orchestrator | 1 regex, 3 tool call, 1 file | 2 | 0 of 2 | no | 0.44 | 0.01 | 93 (78 + 6) | 13 of 59 | no pass on the skill |
| `orchestrator-route-slicer-accessibility-mistake` | orchestrator | 4 tool call | 1 | 0 of 1 | no | 0.32 | 0.00 | 38 (21 + 2) | 1 of 43 | no pass on the skill |
| `orchestrator-route-slicing` | orchestrator | 4 tool call, 1 file | 2 | 0 of 2 | no | 0.32 | 0.01 | 46 (33 + 4) | 6 of 57 | no pass on the skill |
| `orchestrator-route-tech-bootstrap` | orchestrator | 4 tool call, 1 file | 2 | 0 of 2 | no | 0.27 | 0.01 | 33 (24 + 4) | 3 of 45 | no pass on the skill |
| `orchestrator-route-user-story` | orchestrator | 4 tool call, 1 file | 2 | 0 of 2 | no | 0.25 | 0.01 | 33 (15 + 4) | 5 of 49 | no pass on the skill |
| `orchestrator-runner-handback-unverified` | orchestrator | 2 regex, 3 tool call | 2 | 0 of 2 | partly: "This session may launch no agent: when the next action is a launch, write the handoff file for it and stop there" | 0.30 | 0.02 | 38 (25 + 11) | 0 of 10 | no pass on the skill |
| `orchestrator-security-stage` | orchestrator | 3 tool call, 1 file | 2 | 0 of 2 | no | 0.31 | 0.02 | 42 (25 + 4) | 0 of 42 | no pass on the skill |
| `orchestrator-session-setup` | orchestrator | 4 tool call | 1 | 0 of 1 | no | 0.24 | 0.01 | 22 (11 + 2) | 8 of 46 | no pass on the skill |
| `orchestrator-slice-review-launches` | orchestrator | 9 tool call, 2 tool order | 0 |  | partly: "hand off as soon as round 0 of the slice review has been launched" | 4.00 | 0.00 | 203 | 2 of 18 | 1 kept: `cold-reader-launch` |
| `orchestrator-solo-build-launch` | orchestrator | 1 regex, 8 tool call, 1 tool order | 0 |  | partly: "hand off as soon as the next agent has been launched" | 1.08 | 0.00 | 162 | 1 of 6 | no pass on the skill |
| `orchestrator-solo-confirmed-only` | orchestrator | 3 regex, 7 tool call, 1 file | 0 |  | partly: "Hand off as soon as the next agent has been launched" | 0.73 | 0.00 | 92 | 1 of 6 | no pass on the skill |
| `orchestrator-solo-from-message` | orchestrator | 3 regex, 2 tool call, 1 file | 0 |  | partly: "Build this slice solo: one builder for the slice." | 0.44 | 0.00 | 49 (44 + 2) | 0 of 5 (few runs) | no pass on the skill |
| `orchestrator-solo-from-standing-file` | orchestrator | 5 regex, 2 tool call, 1 file | 0 |  | no | 0.46 | 0.00 | 52 (50 + 3) | 0 of 5 (few runs) | no pass on the skill |
| `orchestrator-solo-nothing-confirmed` | orchestrator | 5 regex, 4 tool call, 1 file | 0 |  | partly: "Hand off as soon as the slice review's line is written in the log, or as soon as an agent has been launched, whichever comes first" | 0.38 | 0.00 | 36 (30 + 7) | 0 of 5 (few runs) | 1 kept: `confirmed-only` |
| `orchestrator-superseded-scope-map` | orchestrator | 4 tool call, 1 file | 1 | 0 of 1 | no | 0.28 | 0.01 | 35 (24 + 2) | 0 of 43 | no pass on the skill |
| `orchestrator-target-from-project` | orchestrator | 3 regex, 3 tool call, 1 file | 0 |  | no | 0.25 | 0.00 | 15 (12 + 0) | 0 of 4 (few runs) | 1 kept: `target-from-project` |
| `pr-writeup-portal-fines` | pr-writeup | 1 tool call | 3 | 0 of 3 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `problem-framing-doc-payfine-phase1` | problem-framing-doc | 1 regex, 1 tool call | 2 | 0 of 2 | no | 0.06 | 0.01 | 15 | 0 of 4 (few runs) | no pass on the skill |
| `problem-framing-doc-payfine-phase2` | problem-framing-doc | 1 regex, 1 file | 3 | 0 of 3 | no | 0.07 | 0.06 | 30 | 0 of 4 (few runs) | no pass on the skill |
| `reliability-requirements-neg-review` | reliability-requirements | 1 tool call | 0 |  | no | 0.10 | 0.00 | 23 (20 + 1) | 0 of 18 | no pass on the skill |
| `reliability-requirements-payfine-phase1` | reliability-requirements | 1 tool call | 2 | 0 of 2 | no | 0.14 | 0.02 | 28 (22 + 7) | 0 of 7 | no pass on the skill |
| `reliability-requirements-payfine-phase2` | reliability-requirements | 1 regex | 3 | 0 of 3 | no | 0.14 | 0.06 | 40 (25 + 6) | 0 of 12 | no pass on the skill |
| `reliability-requirements-payfine-phase2-proceed` | reliability-requirements | 1 regex | 3 | 0 of 3 | no | 0.14 | 0.06 | 42 (45 + 6) | 0 of 11 | no pass on the skill |
| `reliability-requirements-payfine-phase2-stop` | reliability-requirements | 1 regex | 3 | 0 of 3 | no | 0.12 | 0.05 | 23 (10 + 12) | 3 of 11 | no pass on the skill |
| `reliability-requirements-payfine-phase3` | reliability-requirements | 1 regex, 1 file | 7 | 0 of 7 | no | 0.27 | 0.19 | 102 (73 + 20) | 0 of 5 (few runs) | no pass on the skill |
| `reliability-requirements-refusal-phase1` | reliability-requirements | 2 regex, 2 tool call | 0 |  | no | 0.18 | 0.00 | 39 (20 + 0) | 0 of 1 (few runs) | no pass on the skill |
| `reliability-requirements-refusal-phase2` | reliability-requirements | 4 regex, 1 tool call, 1 file | 0 |  | partly: "if you need the skill's own directory again, invoke the skill by name and it prints it" | 0.27 | 0.00 | 52 (50 + 1) | 5 of 9 | no pass on the skill |
| `reliability-review-catalog` | reliability-review | 1 regex, 1 tool call, 1 file | 2 | 0 of 2 | no | 0.24 | 0.06 | 71 | 8 of 34 | no pass on the skill |
| `reliability-review-criterion-no-exit` | reliability-review | 3 regex, 1 tool call, 1 file | 0 |  | no | 0.26 | 0.00 | 59 | 0 of 0 (few runs) | no pass on the skill |
| `reliability-review-fine-payment` | reliability-review | 1 regex, 1 tool call, 1 file | 2 | 0 of 2 | no | 0.23 | 0.10 | 77 | 2 of 24 | no pass on the skill |
| `reliability-review-http` | reliability-review | 3 regex, 1 tool call, 1 file | 4 | 0 of 4 | no | 0.32 | 0.19 | 105 | 1 of 30 | 1 kept: `handed-on` |
| `reliability-review-neg-architecture` | reliability-review | 1 tool call | 0 |  | no | 0.10 | 0.00 | 24 (16 + 1) | 0 of 18 | no pass on the skill |
| `reliability-review-neg-security` | reliability-review | 1 tool call | 0 |  | no | 0.08 | 0.00 | 17 | 0 of 18 | no pass on the skill |
| `reliability-review-nightly` | reliability-review | 1 regex, 1 tool call, 1 file | 4 | 0 of 4 | no | 0.33 | 0.34 | 127 | 7 of 30 | no pass on the skill |
| `reliability-review-nightly-via-agent` | reliability-review | 1 regex, 1 tool call, 1 file | 4 | 0 of 4 | no | 0.48 | 0.32 | 175 | 6 of 32 | no pass on the skill |
| `reliability-review-refund-pr` | reliability-review | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.23 | 0.08 | 66 | 1 of 21 | no pass on the skill |
| `requirements-refinement-open-question` | requirements-refinement | 1 regex, 1 tool call | 3 | 0 of 3 | no | 0.11 | 0.02 | 26 (16 + 6) | 0 of 12 | no pass on the skill |
| `requirements-refinement-owner-sheet` | requirements-refinement | 3 regex, 1 tool call | 1 | 0 of 1 | no | 0.14 | 0.01 | 31 (27 + 3) | 0 of 23 | no pass on the skill |
| `requirements-refinement-payfine-phase1` | requirements-refinement | 1 tool call | 3 | 0 of 3 | no | 0.11 | 0.04 | 28 (19 + 7) | 6 of 23 | no pass on the skill |
| `requirements-refinement-payfine-phase2` | requirements-refinement | 1 regex, 1 file | 7 | 0 of 7 | no | 0.13 | 0.10 | 52 (17 + 20) | 12 of 15 | no pass on the skill |
| `scope-map-self-service` | scope-map | 1 tool call, 1 file | 3 | 0 of 3 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `screen-design-owner-sheet` | screen-design | 2 regex, 1 tool call, 1 file | 1 | 0 of 1 | no | 0.31 | 0.01 | 89 | 1 of 20 | no pass on the skill |
| `screen-design-payfine` | screen-design | 5 regex, 2 tool call, 1 file | 6 | 0 of 6 | no | 0.29 | 0.10 | 108 | 2 of 16 | 1 kept: `changed-states-section` |
| `security-requirements-neg-review` | security-requirements | 1 tool call | 0 |  | no | 0.06 | 0.00 | 12 (10 + 0) | 0 of 16 | no pass on the skill |
| `security-requirements-payfine-phase1` | security-requirements | 1 tool call | 2 | 0 of 2 | no | 0.14 | 0.02 | 33 (27 + 4) | 0 of 13 | no pass on the skill |
| `security-requirements-payfine-phase2` | security-requirements | 1 regex | 3 | 0 of 3 | no | 0.15 | 0.08 | 43 (36 + 6) | 4 of 22 | no pass on the skill |
| `security-requirements-payfine-phase2-proceed` | security-requirements | 1 regex | 3 | 0 of 3 | no | 0.16 | 0.06 | 49 (35 + 6) | 0 of 17 | no pass on the skill |
| `security-requirements-payfine-phase2-stop` | security-requirements | 1 regex | 3 | 0 of 3 | no | 0.12 | 0.04 | 21 (9 + 6) | 0 of 17 | no pass on the skill |
| `security-requirements-payfine-phase3` | security-requirements | 1 regex, 1 file | 7 | 0 of 7 | no | 0.21 | 0.18 | 68 (53 + 15) | 13 of 16 | no pass on the skill |
| `security-requirements-placeholder-pointer` | security-requirements | 5 regex, 1 tool call, 1 file | 1 | 0 of 1 | no | 0.31 | 0.03 | 101 (83 + 3) | 0 of 11 | no pass on the skill |
| `security-requirements-source-criterion` | security-requirements | 3 regex, 2 tool call, 1 file | 1 | 0 of 1 | partly: "nothing from that file may end up in the repository" | 0.29 | 0.03 | 93 (83 + 2) | 0 of 10 | no pass on the skill |
| `security-review-catalog` | security-review | 1 regex, 1 tool call, 1 file | 2 | 0 of 2 | no | 0.19 | 0.06 | 53 | 1 of 20 | no pass on the skill |
| `security-review-config` | security-review | 3 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.32 | 0.18 | 110 | 3 of 25 | 1 kept: `handed-on` |
| `security-review-deferrals-not-restated` | security-review | 4 regex, 1 tool call, 1 file | 0 |  | no | 0.20 | 0.00 | 50 | 5 of 12 | 1 kept: `deferrals-not-restated` |
| `security-review-neg-architecture` | security-review | 1 tool call | 0 |  | no | 0.10 | 0.00 | 23 (18 + 0) | 0 of 16 | no pass on the skill |
| `security-review-neg-reliability` | security-review | 1 tool call | 0 |  | no | 0.11 | 0.00 | 30 | 0 of 18 | no pass on the skill |
| `security-review-portal-pr` | security-review | 1 regex, 1 tool call, 1 file | 4 | 0 of 4 | no | 0.19 | 0.13 | 60 | 3 of 25 | no pass on the skill |
| `security-review-source-value` | security-review | 3 regex, 2 tool call, 1 file | 1 | 0 of 1 | no | 0.15 | 0.02 | 32 | 0 of 18 | no pass on the skill |
| `slice-build-cancel-hold` | slice-build | 10 regex, 4 tool call, 2 tool order | 0 |  | no | 0.75 | 0.00 | 136 (134 + 1) | 1 of 6 | no pass on the skill |
| `staleness-audit-docs` | staleness-audit | 1 tool call | 4 | 0 of 4 | no | 0.12 | 0.07 | 40 | 3 of 7 | no pass on the skill |
| `supply-chain-review-accept-phase1` | supply-chain-review | 1 tool call | 2 | 0 of 2 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `supply-chain-review-accept-phase2` | supply-chain-review | 0 | 3 | 0 of 3 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `supply-chain-review-accepted` | supply-chain-review | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.20 | 0.12 | 70 | 1 of 4 (few runs) | no pass on the skill |
| `supply-chain-review-build` | supply-chain-review | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.21 | 0.11 | 98 | 1 of 7 | no pass on the skill |
| `supply-chain-review-build-via-agent` | supply-chain-review | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.34 | 0.15 | 111 | 0 of 3 (few runs) | no pass on the skill |
| `supply-chain-review-neg-reliability` | supply-chain-review | 1 tool call | 0 |  | no | 0.10 | 0.00 | 19 | 0 of 16 | no pass on the skill |
| `supply-chain-review-neg-security` | supply-chain-review | 1 tool call | 0 |  | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `supply-chain-review-workflows` | supply-chain-review | 1 regex, 1 tool call, 1 file | 2 | 0 of 2 | no | 0.20 | 0.09 | 70 | 0 of 4 (few runs) | no pass on the skill |
| `tdd-implementation-lite-cancel-hold` | tdd-implementation-lite | 13 regex, 2 tool call, 4 tool order, 1 file | 6 | 0 of 6 | no | 0.41 | 0.10 | 97 | 30 of 30 | no pass on the skill |
| `tdd-implementation-lite-cancel-hold-via-agent` | tdd-implementation-lite | 14 regex, 2 tool call, 2 tool order, 1 file | 6 | 0 of 6 | no | 0.39 | 0.10 | 116 | 42 of 42 | no pass on the skill |
| `tdd-implementation-lite-checks-before-commit` | tdd-implementation-lite | 7 regex, 3 tool call | 0 |  | no | 0.27 | 0.00 | 42 (37 + 3) | 0 of 1 (few runs) | 1 kept: `checks-before-commit` |
| `tdd-implementation-lite-chunk-plan` | tdd-implementation-lite | 3 regex, 2 tool call, 1 file | 2 | 0 of 2 | partly: "Write the chunk plan [...] and build nothing" | 0.19 | 0.06 | 53 | 14 of 29 | no pass on the skill |
| `tdd-implementation-lite-fix-test-renamed` | tdd-implementation-lite | 7 regex, 2 tool call, 1 tool order | 0 |  | no | 0.23 | 0.00 | 31 (22 + 4) | 0 of 1 (few runs) | no pass on the skill |
| `tdd-implementation-lite-named-fix` | tdd-implementation-lite | 8 regex, 2 tool call, 1 file | 3 | 0 of 3 | no | 0.36 | 0.03 | 76 | 11 of 38 | no pass on the skill |
| `tdd-implementation-lite-one-chunk` | tdd-implementation-lite | 8 regex, 3 tool call, 1 tool order | 4 | 0 of 4 | partly: "Chunks are committed." | 0.30 | 0.05 | 59 (44 + 8) | 7 of 32 | no pass on the skill |
| `tdd-implementation-lite-rename-fix` | tdd-implementation-lite | 10 regex, 3 tool call, 1 file | 0 |  | no | 0.26 | 0.00 | 38 | 6 of 31 | no pass on the skill |
| `technology-bootstrap-phase1` | technology-bootstrap | 1 tool call | 2 | 0 of 2 | no | 0.10 | 0.02 | 25 (16 + 7) | 1 of 20 | no pass on the skill |
| `technology-bootstrap-phase2` | technology-bootstrap | 5 regex | 3 | 0 of 3 | partly: "pick the one where that's the default [...] Give me your recommendations for the whole set in one message rather than one at a time" | 0.15 | 0.10 | 71 (59 + 8) | 13 of 30 | no pass on the skill |
| `technology-bootstrap-phase3` | technology-bootstrap | 3 regex, 1 file | 4 | 0 of 4 | no | 0.15 | 0.18 | 42 (21 + 18) | 12 of 28 | 1 kept: `gate-checks-recorded` |
| `technology-bootstrap-phase3-reject` | technology-bootstrap | 1 regex, 1 file | 5 | 0 of 5 | no | 0.18 | 0.20 | 60 (35 + 10) | 10 of 22 | no pass on the skill |
| `test-quality-review-fines` | test-quality-review | 3 regex, 1 tool call, 1 file | 5 | 0 of 5 | no | 0.19 | 0.25 | 81 | 17 of 33 | 1 kept: `handed-on` |
| `test-quality-review-neg-code-review` | test-quality-review | 1 tool call | 0 |  | no | 0.11 | 0.00 | 27 | 0 of 19 | no pass on the skill |
| `test-quality-review-reminders` | test-quality-review | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.15 | 0.06 | 42 | 0 of 17 | no pass on the skill |
| `test-quality-review-seam-fake` | test-quality-review | 3 regex, 1 tool call, 1 file | 3 | 0 of 3 | partly: "Write your report in the shared finding format [...] and hand back the counts and the path" | 0.20 | 0.06 | 45 | 2 of 33 | no pass on the skill |
| `test-quality-review-survivors-at-d` | test-quality-review | 5 regex, 1 tool call, 1 file | 0 |  | no | 0.23 | 0.00 | 59 | 1 of 8 | 1 kept: `survivors-read` |
| `user-facing-docs-renewals` | user-facing-docs | 1 tool call, 1 file | 2 | 0 of 2 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `user-story-writeup-payfine-phase1` | user-story-writeup | 1 tool call | 1 | 0 of 1 | no | 0.06 | 0.01 | 12 (7 + 2) | 0 of 12 | no pass on the skill |
| `user-story-writeup-payfine-phase2` | user-story-writeup | 1 regex, 1 file | 3 | 0 of 3 | partly: "Don't create the issue yourself" |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `vertical-slicing-handback` | vertical-slicing | 1 tool call | 3 | 0 of 3 | no | 0.16 | 0.02 | 51 (32 + 5) | 1 of 23 | no pass on the skill |
| `vertical-slicing-no-requirements` | vertical-slicing | 1 regex, 1 tool call | 2 | 0 of 2 | no | 0.09 | 0.01 | 15 (5 + 4) | 0 of 17 | no pass on the skill |
| `vertical-slicing-no-screen` | vertical-slicing | 1 regex, 1 tool call, 1 file | 1 | 0 of 1 | no | 0.17 | 0.02 | 42 (24 + 5) | 1 of 23 | no pass on the skill |
| `vertical-slicing-owner-sheet` | vertical-slicing | 3 regex, 2 tool call, 1 file | 2 | 0 of 2 | no | 0.17 | 0.02 | 45 (42 + 5) | 3 of 37 | no pass on the skill |
| `vertical-slicing-payfine-phase1` | vertical-slicing | 1 regex, 2 tool call, 1 file | 5 | 0 of 5 | no | 0.15 | 0.06 | 45 (25 + 8) | 1 of 17 | no pass on the skill |
| `vertical-slicing-thinnest-cut` | vertical-slicing | 5 regex, 1 tool call, 1 file | 0 |  | no | 0.16 | 0.00 | 28 (28 + 0) | 1 of 5 (few runs) | no pass on the skill |
| `why-comments-collect-fine` | why-comments | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.08 | 0.04 | 25 | 0 of 8 | no pass on the skill |

**One run of every case:** $72.63 over the 191 cases with a completed run held (agent $63.82, judges $8.81, 12% judges); $72.63 over the 191 with a run since 2026-11-10. 12 cases have no completed run held and are not priced.

**Graders:** 357 judges and 1073 tool checks over 203 cases; 69 cases have no judge.

**Judges a tool could decide:** 0 of 357, in 0 cases; 0 cases would be left with no judge. Their share of the judge cost, split evenly within each case (an estimate): $0.00 per run of every case.

**Runs that failed only on a judge:** of 4417 completed runs since the bars, 949 failed; 541 of those failed on judges alone, and 0 on judges a tool could decide alone ($0.00 of runs at today's cost per run): none.

**Prompt states the rule it grades:** yes 3, partly 46, no 154.

**Never failed since the bar (6 or more runs):** 52 cases, $11.71 of one run of every case. **Never failed and $0.40 or more a run (6, $3.67):** `chunk-runner-fix-gate-fails` $1.16, `orchestrator-last-fix-review-at-d` $0.66, `chunk-runner-gate-outside` $0.57, `delivery-screens-owed` $0.46, `external-review-triage-cancel-hold` $0.42, `orchestrator-autopilot-question` $0.41.

By skill (one run of each of its cases; the judges a tool could decide and their estimated share):

| Skill | Cases (priced) | Agent $ | Judges $ | Judges | A tool could decide | Their share $ | Prompts stating the rule (yes, partly) | Never failed |
|---|---|---|---|---|---|---|---|---|
| orchestrator | 54 (54) | 31.11 | 0.39 | 50 | 0 | 0.00 | 0, 23 | 9 |
| chunk-runner | 12 (12) | 7.42 | 0.02 | 0 | 0 | 0.00 | 1, 6 | 2 |
| reliability-review | 9 (9) | 2.27 | 1.09 | 19 | 0 | 0.00 | 0, 0 | 2 |
| tdd-implementation-lite | 8 (8) | 2.41 | 0.34 | 21 | 0 | 0.00 | 0, 2 | 0 |
| architecture-review | 8 (8) | 1.76 | 0.90 | 20 | 0 | 0.00 | 0, 1 | 4 |
| code-review | 9 (9) | 1.64 | 0.81 | 26 | 0 | 0.00 | 0, 1 | 1 |
| reliability-requirements | 10 (10) | 1.63 | 0.43 | 20 | 0 | 0.00 | 1, 1 | 4 |
| accessibility-review | 5 (5) | 1.20 | 0.67 | 13 | 0 | 0.00 | 1, 3 | 1 |
| security-requirements | 8 (8) | 1.45 | 0.43 | 20 | 0 | 0.00 | 0, 1 | 6 |
| architecture-design | 7 (7) | 1.40 | 0.38 | 14 | 0 | 0.00 | 0, 1 | 3 |
| security-review | 7 (7) | 1.25 | 0.38 | 10 | 0 | 0.00 | 0, 0 | 3 |
| supply-chain-review | 8 (5) | 1.06 | 0.47 | 16 | 0 | 0.00 | 0, 0 | 1 |
| design-system | 5 (5) | 0.98 | 0.37 | 15 | 0 | 0.00 | 0, 0 | 3 |
| delivery | 3 (3) | 1.31 | 0.03 | 3 | 0 | 0.00 | 0, 2 | 1 |
| test-quality-review | 5 (5) | 0.88 | 0.37 | 11 | 0 | 0.00 | 0, 1 | 2 |
| technology-bootstrap | 4 (4) | 0.59 | 0.50 | 14 | 0 | 0.00 | 0, 1 | 0 |
| vertical-slicing | 6 (6) | 0.91 | 0.12 | 13 | 0 | 0.00 | 0, 0 | 1 |
| slice-build | 1 (1) | 0.75 | 0.00 | 0 | 0 | 0.00 | 0, 0 | 0 |
| screen-design | 2 (2) | 0.60 | 0.11 | 7 | 0 | 0.00 | 0, 0 | 0 |
| ci-pipeline | 2 (2) | 0.69 | 0.00 | 0 | 0 | 0.00 | 0, 0 | 0 |
| requirements-refinement | 4 (4) | 0.49 | 0.18 | 14 | 0 | 0.00 | 0, 0 | 2 |
| map-update | 1 (1) | 0.17 | 0.49 | 3 | 0 | 0.00 | 0, 0 | 0 |
| cold-read | 2 (2) | 0.44 | 0.00 | 0 | 0 | 0.00 | 0, 0 | 0 |
| external-review-triage | 1 (1) | 0.35 | 0.07 | 3 | 0 | 0.00 | 0, 1 | 1 |
| domain-model | 2 (2) | 0.21 | 0.00 | 0 | 0 | 0.00 | 0, 1 | 0 |
| problem-framing-doc | 2 (2) | 0.13 | 0.07 | 5 | 0 | 0.00 | 0, 0 | 0 |
| map-query | 2 (2) | 0.17 | 0.04 | 5 | 0 | 0.00 | 0, 0 | 1 |
| staleness-audit | 1 (1) | 0.12 | 0.07 | 4 | 0 | 0.00 | 0, 0 | 0 |
| operational-readiness | 6 (2) | 0.16 | 0.00 | 13 | 0 | 0.00 | 0, 0 | 2 |
| why-comments | 1 (1) | 0.08 | 0.04 | 3 | 0 | 0.00 | 0, 0 | 1 |
| adr | 2 (1) | 0.08 | 0.01 | 2 | 0 | 0.00 | 0, 0 | 0 |
| acceptance-criteria | 1 (1) | 0.07 | 0.01 | 1 | 0 | 0.00 | 0, 0 | 1 |
| user-story-writeup | 2 (1) | 0.06 | 0.01 | 4 | 0 | 0.00 | 0, 1 | 1 |
| pr-writeup | 1 (0) |  |  | 3 | 0 | 0.00 | 0, 0 | 0 |
| scope-map | 1 (0) |  |  | 3 | 0 | 0.00 | 0, 0 | 0 |
| user-facing-docs | 1 (0) |  |  | 2 | 0 | 0.00 | 0, 0 | 0 |

**Judges a tool could decide, with the reason** (the judges that take reading have theirs in `tools/case_reading.json`):

| Case | Judge | What a tool would read | Share of a run $ |
|---|---|---|---|

**Prompts that state the rule they grade:**

| Case | The prompt's words | What they give away |
|---|---|---|
| `accessibility-review-ac-walk` | yes: "Start it through the scratch launcher `tools/scratch_run.py` with the scratch folder `scratch/portal-walk` next to the project [...] and `PORTAL_DATA` inside that folder" | the launcher, the scratch folder and the data directory are what `app-started-through-the-launcher` and `app-never-started-bare` grade; "in its criteria-walk mode" and "Hand back the counts and the path" are the orchestrator's launch text |
| `accessibility-review-design-notes` | partly: "the declined message must read exactly "Your card was declined. Try another card." and a screen reader user has to be told as soon as it appears" | the designer's two requirements are given; it does not say that one is a design note and the other a criterion |
| `accessibility-review-payfine` | partly: "fill in the slice's accessibility placeholder" | tells the run the slice file has to change, which `slice-placeholder-filled` grades; how (a one-line pointer, nothing else touched) is left to the skill |
| `accessibility-review-payfine-subtle` | partly: "fill in the slice's accessibility placeholder" | as `accessibility-review-payfine` |
| `architecture-design-payfine-via-agent` | partly: "its architecture map is at `docs/architecture-map.md`" | points the run at the map, and `consults-map-query` grades that the map was consulted; the agent named is the path the case exists to run |
| `chunk-runner-fix-gate-fails` | partly: "Stop once round 1 is recorded" | the resume line names the step the round stopped at and the handoff holds the facts; the stopping point bounds the run. The stop names round 1's recording, which `round-one-recorded-with-the-range` grades by its `--range`, not by its happening. |
| `chunk-runner-gate-deviation` | partly: "Stop once the gate has run and its result is known, before any launch" | reworded in E5: the resume line names the state ("no gate has run on that commit"). The stopping point is left: it bounds the run's cost, and it is what `no-fixer-no-reviewer` grades; the module directories and deviation zone are handed-over facts, not the rule. |
| `chunk-runner-gate-outside` | partly: "Stop once the gate has passed, before any reviewer is launched" | reworded in E5: the resume line names the state. The stopping point is left (it bounds the run's cost): it says to go on until the gate passes and to launch no reviewer, `gate-run-twice` and `no-reviewer-before-the-pass` |
| `chunk-runner-gate-sources` | partly: "Stop once the gate has passed, before any reviewer is launched" | as `chunk-runner-gate-outside`; the prompt also says the target directory holds `sources.md`, which points at `--planning` |
| `chunk-runner-one-fix-round` | partly: "the sandbox checks in this round are information and never end it" | reworded in E5: the resume line names the state ("round 1 is not recorded yet") and no longer the action `round-one-recorded-with-the-range` grades. What is left is a handed-over fact the E2 pass found the run follows instead of the skill's sentence. Naming the skill to invoke is the launch, not a leak. Since 0.15.1 the resume line names only the step ("after the re-reviewer's hand-back") and the fixture's handoff names the step, not the command. |
| `chunk-runner-review-round` | partly: "Stop once round 0 is recorded [...] don't start the fix round" | reworded in E5: the resume line names the state ("no reviewer and no smoke agent has been launched") and no longer the two launches. The stopping point is left (it bounds the run's cost) and still names the recording `round-recorded-by-the-script` grades; the hand-over names `scratch_run.py`, which `smoke-agent-handed-the-launcher` grades |
| `chunk-runner-waits-for-handback` | yes: "end after step 2, the gate on the builder's commit (and its one fixer, if the gate fails). Launch no reviewer and no smoke agent" | `no-reviewer-launched` and `gate-on-the-builders-commit` grade what the stopping point says. The case starts at the build and has no resume line, so E5 reworded nothing here: the stopping point is the run's bound. |
| `code-review-comments-chunk` | partly: "Write one report in the shared finding format [...] and hand back the counts and the path" | the reply's content is what `hands-back-counts-and-path` grades; the rest is the orchestrator's launch text for a chunk reviewer, and "Touches: storage" is the state that should bring the reliability lens |
| `delegation-consult-with-file` | yes: "Decide it, revise your document in place, commit it by name as `Decision <n>: <title>`, and hand back the commit hash and one sentence" | every tool check and the hand-back judge grade what this sentence says; it is the orchestrator's task text, and the same words in `delegation-consult-without-file` are what must be refused, so here the case shows only that the file's presence does not stop the run |
| `delivery-ci-red-not-done` | partly: "This session may launch no agent: when the next action is a launch, write the handoff file for it (what the agent is to be handed, word for word where the skill gives words) and stop there" | `nothing-launched` grades what the prompt forbids, and the handoff the judge reads is asked for; that red checks are read and are not "done" is left to the skill |
| `delivery-screens-stray` | partly: "This session may launch no agent: when the next action is a launch, write the handoff file for it (what the agent is to be handed, word for word where the skill gives words) and stop there" | as `delivery-ci-red-not-done`: the handoff is asked for; that the screens check has a verdict to read, and that a stray state is no baseline, is left to the skill |
| `domain-model-bank-phase2` | partly: "What you would ask me, answered: a connection that the bank or the vendor has ended for good, with no way out in the app, stays unsupported for now." | the owner's answer is given so the run reaches the document; it does not say what the table holds, which states to find, or that a source not read is `to verify` |
| `external-review-triage-cancel-hold` | partly: "Write your report to [...] and hand back the counts and the path" | the reply's content is what `hands-back-counts-and-path` grades; it is the orchestrator's launch text |
| `library-app-lending-review-via-agent` | partly: "return its findings report verbatim [...] (including its opening section on the importance ordering it assumed)" | tells the run the report has an importance-ordering section, which `states-assumed-importance-ordering` grades; the agent named is the path the case exists to run |
| `orchestrator-autopilot-counts-over` | partly: "hand off as soon as the next chunk's runner has been launched" | the bound names the launch the case grades; without the stop the run would be a whole chunk. The state's `autopilot.md` states the rule in the owner's words, as a real project's file does, so no deletion from the skill makes the case fail. |
| `orchestrator-autopilot-recorded` | partly: "And yes to autopilot: take your own recommendation at the stops the chunk loop would otherwise put to me, and log each one" | the owner's answer is the state; the file, its name and what it holds are left to the skill |
| `orchestrator-autopilot-round` | partly: "Hand off as soon as the next agent has been launched" | the bound names a launch, not which one; that a standing High gets a verification and not a stop is left to the skill. The state's `autopilot.md` says yes and names no stop |
| `orchestrator-capture-states` | partly: "This session may launch no agent: when the next action is a launch, write the handoff file for it (what the agent is to be handed, word for word where the skill gives words) and stop there" | `nothing-launched` grades what the prompt forbids and the handoff is asked for; that a listed state needs a capture before the push is left to the skill |
| `orchestrator-chunk-runner-handback` | partly: "hand off once chunk 1's C line is written and its records committed, before chunk 2's runner is launched" | names the two actions `c-line-written-from-the-hand-back` and `records-committed-by-name` grade, and the stop `nothing-launched` grades; what goes on the line is left to the skill |
| `orchestrator-chunk-runner-launch` | partly: "hand off as soon as chunk 1's runner has been launched: don't wait for it to return; write the handoff file saying the runner is in flight and stop" | says a runner is what gets launched (`one-chunk-runner-launched`) and dictates the handoff's content, which is all the judge reads |
| `orchestrator-definition-of-done` | partly: "hand off before the slice reviewers are launched (after the Definition of Done has been acted on and checked again)" | "checked again" is `definition-of-done-checked-twice`; the stop is `no-slice-reviewer-yet` |
| `orchestrator-delivery-removal` | partly: "If the scan finds anything of that file in this branch's commits, replace it and rewrite the branch before it is pushed. You have my word for that rewrite" | the owner's word is an input the procedure requires, but "scan", "rewrite" and "before it is pushed" are also what `every-commit-scanned-before-and-after`, `branch-rewritten-by-the-script` and `rewrite-before-the-push` grade |
| `orchestrator-issue-fix-records` | partly: "Hand off as soon as the chunk loop's A line is written (write the handoff file and stop; don't start B in this session)" | the stop is `nothing-launched`, the handoff file is `handoff-carries-the-issue-prefix`; "Issue #14 is the one I told you to fix first on its own branch" is the owner's earlier answer, an input |
| `orchestrator-last-fix-review-at-d` | partly: "Hand off as soon as the next agent has been launched" | the bound names a launch, not which one; that the second fix is read once on its diff is left to the skill |
| `orchestrator-mutation-before-review` | partly: "hand off when the next thing to do is launching round 0 of the slice review itself" | the stopping point bounds the run; the handoff file says the Definition of Done is behind and "the rest of D", and names no mutation pass |
| `orchestrator-plan-check-seam` | partly: "hand off once the B line is written, before chunk 1's build" | the stop is `no-builder-launched` and the B line is `b-line-written`; that a failed plan goes back to a planner is left to the skill |
| `orchestrator-planning-row` | partly: "do everything up to the first `git push`, don't push, and tell me what you would push and what happens after" | the stop before the push is given because the fixture has no network; it does not say the plan gets a pull request of its own, or the order of branch and gate |
| `orchestrator-readiness-gate` | partly: "Hand off as soon as the chunk loop's A line is written (write the handoff file and stop; don't start B in this session)" | the stop is `no-builder-while-the-gate-fails`; the delegation and sandbox sentences are the owner's answers, inputs |
| `orchestrator-readme-stale-not-done` | partly: "hand off before the slice reviewers are launched (after the Definition of Done has been acted on and checked again)" | as `orchestrator-definition-of-done` |
| `orchestrator-recommended-not-asked` | partly: "a problem you find in code that is already there is for a later slice, not this one, and a risk the design leaves standing I accept for now" | the two answers that are the owner's (a problem in older code, a risk left standing) are given so the run reaches the save; it does not say that design questions with a recommended option are taken |
| `orchestrator-route-open-pr` | partly: "Report what is open and stop after your first question to me; don't run the triage or any fix in this session" | "what is open" points at the tracker (`asks-the-tracker-for-open-pull-requests`, `-issues`), and the stop is `nothing-launched` and `no-planning-skill-invoked` |
| `orchestrator-runner-handback-unverified` | partly: "This session may launch no agent: when the next action is a launch, write the handoff file for it and stop there" | `nothing-launched` grades what the prompt forbids; that the line's hash is checked is left to the skill |
| `orchestrator-slice-review-launches` | partly: "hand off as soon as round 0 of the slice review has been launched" | the bound names the launches the case grades by their text; the harness lets the six agents finish, so a run costs about $4 |
| `orchestrator-solo-build-launch` | partly: "hand off as soon as the next agent has been launched" | says an agent is launched and the session ends there; not which agent, on which model, with which skill, or that no plan is asked for |
| `orchestrator-solo-confirmed-only` | partly: "Hand off as soon as the next agent has been launched" | says an agent is launched next; not that it is a fixer, what it is handed or what is kept from it |
| `orchestrator-solo-from-message` | partly: "Build this slice solo: one builder for the slice." | the owner's word for the cadence is the input, so it is given; nothing says the A line carries it, that no plan is written or what the handoff names next |
| `orchestrator-solo-nothing-confirmed` | partly: "Hand off as soon as the slice review's line is written in the log, or as soon as an agent has been launched, whichever comes first" | allows either ending, the review's line or a launch, so it does not say that nothing is launched |
| `reliability-requirements-refusal-phase2` | partly: "if you need the skill's own directory again, invoke the skill by name and it prints it" | the approval and the save path; the sentence about invoking the skill again gives the script's directory, which a resumed session cannot resolve, and not that the check is run |
| `security-requirements-source-criterion` | partly: "nothing from that file may end up in the repository" | the owner's words are the criterion the judge's first half looks for; that the scan is run on writing it and the hit routed back is left to the skill |
| `tdd-implementation-lite-chunk-plan` | partly: "Write the chunk plan [...] and build nothing" | "build nothing" is what `writes-only-the-report` and `stops-after-the-plan` grade; it is the orchestrator's launch text for the planner |
| `tdd-implementation-lite-one-chunk` | partly: "Chunks are committed." | one of the two lines the orchestrator's launch carries to a builder, and what `commits` grades; "and only that chunk" is the task |
| `technology-bootstrap-phase2` | partly: "pick the one where that's the default [...] Give me your recommendations for the whole set in one message rather than one at a time" | the first is the defaults-over-flags rule `pinning-posture-treated-as-a-choice` grades, in the user's mouth; the second asks for the one-message set `recommends-the-built-in-default-set-once` grades |
| `test-quality-review-seam-fake` | partly: "Write your report in the shared finding format [...] and hand back the counts and the path" | the reply's content is what `hands-back-counts-and-path` grades; the rest is the orchestrator's launch text for the test-quality lens |
| `user-story-writeup-payfine-phase2` | partly: "Don't create the issue yourself" | the user's answer, and exactly what `does-not-file-it` grades |

**Grader findings** (described, none fixed):

- `architecture-design-payfine-phase2`: `decisions-show-approval` (judge) failed 19 of 25 runs.
- `chunk-runner-gate-outside`: `allow-list-not-widened` (`--allow[ =]+[\x27"]?utils/`, not_contains on the trace): a double quote is `\"` in the trace's JSON, so `--allow "utils/..."` is not matched; only the bare and single-quoted forms are. Read from the pattern, not seen in a run.
- `chunk-runner-gate-outside`: Nothing reads whether the runner edited code itself: a nested fixer's Edit calls are in the runner's trace too, so a trace regex cannot tell them apart (the comment in the case says so since E5).
- `chunk-runner-review-round`: `cold-findings-cite-no-planning-document` lists `design\.md`, but the fixture's documents are `design-001.md`, `requirements-001.md` and `user-story-001.md`: a finding citing any of those three is not seen (only `slice-001.md` is).
- `chunk-runner-review-round`: `hand-back-line-carries-the-script-counts` reads the trace with `[^\n]`, as `chunk-runner-gap-handback`'s regex does: the parts need only sit in one tool result or message, not on one line of the reply.
- `code-review-fine-notices-pr-via-agent`: `consults-why-comments` failed 18 of 20 runs. Its trace regex wants the exact form `"name":"Skill","input":{"skill":"kad-dev-team:why-comments"`, stricter than the `"skill": ?"..."` form the tdd via-agent case uses for the same kind of nested call; whether the agent skips the consult or the form misses it was not checked. `leaves-mocking-to-test-quality-review` (judge) failed 16 of 17 here against 5 of 13 in the direct case.
- `code-review-structural-high-at-d`: `a-long-single-job-function-stays-a-plain-finding` (judge) failed 6 of 7 runs before E7 rewrote it as a trap on the size alone.
- `delivery-ci-red-not-done`: `failing-tests-written-to-the-records` matches the test's name within 6,000 characters after any Write or Bash call that names `pr-ci-r1.md`, so the failed job's log printed by a later command passes a run that wrote the file without the test names.
- `delivery-screens-owed`: `baselines-adopted-by-the-script` does not fail with the skills' screens text removed: the project's own copy of `screen_check.py` documents `adopt`, and runs found it.
- `map-update-cancel-hold`: `pre-existing-flags-not-new` (judge) failed 13 of 18 runs.
- `orchestrator-autopilot-counts-over`: No known-bad reference: with the skill's autopilot text on the counts removed, the run still went on to chunk 2 in 3 runs of 3, from the fixture's `autopilot.md`.
- `orchestrator-autopilot-question`: Its reference loses runs to the clock: with no question the run builds the slice. Three clean runs over two passes, all failing.
- `orchestrator-autopilot-recorded`: `autopilot-file-written` does not fail with the A.2 bullet removed: the skill's Autopilot paragraph still names the file and the owner said yes. The file's content does fail.
- `orchestrator-budget-exceeded`: Its judge `flow-ends-saying-what-is-built` failed 30 of 43 runs and, on 2026-11-16, three votes of three on a reply that was right; it is the regex `flow-ends-on-the-clock-and-says-what-is-built` since 0.15.1.
- `orchestrator-definition-of-done`: `three-named-fixes-in-one-batch` (judge) failed 57 of 65 completed runs held; the coverage table says it fails replies that report exactly the three fixes. A grader that fails nearly every run tells a broken run from a good one no better than one that never fails.
- `orchestrator-delivery-foreground`: `body-carries-the-deferrals-section` (0.15.0) passes on the script's file spliced into the body command or on the heading written out; a body built in two commands with the splice in a third, alone, would pass on the splice without the body
- `orchestrator-issue-fix-records`: `branch-names-the-slice-and-the-issue` allows a quote before the branch name (`['"]?`), but a double quote is `\"` in the trace's JSON, so `git switch -c "slice-001-issue14-..."` would not match and a correct run would fail. Read from the pattern; the one failure held (2026-11-12) was a run that created no branch.
- `orchestrator-issue-fix-records`: `handoff-carries-the-issue-prefix` matches the file name within 1,500 characters after the start of any Write or Bash call, so a later call or a tool result that names it passes a run that never wrote it.
- `orchestrator-readiness-correction-autopilot`: The skill's exact bullet (`taken as recommended: <check> (autopilot)`) was not written on the first run; the grader reads the route's log entry instead.
- `orchestrator-readme-stale-not-done`: `three-named-fixes-in-one-batch` (judge), the same criterion family as `orchestrator-definition-of-done`'s, failed 7 of 8 runs.
- `orchestrator-route-backward-requirements`: The `stops-after-the-routed-step` criteria come in two wordings: nine cases say "exactly one routed step per invocation ... asks whether to continue; it never chains" (this one, `orchestrator-route-design`, `-design-system`, `-implementation`, `-implementation-prenamed`, `-problem-framing`, `-reliability`, `-tech-bootstrap`, `-user-story`), four say it "continues to the next row in the same conversation" (`-accessibility`, `-scope-decision`, `-screen-design`, `-slicing`). The nine fail a run the four pass; which is the skill's rule today was not checked here.
- `requirements-refinement-payfine-phase2`: `finishes-without-reasking` (judge) failed 8 of 9 runs.
- `security-requirements-payfine-phase3`: `decisions-all-approved` (judge) failed 10 of 15 runs; its criterion pins phase 2's forks from the frozen history and says to re-pin them after a re-freeze.
- `tdd-implementation-lite-cancel-hold`: `test-run-after-each-test-edit` failed 15 of 15 runs here and 30 of 30 in the via-agent twin. It is marked a measurement ("the rate is the finding"), and the rate is settled at zero: it now only lowers both cases' scores.
- `tdd-implementation-lite-rename-fix`: `new-name-in-every-caller` reads only `main/jobs.ts`: the new name in `main/server.ts` and `lending/return-book.ts` is not checked (the old name's absence there is).
<!-- case-sort:end -->

**What the sorting says.** Nothing here is decided; each line is for the
owner. (Written at E4, 2026-11-14, and left as written: the figures in
this list and in "The order for E5" are from before E5, which has since
replaced the 36 judges of groups 1 to 4 and reworded six prompts; see
"Judges turned into tool checks". The table above is regenerated and
shows the suite as it is now.)

1. *Turning judges into tool checks saves little money and some noise.*
   51 of 471 judges could be tool checks. Their share of the judge cost
   is about $0.77 a pass (1.7%), an estimate: a result holds one judge
   cost per run, split here evenly over the case's judges. The other 420
   judges take reading, and they are where the judge money is: the review
   skills' "did it find the planted problem" and "is this a false alarm"
   judges. The better reason to replace the 51 is noise: 72 completed
   runs since the bars failed on those judges alone, which is 12% of all
   failed runs. Two thirds of all failed runs (419 of 623) failed on
   judges alone, replaceable or not; that figure includes real catches,
   since a review that misses a planted problem fails only a judge.
2. *The money is in the agent's own runs.* 82% of a pass. A pass gets
   cheaper by running fewer or shorter cases (E6 and E7), not by E5.
   Four cases cost over $1 a run, all of them cases that launch agents:
   `orchestrator-chunk-runner-launch` $1.76, `chunk-runner-review-round`
   $1.20, `orchestrator-readme-stale-not-done` $1.12,
   `orchestrator-definition-of-done` $1.10.
3. *`orchestrator-chunk-runner-launch` pays for a round nobody grades.*
   Its graders read the launch and the handoff file; because a launch
   blocks under the eval, the launched runner then runs its whole round
   (279 s a run). Ending the case at the launch would save most of its
   $1.76, perhaps $1.50 a pass (3%). A guess: the orchestrator's own
   share of the run was not measured, and the CLI may offer no way to
   stop a launched agent early.
4. *Nine prompts state the rule they grade and 23 state part of it.* The
   nine are seven `chunk-runner` cases (the resume line names the next
   action, as the deletion pass found), `accessibility-review-ac-walk`
   (the prompt gives the launcher, the scratch folder and the data
   directory) and `delegation-consult-with-file` (the prompt gives the
   revision, the commit name and the hand-back). The 23 are mostly a
   stopping point ("hand off once the B line is written") or the
   orchestrator's own launch sentence ("hand back the counts and the
   path"). Rewording saves nothing and may cost a little, since the run
   then has to find the action itself; what it buys is a case that can
   fail when the rule goes. The seven `chunk-runner` cases would then owe
   their deletions again, about 40 to 60 runs, a guess from the pass's
   own counts.
5. *The `-via-agent` cases repeat their twin's judges.* Six cases, five
   priced at $2.53 a pass together, $0.82 of it judges. Keeping the path
   check and two judges in each would save about $0.59 a pass (1.3%), a
   guess from the even split. They are not candidates to retire: two of
   them fail a grader far more often than their direct twin
   (`code-review-fine-notices-pr-via-agent` fails `consults-why-comments`
   in 18 of 20 runs against 2 of 13;
   `tdd-implementation-lite-cancel-hold-via-agent` fails `final-review-runs`
   in 11 of 30 against none of 15), so the agent path does behave
   differently, unless the first is the grader's form (see the findings).
6. *Never failed and costly: seven cases, $3.39 a pass (7.4%).* Listed
   under the table. Only two have a deletion result,
   `chunk-runner-gate-outside` (0 of 10 deletions failed it) and
   `chunk-runner-replay-not-the-handback` (0 of 4): $1.01 a pass (2.2%)
   if both went. The other five are review cases with no deletion pass
   and no bare-model run, so by E7's own rule they are not candidates
   yet. All 62 never-failed cases together are $14.23 a pass (31%), the
   ceiling on what E7 can retire, not an estimate of it.
7. *Twelve graders fail in most of their runs.* Listed in the findings.
   A grader that fails nearly every run separates a good run from a
   broken one no better than one that never fails, and each is a re-run
   waiting to happen when its case's bar moves.

**The order for E5**, by noise removed first and certainty of the
replacement:

1. `chunk-runner`'s six judges on a hand-back line, the two E5 names
   first (`stops-with-the-decision-on-the-line`,
   `hand-back-is-the-one-line`), together with the seven prompts
   reworded, since both change the same case files and one gate run
   covers them.
2. The five hand-back judges on a short reply in other skills
   (`hands-back-counts-and-path` three times,
   `hands-back-the-hash-and-one-sentence`, `ends-on-the-hand-back-line`).
3. The eight counts and names on a reply: `no-criteria-before-approval`
   four times and `no-criteria-written` twice, whose criteria already
   state a number, `no-live-scan-answer` and `uses-what-the-map-found`.
4. The 17 judges on a file's shape or contents (the chunk plan's shape
   and its seam tests, the reflog's two lines, the requirements
   template's headings, the slice's placeholder line, the ADR's banned
   names, three of `map-update`'s seven, the constructor and wiring
   checks). Some need the per-case script E5 describes: a count of chunk
   entries or a comparison with the fixture's earlier map is not one
   regex.
5. Last, and only if wanted: the 15 judges on the orchestrator's log
   (`log-names-row-and-artifact` eleven times and four like it). A regex
   holds the destination and the artifact path and loses the state's
   wording. They are the least certain of the 51.

**The skills E6 should take first.** By money and by how many of the
skill's cases have never failed, which is where a bare model matching the
skill would free the most: `architecture-review` (11 cases, $3.59, 8
never failed), `security-review` (8, $2.22, 6 never failed), then
`reliability-review` (10, $4.14, the most judge money of any skill),
`code-review`, `security-requirements` (6 of 8 never failed) and
`reliability-requirements`, then the design skills. Two limits read from
the cases: the 21 cases that resume a `history.jsonl` carry the skill's
text inside the history, so "without the plugin" is not without the skill
there, and E6 can measure only the first-turn cases of those skills; and
16 of the 17 negative-trigger cases already grade both arms (`arm: both`;
`adr-neg-rename` does not), $1.39 a pass for the 17, so they need no E6
run.

**`orchestrator` and `delivery`: which rules a grader could notice.**
`TODO.md` asks this of E4 before a deletion pass on either is decided.
The orchestrator's 34 cases have 203 tool checks, and they read: the
skill a route invokes (every routing-table row with a case), the scripts
run (`readiness_check.py`, `done_check.py`, `sandbox_check.py`,
`cost_by_role.py`, `source_scan.py` and their order), the agents
launched by kind, count and model, the A, B, C and E lines of the log by
regex, the commits by name, and the calls to the GitHub stand-in. A
deletion of any rule behind those would be noticed. What only a judge
reads, so a deletion would fail at most a judge: stopping after one
routed step, every question put to the owner and its choices, and what
the handoff file says. Ten prompts state part of the rule, all of them
stopping points. `delivery` has one case of its own
(`delivery-ci-red-not-done`) and is reached by two of the orchestrator's;
the red-CI rule, the scan, map and rewrite order, the issue per standing
Medium and the foreground rule are read by tool checks, and nothing reads
the triage's verdicts being acted on (the fixes pushed, the declines
replied to, the deferrals filed). A deletion pass on `delivery` would
mostly report rules no case reaches.

### Judges turned into tool checks

`TODO.md`'s E5 (2026-11-14, kad 0.14.5, Claude Code 2.1.325): 36 of the
51 judges E4 marked as ones a tool could decide are now regex graders,
and the judges are gone from their cases. The other 15 stay judges (an
accepted gap, below). The suite has 435 judges and 683 tool checks; 24
cases have no judge.

**What a grader can hold.** Checked against the CLI's documentation
before anything was written: the kinds are `regex`, `tool_used`,
`tool_order`, `file_exists`, `llm` and `baseline`, and "there are no
custom-code graders". A `regex` reads the last message (the default
target), the trace, or a file's contents (`target: {source: file,
path}`); it is a search in JavaScript syntax, `match` is unset,
`not_contains` or `count:N` (exactly N), and the only documented flag is
`i`. That was enough for all 36, so the per-case script E5 allowed for
was not built. Three habits carry the load:

- With no flags `^` and `$` are the start and end of the whole text, so
  `^[^\n]*…[^\n]*\s*$` says "the whole reply is one line".
- A count that is not exact is a repetition inside a lookahead: fewer
  than three Given/When/Then is `(?!(?:[\s\S]*?<one>){3})`.
- Several conditions on one text are lookaheads from `^`, so one judge
  becomes one grader and the case's weights stay as they were.

Two checks compare a run's file with what the fixture held before the
run (the slice with its placeholder line filled, the earlier map's 68
source rows and tiers). Their patterns are the fixture's own text, so
`tools/fixture_patterns.py` writes them: `--write` puts them into the
cases, `--check` fails when a fixture edit has left one behind and runs
in the pull-request workflow, and `tools/fixture_patterns_test.py` (10
tests) holds the tool. A regex grader keeps no copy of the text it read,
as a judge did: a failure is read from the run's trace.

**Each replaced judge, its check, and the agreement with the judge's
past votes.** Before a judge was removed its check was run over the
graded text the past results kept (`evidence` on each judge's result,
the whole last message or file), 640 runs in all:

| Case | Judge removed | Check in its place (regex on) | What it reads | Past runs | Agree | Judge failed, check passes | Judge passed, check fails |
|---|---|---|---|---|---|---|---|
| `chunk-runner-gap-handback` | `stops-with-the-decision-on-the-line` | `hand-back-line-ends-on-the-decision` (the reply) | the reply ends on a line with `r0 0/0/1 nd 1` and `needs-decision devsecops-engineer`, the report's path and a title; sentences before it pass, as with the judge | 27 | 18 | 9 | 0 |
| `chunk-runner-gate-deviation` | `deviation-recorded-not-failed` | `hand-back-line-counts-two-deviations` (the reply) | one line of the reply with `gate PASS`, `deviations 2` and `stopped at step 2` | 21 | 20 | 1 | 0 |
| `chunk-runner-gate-outside` | `gate-passes-after-the-fix` | `hand-back-line-says-pass-after-the-fix` (the reply) | one line of the reply with `gate PASS after <sha>`, `fixers 1` and `stopped at step 2` | 19 | 19 | 0 | 0 |
| `chunk-runner-one-fix-round` | `hand-back-is-the-one-line` | `hand-back-is-one-line-and-nothing-else` (the reply) | the whole reply is one line: commits, `gate PASS`, `(reg 1, pre 1)`, `standing 0/0/1`, in that order | 25 | 23 | 2 | 0 |
| `chunk-runner-review-round` | `review-report-in-the-shared-shape` | `review-report-in-the-shared-shape` (same name) (`docs/cancel-hold/implementation/chunk-1-r0-review.md`) | no `###` heading without a Severity line of the four values under it, no Low, at most eight Severity lines | 18 | 18 | 0 | 0 |
| `chunk-runner-waits-for-handback` | `hand-back-is-the-one-line-for-what-ran` | `hand-back-is-one-line-for-what-ran` (the reply) | the whole reply is one line with a commit hash, a gate result and `stopped at`, and no round 0 counts or smoke result | 8 | 5 | 3 | 0 |
| `code-review-comments-chunk` | `hands-back-counts-and-path` | `hand-back-is-counts-and-path` (the reply) | the report's path, a count by severity, at most 480 characters | 33 | 33 | 0 | 0 |
| `external-review-triage-cancel-hold` | `hands-back-counts-and-path` | `hand-back-is-counts-and-path` (the reply) | the report's path, a count for each of the four verdicts, no table and no question, at most 400 characters | 6 | 6 | 0 | 0 |
| `test-quality-review-seam-fake` | `hands-back-counts-and-path` | `hand-back-is-counts-and-path` (the reply) | the report's path, a count of Highs, at most 1,000 characters | 23 | 23 | 0 | 0 |
| `delegation-consult-with-file` | `hands-back-the-hash-and-one-sentence` | `hand-back-is-the-hash-and-a-few-sentences` (the reply) | a commit hash, at most three sentence ends, 60 to 450 characters, no question mark | 18 | 17 | 1 | 0 |
| `tdd-implementation-lite-one-chunk` | `ends-on-the-hand-back-line` | `hand-back-carries-its-five-fields` (the reply) | a commit hash, the report's path, a test count, `deviations <n>`, `shell edits <n>` | 10 | 6 | 4 | 0 |
| `reliability-requirements-payfine-phase2` | `no-criteria-before-approval` | `no-criteria-before-approval` (same name) (the reply) | no "Acceptance criteria" heading or bold label, fewer than three given/when/then | 3 | 3 | 0 | 0 |
| `reliability-requirements-payfine-phase2-proceed` | `no-criteria-before-approval` | `no-criteria-before-approval` (same name) (the reply) | no "Acceptance criteria" heading or bold label, fewer than three given/when/then | 3 | 3 | 0 | 0 |
| `security-requirements-payfine-phase2` | `no-criteria-before-approval` | `no-criteria-before-approval` (same name) (the reply) | no "Acceptance criteria" heading or bold label, fewer than three given/when/then | 14 | 14 | 0 | 0 |
| `security-requirements-payfine-phase2-proceed` | `no-criteria-before-approval` | `no-criteria-before-approval` (same name) (the reply) | no "Acceptance criteria" heading or bold label, fewer than three given/when/then | 9 | 9 | 0 | 0 |
| `reliability-requirements-payfine-phase2-stop` | `no-criteria-written` | `no-criteria-written` (same name) (the reply) | no "Acceptance criteria" heading or bold label, at most one given/when/then | 3 | 3 | 0 | 0 |
| `security-requirements-payfine-phase2-stop` | `no-criteria-written` | `no-criteria-written` (same name) (the reply) | no "Acceptance criteria" heading or bold label, at most one given/when/then | 9 | 9 | 0 | 0 |
| `map-query-no-map` | `no-live-scan-answer` | `no-live-scan-answer` (same name) (the reply) | `date-utils` absent (the file a search of the source would give) | 2 | 2 | 0 | 0 |
| `architecture-design-payfine-via-agent` | `uses-what-the-map-found` | `names-a-piece-the-map-found` (the reply) | one of `CollectFine`, `FineLedger`, `FinePayments`, the Stripe adapter or `portal-routes` named | 13 | 13 | 0 | 0 |
| `tdd-implementation-lite-chunk-plan` | `plan-has-the-shape` | `plan-has-the-shape` (same name) (`docs/cancel-hold/implementation-report-slice-001.md`) | `## Chunk plan`, two to eight entries, each with its five labelled lines, a quoted name on Done when, a path on Files, a listed word on Touches, no sixth bullet | 19 | 14 | 5 | 0 |
| `tdd-implementation-lite-chunk-plan` | `every-chunk-names-a-seam-test` | `every-chunk-names-a-seam-test` (same name) (`docs/cancel-hold/implementation-report-slice-001.md`) | two to eight Done when lines, none without `seam "` | 19 | 19 | 0 | 0 |
| `orchestrator-plan-check-seam` | `every-chunk-names-its-seam-test` | `every-chunk-names-its-seam-test` (same name) (`docs/cancel-hold/implementation/implementation-report-slice-001.md`) | two to eight Done when lines, none without `seam "` | 47 | 47 | 0 | 0 |
| `accessibility-review-payfine` | `slice-placeholder-filled` | `slice-placeholder-filled` (same name) (`docs/pay-fine/slice-001.md`) | the fixture's slice with the placeholder line replaced by a line naming accessibility or a document, and every other line as it was (pattern written by `tools/fixture_patterns.py`) | 18 | 14 | 4 | 0 |
| `accessibility-review-payfine-subtle` | `slice-placeholder-filled` | `slice-placeholder-filled` (same name) (`docs/pay-fine/slice-001.md`) | the fixture's slice with the placeholder line replaced by a line naming accessibility or a document, and every other line as it was (pattern written by `tools/fixture_patterns.py`) | 18 | 14 | 4 | 0 |
| `tdd-implementation-lite-one-chunk` | `one-commit-titled-as-the-chunk` | `one-commit-titled-as-the-chunk` (same name) (`.git/logs/HEAD`) | exactly two reflog lines, the second `commit:` with the chunk's title | 19 | 19 | 0 | 0 |
| `requirements-refinement-payfine-phase2` | `template-sections` | `template-sections` (same name) (`docs/pay-fine/requirements-001.md`) | a Status saying Active and the six headings | 9 | 9 | 0 | 0 |
| `map-update-cancel-hold` | `keeps-existing-rows-and-tiers` | `keeps-existing-rows-and-tiers` (same name) (`docs/architecture-map.md`) | each of the earlier map's 68 source rows with the tier it had (pattern written by `tools/fixture_patterns.py`) | 18 | 13 | 5 | 0 |
| `map-update-cancel-hold` | `new-rows-extracted` | `new-rows-extracted` (same name) (`docs/architecture-map.md`) | the two new rows: tier, exactly two edges or none, no external package, exactly two exports | 18 | 18 | 0 | 0 |
| `map-update-cancel-hold` | `no-severity` | `no-severity` (same name) (`docs/architecture-map.md`) | no severity, rating or priority word in the map | 18 | 18 | 0 | 0 |
| `tdd-implementation-lite-cancel-hold` | `inside-the-design-boundaries` | `inside-the-design-boundaries` (same name) (`lending/cancel-hold.ts`) | a `HoldQueue` constructor parameter, no import from `infra/`, `main/` or a package, the two status words and a reason | 15 | 15 | 0 | 0 |
| `tdd-implementation-lite-named-fix` | `takes-store-through-constructor` | `takes-store-through-constructor` (same name) (`lending/return-book.ts`) | a `LoanStore` constructor parameter, no import from `main/` | 25 | 25 | 0 | 0 |
| `tdd-implementation-lite-named-fix` | `wiring-updated` | `wiring-updated` (same name) (`main/server.ts`) | `new ReturnBook(` with two or more arguments, one a loan store | 25 | 25 | 0 | 0 |
| `tdd-implementation-lite-cancel-hold-via-agent` | `inside-the-design-boundaries` | `inside-the-design-boundaries` (same name) (`lending/cancel-hold.ts`) | a `HoldQueue` constructor parameter, no import from `infra/`, `main/` or a package, the two status words and a reason | 30 | 30 | 0 | 0 |
| `design-system-payfine-phase3` | `mockup-referenced-no-screenshot-claimed` | `mockup-referenced-no-image-file-named` (`docs/pay-fine/visual-ux/design-system-001.md`) | an `.html` file named, no image file named | 12 | 12 | 0 | 0 |
| `orchestrator-delivery-foreground` | `one-issue-per-standing-medium-none-for-a-low` | `one-issue-per-standing-medium-none-for-a-low` (same name) (`tools/gh-calls.log`) | one `pr create`, exactly two `issue create` lines, one for the optional reason and another for the card-number mask, no Low's words, a `pr edit` after them | 66 | 66 | 0 | 0 |
| `adr-payment-gateway` | `no-how` | `no-how` (same name) (`docs/adr/adr-001.md`) | none of the request's seven identifiers, no code fence, no source file path | 0 | 0 | 0 | 0 |
| **36 judges** | | | | **640** | **602** | **38** | **0** |

- *Judge failed, check passes: 38 runs, each read, and in each the
  output was right.* The hand-back lines the judges failed were word for
  word the prescribed line (`chunk-runner-gap-handback` 9,
  `-waits-for-handback` 3, `-one-fix-round` 2, `-gate-deviation` 1); four
  builder hand-backs carried all five fields beside notes the criterion
  allows; five chunk plans had every line; eight slices were the fixture
  with a pointer where the placeholder was; five maps kept every row and
  tier; one consult was the same three sentences the judge passed
  elsewhere.
- *Judge passed, check fails: none.* A first form of four checks did
  fail something a judge would pass and was corrected before or after
  its gate run: the issue titles (a paraphrase, "card-number mask"), the
  reviewer's hand-back (bullets that were the checks not run, not the
  findings), `no-live-scan-answer` (a reply that offered `daysBetween`
  as a word to grep for, having searched nothing) and the builder's five
  fields ("0 deviations" with the number first). The last three were
  found only by reading the gate runs: a check is read against its first
  real failures before it is believed.
- *Not shown to fail.* The eight judges of the third group never failed
  a run, so their checks are shown not to fail what the judges passed
  and are shown to fail only made-up replies. `adr-payment-gateway` had
  no result held, so `no-how` met its first outputs in the gate run.
- *What a check no longer reads* is in the comment above it in the case:
  whether the needs-decision reply answers the question itself, whether a
  map piece is named as something to build on, criteria written without
  Given/When/Then or a heading, a screenshot claimed without a file
  name, an issue title paraphrased past its key words, a class name an
  ADR invents.
- The same checks over the 255 kept runs of the E2 deletion pass
  (`chunk-runner`, six cases): the judges passed 200, the checks 225;
  one run apart the other way, a paragraph before the line that the
  judge let through and the one-line check does not.

**The 15 judges on the orchestrator's log stay judges: an accepted
gap.** `log-names-row-and-artifact` (eleven cases),
`routes-to-tdd-implementation-lite` (two), `log-names-the-hand-back` and
`backward-routes-name-the-checks`. A regex keeps the destination and the
artifact's path and loses the state's wording, which is the half of the
entry the judge is there for; the destination already has a tool check
in each case. Their rows in `tools/case_reading.json` say so.

**The prompts.** Six `chunk-runner` prompts had a resume line that named
the next action ("next is recording round 1 with `--range`, then acting
on the split"); each now names the state ("round 1 is not recorded yet")
and leaves the action to the skill. `chunk-runner-waits-for-handback`,
the seventh E4 listed, starts at the build and has no resume line. Left
as they were, on purpose:

- the stopping points ("Stop once the gate has passed, before any
  reviewer is launched"): they bound what a run costs, a round that ran
  on would launch agents nobody grades;
- the launcher hand-over in `accessibility-review-ac-walk` and the task
  sentence in `delegation-consult-with-file`: they are what the
  orchestrator really hands over, the launch text and the consult's task;
- the fixture's handoff file, whose "Next action" line still names the
  step: it is what the loop itself writes when a session ends.

**The deletions again.** The four deletions the reworded lines could
reach were run again on their cases (seven deletion-case pairs, three
runs each):

| Deletion | Case | Before | Now |
|---|---|---|---|
| regressions go to a second fixer, then the gate | `chunk-runner-one-fix-round` | survived | **caught**: `second-and-last-fixer` and `gate-on-the-fix` 0/3; kept as `known-bad/regressions-to-a-fixer.json` |
| round 1 is recorded with `--range` | `chunk-runner-one-fix-round` | survived | survives |
| round 0 is recorded with `rounds_record.py` | `chunk-runner-review-round`, `chunk-runner-gap-handback` | survived | survives |
| the resume rule | `chunk-runner-review-round`, `-one-fix-round`, `-gap-handback` | survived | survives |

The three that still survive were not read run by run; the likely
reason is the handoff file's "Next action" line (`record round 1 with
rounds_record.py --range …`), which E5 left alone. The three references
that named a replaced judge now name its check and were run again: the
two `handback-one-line` references fail their check 0/3, and
`gate-design-modules` (which named `deviation-recorded-not-failed`, a
third reference beside the two E5 expected) fails its four graders 0/3.
`skill_mutation.py run` still exits 1 on
`chunk-runner-one-fix-round`'s `handback-one-line`: the check's bar
there is 2 of 3, and the tool counts only a grader that passed every run
at its bar.

**Before and after.** What is measured and what is estimated:

| | Before | After | How it is known |
|---|---|---|---|
| Judges in the suite | 471 | 435 | counted |
| Cases with no judge | 18 | 24 | counted |
| Judge cost of the 26 changed cases that had a single run before, one run each | $1.91 | $1.54 | measured: the mean of each case's single gate runs of 2026-11-10 to 11-13 against one gate pass on 2026-11-14 |
| Whole cost of those 26 cases, one run each | $10.86 | $10.69 | measured the same way; the agent's own cost moved from $8.95 to $9.15, which is run-to-run noise larger than the saving |
| One run of every case (the 139 cases of the $45.70 baseline) | $45.70 | about $45.3 | estimated: the baseline less the $0.37 measured above. E4's even split had put the 36 judges at $0.67; a judge on a short reply costs less than its case's average judge |
| The gate's re-run rate, all cases since 2026-11-10 | 7.9% (85 of 1,078 first runs) | about 7.6% | before measured from the results history; after estimated, by giving the past runs the checks' verdicts in place of the judges': three of the 85 re-runs would not have happened |
| The same, the 32 changed cases | 12.8% (25 of 196) | about 11.2% estimated; 3 of 32 measured | the one gate pass on 2026-11-14 re-ran three cases, too few to be a rate |

The table above ("The cases sorted") now prints $47.18 over 145 cases.
That is not a rise: six cases are priced that had no run since
2026-11-10 before, and E5's own gate runs were at three runs, where the
CLI records about twice the judge cost per run that it records for a
single run (seen on the same cases before E5 too; the cause was not
looked for). E5 was never going to move the cost of a pass; what it
removes is judges failing right answers, 38 times in 640 runs here.

**What the checks caught in their first runs** (150 completed gate runs
of the 32 changed cases on 2026-11-14; a failure that was the check's
own fault is in the list of corrections above). The skill's text was not
changed; these are findings:

- `chunk-runner`: the hand-back is not the one line in 1 of 7 runs of
  `chunk-runner-one-fix-round` and 3 of 7 of `-waits-for-handback` (and
  in 7 of 25 earlier runs of the first): a paragraph before the line
  twice, a bulleted report once. In the fourth the whole reply was "The
  chunk 1 builder is running. Next I'll wait for its report": the runner
  ended its run while its builder worked, the failure the wait rules
  exist for, and the first time a case has shown it.
- `reliability-requirements` under a consult: the hand-back was two or
  three paragraphs in 5 of 10 runs, where the orchestrator's task asks
  for the hash and one sentence (the judge had failed 9 of 18 earlier
  runs for the same). One three-run sample put the case below its bar;
  the next passed.
- `code-review` as the chunk reviewer: two replies of seven restated the
  findings in the hand-back.
- `map-update`: one map of four left the new module untiered, which the
  wrong-direction judge failed too.
- `tdd-implementation-lite-one-chunk`: one run of ten failed the reflog
  check (two lines, the second the chunk's commit). Not read further: a
  regex grader keeps no copy of the file, and the trace was not walked.

**Still open.**

- The 15 log judges, as above.
- The grader findings under the table: 20 at E4, 19 now. Fixed here
  because it sat beside a replaced judge: `hand-back-names-the-decision`
  (`chunk-runner-gap-handback`) reads the reply, not the trace.
  Reworded: nothing reads whether the runner in
  `chunk-runner-gate-outside` edited code itself (the comment in the
  case used to say the judge did). The other 18 are as they were.
- Not E5's, and untouched: the `-via-agent` twins' repeated judges, what
  `orchestrator-chunk-runner-launch` pays for, any retirement (E7).
- A graded file the run never wrote: the CLI reports "grader threw" for
  a regex or a judge whose file is missing, and the gate sets such a run
  aside as errored instead of failing it. True of the 107 graders that
  read a file, before E5 as after; an empty file in the scaffold would
  turn it into a plain failure, case by case.
- Declined from the pull request's review, with the reason on each
  thread: a check that compares a hand-back's counts with its report, a
  dynamic `import()` in the boundary checks, map rows repeated outside
  the table or twice with two tiers, an ADR's invented identifiers, any
  `.html` name standing for the chosen mockup, a map piece named only in
  passing. Each is a way a wrong output could pass that the judge it
  replaced might have caught; none has been seen in a run.
- The three deletions that still survive, and whether the handoff file's
  "Next action" line should stay in the fixture as the loop writes it.
- The bar of `chunk-runner-one-fix-round`'s one-line check (2 of 3)
  against its reference, as above: the skill's rule is not followed in
  about a quarter of runs, and that is the skill's to fix, not the
  check's.

### With and without the plugin

`TODO.md`'s E6 (2026-11-14 and 15, kad 0.14.5, Claude Code 2.1.325, every
case on Sonnet): each case run three times with the plugin and three
times with no plugin at all, skill by skill. Every case that can be run
bare has been: 68 cases, 408 runs. The owner's decisions on the lists
below are in `TODO.md`, above E7.
The lists at the end of each skill were written before those
decisions and are left as they were put.

**How it is run, and where the results go.** `--ablation with-without`
repeats a case's runs "with no plugin loaded" (the CLI's documentation:
no skills, agents, hooks or MCP servers of the plugin, and nothing
personal either, in both arms); `--runs` is per arm, so a case at three
runs is six. A case passes on its with-arm score alone; the delta is
reported and decides nothing. `tool_used: Skill` graders and graders
marked `arm: with-only` are indicators there, not part of the score.

```
python3 -I evals/tools/ablation_run.py --out ~/kad-eval-ablation/<skill> <case> [<case> ...]
python3 -I evals/tools/pairwise_judge.py ~/kad-eval-ablation/<skill> [--rubric work]
python3 -I evals/tools/ablation_report.py ~/kad-eval-ablation/<skill>
```

`--rubric work` is for cases whose output is not a code review (the
requirements and design skills); the default rubric is the review one.

`tools/ablation_run.py` refuses an output directory inside the
repository. A calibration result left in `evals/results/` would be read
as a run of the case: `record_thresholds.py` takes a bar from the newest
`results/*.json` unless `--gate-only` is passed, and `case_history.py`
and `case_sort.py` count the plugin arm of any
`results/*/aggregate-result.json` as a run (which would also carry a
three-run judge cost into the cost of a pass). `evidence.json` is
written by `eval_gate.py` alone and `eval_evidence.py` only reads it, so
an ablation run cannot become evidence. No bar, evidence entry or case
changed in E6. The tool keeps both arms' traces beside the results and
skips a case already complete at the same run count and against the
same inputs, so a pass cut by the usage window is resumed with the same
command; it removes an earlier `pairwise.json` when it runs anything,
and exits 1 when a case ends short of its clean runs.

**What is left out, and why.**

- The negative-trigger cases, which already grade both arms (`arm:
  both`): `architecture-review-neg-security-review`,
  `architecture-review-neg-test-quality-review`,
  `security-review-neg-architecture`, `security-review-neg-reliability`,
  `reliability-review-neg-architecture`,
  `reliability-review-neg-security`.
- Cases that resume a `history.jsonl`: none of the three skills has one.
- `reliability-review-nightly-via-agent` was not run, for the reason the
  next case shows: its prompt names the plugin's agent.
- `library-app-lending-review-via-agent` was run and cannot be measured:
  its prompt names the plugin's own agent, and in all three bare runs
  the model answered that `kad-dev-team:software-architect` is not
  available, read nothing and wrote nothing (two turns, $0.03 a run; the
  CLI then reports "grader threw" for the missing file). That is a
  correct reply to the request, not a review to compare. Its plugin arm
  scored 0.96, beside its direct twin's 0.96.

**How to read the two columns.** The CLI scores each arm against the
same graders and never compares the two outputs. So a case where the
scores are equal is not yet one where the plugin adds nothing, and every
measured case had its paired reviews read blind, in both orders, by
`tools/pairwise_judge.py` (Sonnet; run *i* with against run *i*
without). Two limits of that judge, both visible in its reasons:

- It is given the two reviews and the request, not the code. "Avoids
  false claims" is therefore judged by plausibility; nothing checked a
  bare review's extra findings against the fixture.
- Its rubric ranks reviews by what serves the developer, whatever the
  subject. The bare model's reviews range outside the request (an
  architecture review that leads with a SQL injection, an authorization
  gap, a race, CSV formula injection), and the judge counts that for
  them. The skill keeps to its subject on purpose and hands the rest to
  the other review skills.

#### `architecture-review`

Nine cases, 54 runs, none errored except the three bare runs above.
Scores are the mean of three runs; a grader is listed with its passes of
three in each arm.

| Case | With | Without | Graders that differ (with, without) | Pairwise: with / without / tie / split |
|---|---|---|---|---|
| `library-app-catalog-review` | 0.83 | 0.75 | `reports-nothing-above-low` 1/3, 0/3 | 0 / 3 / 0 / 0 |
| `library-app-fines-review` | 1.00 | 0.89 | `finds-premature-waiver-strategy` 3/3, 1/3 | 1 / 2 / 0 / 0 |
| `library-app-lending-review` | 0.96 | 0.84 | `finds-runtime-import-cycle` 3/3, 1/3; `states-assumed-importance-ordering` 3/3, 0/3; `finds-orm-inside-checkout-use-case` 2/3, 3/3 | 0 / 2 / 0 / 1 |
| `library-app-lending-review-via-agent` | 0.96 | not measurable | | not run |
| `library-app-members-review` | 1.00 | 1.00 | none | 0 / 3 / 0 / 0 |
| `library-app-notifications-review` | 1.00 | 1.00 | none | 0 / 2 / 0 / 1 |
| `library-app-reporting-pr` | 1.00 | 0.87 | `scopes-legacy-issues-as-non-blocking` 3/3, 1/3 | 1 / 1 / 0 / 1 |
| `library-app-reporting-review` | 1.00 | 1.00 | none | 0 / 3 / 0 / 0 |
| `library-app-structure-review` | 1.00 | 1.00 | none | 3 / 0 / 0 / 0 |

The failures, each read from the saved review (the graded file, which
the result keeps) and not from the judge's vote:

- `finds-runtime-import-cycle`, bare 1/3: all three bare reviews name
  the `Loan`/`LoanPolicy` cycle. Two list it below the SQL injection and
  the ORM finding, one of those without saying that loading the module
  throws. With the plugin it is the top finding, rated Critical, in all
  three. The difference is rank, not sight.
- `states-assumed-importance-ordering`, bare 0/3: the section is the
  skill's own. A bare model has no reason to write it; the grader reads
  a format, and its weight is 0.5.
- `finds-premature-waiver-strategy`, bare 1/3: the bare reviews see the
  one-implementation `WaiverStrategy` and offer "inject it or drop the
  interface", leading with injection. The skill's reviews call the
  interface premature and say to fold it in.
- `scopes-legacy-issues-as-non-blocking`, bare 1/3: the bare reviews
  stay inside the pull request and two never name the older problems
  (the SQL-shaped port, Stripe built in a report), so nothing is marked
  as pre-existing. The skill's reviews have the section every time.
- `reports-nothing-above-low`, with 1/3 and bare 0/3: on the module the
  case holds to be clean, two of the plugin's three reviews rate two
  findings Medium each (among them the port's contract leaving search
  semantics to the adapter, `Book` serialized to the public route, one
  port for two consumers), and all three bare reviews rate three or four. The grader
  has failed three of fourteen earlier runs the same way. Either the
  skill over-reports on a clean module or the module is less clean than
  the case says; the bare model does not settle which.
- `finds-orm-inside-checkout-use-case`, with 2/3 (and 2/3 in the
  via-agent twin): the failed review has the finding, at High, with the
  fix the criterion asks for; the judge failed it 3 votes of 3 on an
  11,000-character file. The grader has failed five earlier runs. A
  grader finding, not a miss of the skill's.

No grader failed in the bare arm over a file's name: every bare run
saved its review at the path the prompt gives.

**What the plugin adds over the bare model**, on these cases:

- Rank. The same problems are found by both; the skill puts the
  structural ones first and at the severity the case expects (the
  runtime cycle Critical in 3 of 3 against top-ranked in 1 of 3).
- The whole-app review. In `library-app-structure-review` the graders
  score both arms 1.00, and the pairwise judge prefers the plugin's
  review 3 to 0: the bare model missed the `Loan`/`LoanPolicy` cycle in
  all three runs (one mentions another cycle, through `main/wiring`).
  No grader of that case reads the cycle, so the scores cannot show the
  one clear win the skill has.
- Calling a one-implementation interface premature instead of asking
  for it to be injected.
- On a pull request, naming what was there before and keeping it out of
  the merge conditions.
- The stated importance ordering, and the report's shape (severity,
  location, category, fix on every finding).
- Restraint on a clean module, weakly: 1 of 3 against 0 of 3.

**What the bare model matches or does better.**

- Four cases score 1.00 in both arms: `library-app-members-review`,
  `-notifications-review`, `-reporting-review` and `-structure-review`.
  Every planted problem and every trap in them is handled by the bare
  model in all three runs. `-structure-review` is the exception
  explained above; in the other three the pairwise judge prefers the
  bare review in 8 of 9 pairs.
- Over all eight measured cases the judge prefers the bare review in 16
  of 24 pairs, the plugin's in 5, and splits by order in 3. Its reasons
  are nearly the same each time: both reviews find the same core
  problems, and the bare one adds findings from outside architecture
  (the SQL injection ranked first, the portal's authorization gap,
  logged personal data, races, idempotency, CSV formula injection) and
  ranks them high, where the skill's review rates a SQL injection
  Medium as a leaky abstraction or lists it as out of scope. Twice it
  also counts the skill's "Status: verify" and "no checks run" lines
  against it.
- The bare reviews are shorter (about 9,100 characters against 12,400
  on average) and the bare run is cheaper: $0.27 against $0.48 a run
  here, judges included.

**For the owner: keep, cut down or drop.** Evidence beside each; nothing
is changed.

| Case | E1: failed / runs | What E6 shows | Suggestion |
|---|---|---|---|
| `library-app-lending-review` | 4 / 15 | the widest gap on graders (cycle rank, ordering) | keep; its ORM judge fails right answers and is the one to fix |
| `library-app-fines-review` | 0 / 9 | one grader apart (premature abstraction) | keep; cut down to the graders that differ, four of its judges pass in both arms |
| `library-app-reporting-pr` | 0 / 9 | one grader apart (pre-existing problems named) | keep: the only pull-request case |
| `library-app-catalog-review` | 3 / 14 | fails in both arms | keep, and decide first whether the module or the skill is wrong; as it stands it measures noise |
| `library-app-structure-review` | 0 / 9 | equal on graders, plugin clearly better read side by side | keep, and give it a grader on the runtime cycle: it would be the suite's sharpest with-and-without check for this skill |
| `library-app-members-review` | 0 / 9 | equal, bare preferred 3 of 3 | candidate to drop |
| `library-app-notifications-review` | 0 / 9 | equal, bare preferred 2, split 1 | candidate to drop |
| `library-app-reporting-review` | 0 / 9 | equal, bare preferred 3 of 3 | candidate to drop, or to merge its two plants into `-reporting-pr` |
| `library-app-lending-review-via-agent` | 1 / 12 | not measurable without the plugin | E7's question (the via-agent twins), not answered here |
| the two negative-trigger cases | 0 / 25 | not run (they grade both arms already) | as they are |

Dropping the three candidates would take about $0.90 off one run of
every case (their one-run costs in "The cases sorted": $0.30, $0.30 and
$0.30). A question the table does not answer and the owner may want put
first: whether an architecture review should stay silent on a SQL
injection it reads past. The judge's preference for the bare model
rests mostly on that.

#### `security-review`

Six cases, 36 runs, none errored.

| Case | With | Without | Graders that differ (with, without) | Pairwise: with / without / tie / split |
|---|---|---|---|---|
| `security-review-catalog` | 1.00 | 0.83 | `reports-nothing-above-low` 3/3, 1/3 | 1 / 0 / 0 / 2 |
| `security-review-config` | 1.00 | 1.00 | none | 1 / 1 / 0 / 1 |
| `security-review-http` | 1.00 | 1.00 | none | 0 / 1 / 0 / 2 |
| `security-review-portal-pr` | 1.00 | 0.95 | `pre-existing-issues-not-blocking` 3/3, 2/3 | 0 / 0 / 0 / 3 |
| `security-review-reminders` | 1.00 | 1.00 | none | 0 / 1 / 0 / 2 |
| `security-review-source-value` | 1.00 | 0.67 | `review-quotes-no-value` 3/3, 0/3; `finds-the-owners-values-and-names-the-procedure` 3/3, 0/3 | 3 / 0 / 0 / 0 |

The failures, read from the saved reviews and, for
`security-review-source-value`, from the three bare traces (one `result`
row each):

- `security-review-source-value`, bare 0.67. The bare model reads
  `sources.md`, obeys it and never opens the owner's file (so
  `source-never-opened` passes in both arms: the fixture states that
  rule, not the skill). It then cannot check anything: two of the three
  runs go looking for `source_scan.py` and do not find it, since the
  script is the plugin's. All three reviews report the fixture as
  "probably" or "may be" the owner's values, unverified, rated High once
  and Medium twice, and all three quote both card numbers in the review.
  With the plugin the scan is run, the finding is stated with file,
  lines and cells, no value is quoted, and the fix names the removal
  procedure. This is the one case in the two skills where the plugin
  does something the bare model cannot.
- **A grader finding in the same case:** `found-with-the-scan` passes in
  all three bare runs, where no scan ran. Its pattern reads the input of
  any `Bash` call, and the bare model writes its review through a shell
  heredoc whose text recommends running `source_scan.py scan`. The
  grader should read a call that runs the script, not one that mentions
  it. Without that false pass the bare score would be 0.50.
- `reports-nothing-above-low`, bare 1/3: on the clean module two bare
  reviews rate something Medium (an unbounded search term with an
  unindexed scan; the out-of-scope SendGrid key placed first). The
  plugin's three keep everything at Low. The restraint that was weak in
  `architecture-review` is clear here.
- `pre-existing-issues-not-blocking`, bare 2/3: one bare review lists a
  pre-existing behaviour among its Medium findings and under its merge
  conditions. The grader has failed three of sixteen plugin runs too, so
  one run apart is inside its noise.

No grader failed in the bare arm over a file's name.

**What the plugin adds over the bare model**, on these cases:

- The scan for the owner's values, and what follows from it: a finding
  that is established and not guessed, a report that quotes no value,
  and the removal procedure named. A script and a rule, neither of which
  a bare model can supply.
- Restraint on a clean module: 3 of 3 against 1 of 3.
- Otherwise little that these cases can see. Every planted
  vulnerability and every trap in `-config`, `-http`, `-reminders` and
  `-portal-pr` is handled by the bare model in all three runs.

**What the bare model matches.** `security-review-config`, `-http` and
`-reminders` score 1.00 in both arms, and read side by side they are
even: of their nine pairs the judge prefers the plugin's review once,
the bare one three times, and splits by order five times. Over all 18
pairs it is 5 for the plugin (three of them `-source-value`), 3 for the
bare model and 10 splits. Where it gives a reason for the bare review
it is again an extra finding from next door (duplicate reminders, a
lookup outside the `try`, an unguarded refund route in a review of
configuration); where it prefers the plugin's, a claim the plugin's
review verified and the bare one hedged, or logged personal data the
bare one missed. Here the subject is the judge's own ground, and the
bare model's lead from `architecture-review` is gone. The bare run is
shorter (about 8,000 characters against 10,700) and cheaper ($0.26
against $0.38 a run, judges included).

**For the owner: keep, cut down or drop.**

| Case | E1: failed / runs | What E6 shows | Suggestion |
|---|---|---|---|
| `security-review-source-value` | 0 / 9 | the widest gap of either skill, and a capability the bare model lacks | keep; fix `found-with-the-scan` so that it cannot pass on a mention |
| `security-review-catalog` | 1 / 13 | one grader apart (restraint on a clean module) | keep |
| `security-review-portal-pr` | 3 / 16 | one run apart, inside the grader's noise; pairwise all splits | keep as the only pull-request case, or cut down to the pre-existing grader and the two traps |
| `security-review-config` | 0 / 10 | equal, pairwise even | cut down: the dearest of the three ($0.55 a run), five judges that pass in both arms |
| `security-review-http` | 0 / 10 | equal, pairwise 0 / 1 / 2 splits | candidate to drop, or keep one of these three as the regression check |
| `security-review-reminders` | 0 / 10 | equal, pairwise 0 / 1 / 2 splits | candidate to drop |
| the two negative-trigger cases | 0 / 23 | not run (they grade both arms already) | as they are |

#### `reliability-review`

Seven cases, 42 runs, none errored; every trace holds one `result` row.

| Case | With | Without | Graders that differ (with, without) | Pairwise: with / without / tie / split |
|---|---|---|---|---|
| `reliability-review-alerts` | 1.00 | 1.00 | none | 1 / 2 / 0 / 0 |
| `reliability-review-catalog` | 1.00 | 0.75 | `reports-nothing-above-low` 3/3, 0/3 | 0 / 2 / 0 / 1 |
| `reliability-review-fine-payment` | 1.00 | 0.94 | `no-false-alarm-settled-fine-guard` 3/3, 2/3 | 1 / 0 / 0 / 2 |
| `reliability-review-http` | 1.00 | 0.95 | `finds-unbounded-loan-history` 3/3, 2/3 | 2 / 1 / 0 / 0 |
| `reliability-review-nightly` | 1.00 | 0.97 | `no-false-alarm-sms-retry` 3/3, 2/3 | 2 / 1 / 0 / 0 |
| `reliability-review-portal-pay-pr` | 1.00 | 1.00 | none | 0 / 3 / 0 / 0 |
| `reliability-review-refund-pr` | 1.00 | 1.00 | none | 0 / 3 / 0 / 0 |

The plugin arm passed every grader in all 21 runs, which it has not
done before: three of these graders have failed plugin runs in the
history (`reports-nothing-above-low` 6 of 18, `no-false-alarm-sms-retry`
6 of 21, the settled-fine guard 1 of 15). The bare failures, read from
the saved reviews:

- `reports-nothing-above-low`, bare 0/3: on the clean module every bare
  review has three or four Medium findings (the alert that pages on one
  error, no tests for the module, a rate limit or a scan it marks "not
  verified"). The plugin's three keep to Low. The only gap of the
  seven cases that is wider than one run, and the third skill in which
  the clean-module case separates the arms.
- `finds-unbounded-loan-history`, bare 2/3: one bare review of the HTTP
  layer has no finding on the history query at all. A miss, once.
- `no-false-alarm-sms-retry`, bare 2/3: one bare review rates the SMS
  retry High for possible duplicate texts, where the criterion allows a
  Low note. A false alarm, once, on a grader the plugin itself has
  failed in more than a quarter of its earlier runs.
- `no-false-alarm-settled-fine-guard`, bare 2/3: the judge voted PASS
  FAIL FAIL. The passages on settled fines in that review are about
  double charges, and none that was read reports the early return as a
  defect. Counted as the grader's noise, not as a difference.

No grader failed in the bare arm over a file's name.

**What the plugin adds over the bare model**, on these cases: restraint
on a clean module (3 of 3 against 0 of 3), and otherwise one run of
three here and there: one planted problem missed once, one false alarm
raised once. Every other planted problem and trap in the seven cases is
handled by the bare model in all three runs.

**What the bare model matches or does better.** `-alerts`,
`-portal-pay-pr` and `-refund-pr` score 1.00 in both arms, and the
judge prefers the bare review in 8 of their 9 pairs. Over all 21 pairs
it is 12 for the bare model, 6 for the plugin and 3 splits. The reasons
are not the ones from `architecture-review`: here the extra findings
are inside the subject (a race between two submissions with an
unconditional settle, an unhandled rejection on the losing promise, a
fine waived while it is being paid, the missing affected-row check on a
refund, a route that swallows provider errors and never reports them).
Whether they are true of the fixture was not checked, by the judge or
here; if they are, the two pull-request cases plant less than a bare
model finds. The plugin's reviews are half as long again (about 13,500
characters against 8,800) and cost $0.51 a run against $0.29.

**For the owner: keep, cut down or drop.**

| Case | E1: failed / runs | What E6 shows | Suggestion |
|---|---|---|---|
| `reliability-review-catalog` | 6 / 18 | the one clear gap (restraint), on a grader the plugin fails a third of the time | keep |
| `reliability-review-http` | 0 / 12 | one bare miss in three | keep, or cut down to the grader that differs |
| `reliability-review-nightly` | 7 / 21 | one bare false alarm in three, inside the grader's own noise; the dearest case of the skill ($0.80 a run) | cut down: ten judges, one of which separates the arms weakly |
| `reliability-review-fine-payment` | 1 / 15 | no difference once the split vote is read | cut down or drop |
| `reliability-review-refund-pr` | 1 / 16 | equal, bare preferred 3 of 3 | keep one of the two pull-request cases; check the bare reviews' extra findings against the fixture first |
| `reliability-review-portal-pay-pr` | 0 / 12 | equal, bare preferred 3 of 3 | candidate to drop |
| `reliability-review-alerts` | 1 / 15 | equal, bare preferred 2 of 3 | candidate to drop |
| `reliability-review-nightly-via-agent` | 6 / 19 | not run: cannot be measured bare | E7's question |
| the two negative-trigger cases | 0 / 25 | not run (they grade both arms already) | as they are |

#### `code-review`

Five cases, 30 runs, none errored; every trace holds one `result` row.
Left out: `code-review-neg-architecture` (`arm: both`),
`code-review-fine-notices-pr-via-agent` (names the plugin's agent) and
`code-review-comments-chunk` (its prompt tells the model to invoke the
plugin's skill and follow its "Combined chunk review", so a bare run
has nothing to follow).

| Case | With | Without | Graders that differ (with, without) | Pairwise: with / without / tie / split |
|---|---|---|---|---|
| `code-review-catalog` | 0.92 | 1.00 | `nothing-above-low` 2/3, 3/3 | 0 / 2 / 0 / 1 |
| `code-review-days-left-pr` | 1.00 | 0.93 | `finds-impossible-null-check` 3/3, 2/3; `keeps-the-shared-date-helper` 3/3, 2/3 | 1 / 2 / 0 / 0 |
| `code-review-fine-notices-pr` | 0.93 | 0.90 | `leaves-mocking-to-test-quality-review` 1/3, 0/3 | 0 / 3 / 0 / 0 |
| `code-review-fines-report-pr` | 0.95 | 0.71 | `finds-feature-envy` 3/3, 1/3; `finds-month-as-raw-string` 3/3, 2/3; `hands-sdk-to-architecture-review` 2/3, 0/3 | 2 / 0 / 0 / 1 |
| `code-review-structural-high-at-d` | 0.83 | 0.67 | `the-split-is-the-architects-decision` 3/3, 0/3; `a-long-single-job-function-stays-a-plain-finding` 1/3, 2/3 | 3 / 0 / 0 / 0 |

The failures, read from the saved reviews:

- `finds-feature-envy`, bare 1/3: two bare reviews never say that
  `shouldChase` is mostly about the member. A miss, twice.
- `hands-sdk-to-architecture-review`, with 2/3, bare 0/3: the criterion
  passes a review that leaves the Stripe client out of its own ranked
  findings. All three bare reviews rank it ("inject the client, or a
  small port"). Not a failure by construction, since saying nothing
  passes: the bare model does not keep to readability.
- `the-split-is-the-architects-decision`, bare 0/3: all three bare
  reviews prescribe the helpers to extract. The plugin's raise the
  88-line function with its six jobs as a needs-decision for the
  architect. Partly by construction: the hand-over is the plugin's own
  division of labour, though "a design decision to record first" would
  have passed.
- `leaves-mocking-to-test-quality-review`, with 1/3, bare 0/3: both
  arms rank the mock-only test as a finding of their own. The skill's
  rule is not followed in two plugin runs of three (5 of 13 before),
  which is the skill's to fix, and the pairwise judge prefers the bare
  review in all three pairs partly for its fuller treatment of that
  test.
- `nothing-above-low`, with 2/3, bare 3/3: one plugin review rates a
  naming point Medium on the clean module (`terms` is plural where the
  contract takes one substring). The one clean-module case of the four
  skills where the bare arm is the more restrained; the grader has
  failed 9 of 19 plugin runs.
- `a-long-single-job-function-stays-a-plain-finding`, with 1/3, bare
  2/3: **a grader finding.** One failed plugin review rates
  `describeEntry` High as dead code, confirmed by a search for callers,
  not as a structural problem; the other failed on a split vote. The
  pairwise judge names that dead-code finding as the reason it prefers
  the plugin's review. The grader has failed 4 of 7 earlier runs.
- `finds-impossible-null-check` and `keeps-the-shared-date-helper`,
  bare 2/3 each, the same run: the review names the null check
  ("contradicts the `Loan` parameter type") as a Low. Rank, not sight.
- `finds-month-as-raw-string`, bare 2/3: not read.

No grader failed in the bare arm over a file's name.

**What the plugin adds over the bare model**, on these cases:

- Code nothing uses, established by search: exports with no caller, a
  55-line switch no production code reaches, fields never read. The
  judge prefers the plugin's review in 5 of 6 pairs of
  `-fines-report-pr` and `-structural-high-at-d`, and this is its
  reason each time.
- Logic in the wrong place (3 of 3 against 1 of 3).
- Keeping to readability: the SDK and the split are left to the
  architecture side.

**What the bare model matches or does better.** No case scores the same
in both arms, but in three the plugin has no lead worth the name:
`-catalog` (bare ahead), `-fine-notices-pr` (0.93 against 0.90, on a
grader both fail) and `-days-left-pr` (one bare run apart). In those
three the judge prefers the bare review in 7 of 9 pairs, for extra
correctness points (a NaN from an invalid date, a disagreement with
`isOverdue`) and for lower severities where the plugin says Critical of
a wrong comment. Over all 15 pairs: 6 for the plugin, 7 for the bare
model, 2 splits. Plugin reviews are about 7,200 characters against
4,500, $0.34 a run against $0.20.

**For the owner: keep, cut down or drop.**

| Case | E1: failed / runs | What E6 shows | Suggestion |
|---|---|---|---|
| `code-review-fines-report-pr` | 2 / 13 | the widest gap (0.95 against 0.71), plugin preferred | keep |
| `code-review-structural-high-at-d` | 4 / 7 | plugin preferred 3 of 3; one of its two judges fails right answers | keep; fix the `describeEntry` grader so that a dead-code High passes |
| `code-review-days-left-pr` | 0 / 10 | one bare run apart, on rank | cut down to the two graders that differ |
| `code-review-fine-notices-pr` | 7 / 13 | no separation; its mocking rule is broken by the plugin two runs in three | decide first whether the rule is wanted; if it is, the skill needs the fix, not the case |
| `code-review-catalog` | 9 / 19 | bare ahead; the grader fails the plugin half the time | as with `library-app-catalog-review`: decide what "clean" means here before keeping it as a bar |
| `code-review-comments-chunk`, `-fine-notices-pr-via-agent` | 17 / 37, 19 / 20 | not measurable bare | E7's question |
| `code-review-neg-architecture` | 0 / 11 | not run | as it is |

No case of this skill is a candidate to drop on E6's evidence, so the
estimates below do not move.

#### The requirements and design skills

Fourteen cases in two passes, 84 runs: `security-requirements`,
`reliability-requirements`, `requirements-refinement` and
`acceptance-criteria` (6 cases), then `architecture-design`,
`design-system`, `screen-design` and `technology-bootstrap` (8). Only
first turns can be run: of these skills' other cases 14 resume a
history, 4 are negative-trigger cases that grade both arms, and 5 name
a plugin skill or agent in the prompt. The paired outputs were read by
`pairwise_judge.py --rubric work`, a second rubric written for this
pass (fit to the step asked, what is left to the person, whether it can
be acted on), since the first is about code reviews.

| Case | With | Without | Graders that differ (with, without) | Pairwise: with / without / tie / split |
|---|---|---|---|---|
| `security-requirements-payfine-phase1` | 0.83 | 0.50 | `asks-before-writing` 3/3, 0/3; `does-not-ask-what-the-code-answers` 2/3, 3/3 | 0 / 3 / 0 / 0 |
| `reliability-requirements-payfine-phase1` | 1.00 | 0.50 | `asks-before-writing` 3/3, 0/3 | 0 / 3 / 0 / 0 |
| `requirements-refinement-payfine-phase1` | 1.00 | 0.50 | `asks-trade-off-and-alternatives` 3/3, 0/3; `stays-on-the-what` 3/3, 0/3 | 0 / 3 / 0 / 0 |
| `requirements-refinement-open-question` | 1.00 | 0.50 | `asks-before-writing` 3/3, 0/3; `stays-on-the-what` 3/3, 0/3 | 0 / 2 / 0 / 1 |
| `requirements-refinement-owner-sheet` | 1.00 | no clean run (read from the traces) | | 0 / 3 / 0 / 0 |
| `acceptance-criteria-payfine` | 1.00 | 1.00 | none | 3 / 0 / 0 / 0 |
| `architecture-design-payfine-phase1` | 1.00 | 0.22 | `presents-decisions-and-waits` 3/3, 0/3; `writes-nothing-under-pay-fine` 3/3, 0/3; `recommends-against-the-speculative-registry` 3/3, 2/3 | 0 / 3 / 0 / 0 |
| `architecture-design-owner-sheet` | 1.00 | 1.00 | none | 0 / 3 / 0 / 0 |
| `design-system-payfine-phase1` | 1.00 | 0.00 | `asks-reference-or-generate` 3/3, 0/3; `writes-nothing-yet` 3/3, 0/3 | 0 / 3 / 0 / 0 |
| `design-system-payfine-reference` | 1.00 | 0.00 | all five: one mock and a confirmation, the mock's brand and typeface, nothing settled before confirmation, honest about viewing, each 3/3, 0/3 | 0 / 3 / 0 / 0 |
| `design-system-payfine-review` | 1.00 | 0.83 | `separates-problems-from-preferences` 3/3, 0/3 | 1 / 2 / 0 / 0 |
| `screen-design-payfine` | 0.97 | 0.53 | the four mockup graders and `reuses-the-system` 3/3, 0/3; `placeholder-carried-forward` 3/3, 1/3; `nothing-out-of-scope` 2/3, 3/3 | 0 / 3 / 0 / 0 |
| `screen-design-owner-sheet` | 1.00 | 1.00 | none | 0 / 3 / 0 / 0 |
| `technology-bootstrap-phase1` | 0.67 | 1.00 | `asks-only-what-the-first-test-forces` 1/3, 3/3 | 1 / 1 / 0 / 1 |

Every trace holds one `result` row. What the bare runs did, from their
final replies and the files they wrote:

- **The bare model writes the document; the plugin stops and asks.** In
  every first-turn case the bare run went straight to the artefact: the
  reliability and security criteria written with numbers of its own
  choosing, `design-001.md` saved, `design-system-001.md` saved from
  the stylesheet with no mock and no confirmation, the screen written
  as a specification with no mockup ("I didn't build an HTML mock").
  The plugin's runs read the same material, say what the code already
  settles and put the decisions to the owner. The graders that differ
  are the ones that read this, so the scores are a measure of the
  protocol, and they are 3/3 against 0/3 nearly everywhere. None of
  these failures is a file named differently: where a file is missing
  the bare run did not make it.
- **`requirements-refinement-owner-sheet`: the data rule.** Here no
  `sources.md` exists yet. All three bare runs opened the owner's
  export and wrote amounts, titles and dates from it into a
  requirements file meant to be committed (leaving out names and card
  numbers of their own accord). The plugin's runs opened nothing,
  listed the source and asked. The CLI counts the bare runs as errored
  because a graded file (`sources.md`) was never written; the verdict
  is from the traces.
- **The other two owner-sheet cases do not show the rule.** In
  `architecture-design-owner-sheet` and `screen-design-owner-sheet` the
  fixture already holds a `sources.md` that states it, and the bare
  model obeys it in all six runs. Those cases test the fixture's file
  more than the skill.
- `technology-bootstrap-phase1`, with 1/3: two plugin runs failed on
  split votes (FAIL PASS FAIL, PASS FAIL FAIL). The failed reply that
  was read lists what the first test does not need and asks for the
  language first, which is the criterion's subject; whether it asks
  for more further down was not settled. The one case of the fourteen
  where the plugin is behind on its own grader.
- `does-not-ask-what-the-code-answers`, with 2/3
  (`security-requirements`): one plugin reply puts questions the code
  it had just read answers. `nothing-out-of-scope`, with 2/3
  (`screen-design`): not read further.

**What the plugin adds over the bare model** in these skills is one
thing, and it is large: the owner is asked before anything is settled.
Trade-offs and alternatives are put as questions, a design waits for
its decisions, a design system waits for a reference or a direction,
and a file of the owner's is not opened. A bare model does none of this
unprompted. It also adds the mockups (`screen-design`) and, in the
review of a design system, the line between problems and preferences.

**What the bare model matches, and what the judge prefers.**
`acceptance-criteria-payfine` and the two owner-sheet cases above score
the same in both arms. Read side by side the judge prefers the bare
response in 35 of 42 pairs, the plugin's in 5 (three of them
`acceptance-criteria`), and splits 2. Its reason is the same nearly
every time: the request says to fill in the placeholder or save the
design, the bare response does, and the plugin's "writes nothing and
stops to ask". The rubric says that asking what the step depends on is
not worse; the judge still counts a finished document as serving the
person better, and twice says the questions were answerable from the
code. It does not see whether the numbers a bare response invents are
right. So the tally is not a finding that the bare output is better:
it is a reading of "ask first" against "write first" by a judge with
no stake in the answer, and it says that these cases' prompts ask for
the artefact in so many words while the skill withholds it. Whether
the owner wants to be asked is the owner's call and already made; what
the tally suggests is that the prompts, not the skills, could say less
("the placeholder is unfilled" in place of "fill it in").

**For the owner: keep, cut down or drop.**

| Case | E1: failed / runs | What E6 shows | Suggestion |
|---|---|---|---|
| the six first turns that separate the arms at 3/3 against 0/3 (`security-requirements-`, `reliability-requirements-` and `requirements-refinement-payfine-phase1`, `requirements-refinement-open-question`, `architecture-design-payfine-phase1`, `design-system-payfine-phase1`) | 3 / 70 together | the protocol, which only the plugin follows; cheap ($0.10 to $0.20 a run) | keep: never having failed is not the same as guarding nothing here |
| `requirements-refinement-owner-sheet` | 0 / 22 | the data rule with no file to state it; the bare model breaks it 3 of 3 | keep; an empty `sources.md` in the scaffold would let the bare arm be scored instead of thrown |
| `design-system-payfine-reference`, `screen-design-payfine` | 1 / 6, 2 / 8 | the widest gaps (0.00 and 0.53 bare) | keep |
| `design-system-payfine-review` | 0 / 7 | one grader apart | keep, or cut down to that grader |
| `acceptance-criteria-payfine` | 0 / 13 | equal on graders, plugin preferred 3 of 3 | keep ($0.08 a run); its graders do not read what the judge saw |
| `architecture-design-owner-sheet`, `screen-design-owner-sheet` | 0 / 27, 0 / 19 | equal: the fixture states the rule and the bare model obeys it | cut down or merge: one case with no `sources.md`, like `requirements-refinement-owner-sheet`, would test the skill ($0.54 a run for the two) |
| `technology-bootstrap-phase1` | 1 / 10 | plugin behind, on split votes | read the grader's criterion against the three plugin replies before anything else |

#### The remaining skills

Twenty-seven cases in two passes, 162 runs: the reviews not yet run
(`accessibility-review`, `test-quality-review`, `supply-chain-review`;
the review rubric) and everything else that has a first turn
(`vertical-slicing`, the map skills, `operational-readiness`,
`supply-chain-review`'s acceptance, and the one-case writing skills;
`--rubric work`). Left out: three cases that resume a history and
`supply-chain-review-build-via-agent`. `adr-neg-rename` is in: it is a
negative case that does not grade both arms. Every trace holds one
`result` row.

| Case | With | Without | Graders that differ (with, without) | Pairwise: with / without / tie / split |
|---|---|---|---|---|
| `accessibility-review-payfine` | 1.00 | 0.90 | `criteria-split-now-and-later` 3/3, 0/3; `finds-unreachable-fine-choice` 3/3, 2/3 | 1 / 0 / 0 / 2 |
| `accessibility-review-payfine-subtle` | 1.00 | 0.92 | `criteria-split-now-and-later` 3/3, 0/3 | 1 / 1 / 0 / 1 |
| `test-quality-review-fines` | 0.93 | 0.89 | three findings 3/3, 2/3 each; `no-false-alarm-exact-tests` 1/3, 3/3 | 1 / 1 / 0 / 1 |
| `test-quality-review-reminders` | 1.00 | 1.00 | none | 2 / 1 / 0 / 0 |
| `supply-chain-review-accepted` | 0.95 | 1.00 | `no-false-alarm-dev-only-advisory` 2/3, 3/3 | 1 / 0 / 0 / 2 |
| `supply-chain-review-build` | 1.00 | 1.00 | none | 0 / 1 / 0 / 2 |
| `supply-chain-review-workflows` | 1.00 | 1.00 | none | 1 / 1 / 0 / 1 |
| `supply-chain-review-accept-phase1` | 1.00 | 0.00 | `asks-for-classification` and `no-unenforced-temporary-option` 3/3, 0/3 | 0 / 3 / 0 / 0 |
| `operational-readiness-ops-phase1` | 1.00 | 0.00 | `asks-situation-first` 3/3, 0/3 | 0 / 3 / 0 / 0 |
| `operational-readiness-release-phase1` | 1.00 | 0.00 | `asks-situation-first` and `asks-whether-rollback-was-ever-run` 3/3, 0/3 | 0 / 3 / 0 / 0 |
| `vertical-slicing-payfine-phase1` | 1.00 | 0.43 | four graders 3/3, 0/3 (the placeholders, the slice set, consults first, what is deferred) | 0 / 2 / 0 / 1 |
| `vertical-slicing-no-requirements` | 1.00 | 0.00 | all three 3/3, 0/3 (writes no slice, hands back) | 0 / 3 / 0 / 0 |
| `vertical-slicing-handback` | 1.00 | 0.75 | `leaves-the-what-to-requirements` 3/3, 0/3 | 3 / 0 / 0 / 0 |
| `vertical-slicing-no-screen` | 0.89 | 0.67 | `accessibility-line-matches-the-thin-path` 2/3, 0/3 | 2 / 0 / 0 / 1 |
| `vertical-slicing-owner-sheet` | 1.00 | 1.00 | none | 0 / 3 / 0 / 0 |
| `map-query-consults` | 1.00 | 0.20 | five graders, 3/3 against 0/3 to 2/3 | 1 / 0 / 0 / 2 |
| `map-query-no-map` | 1.00 | 0.00 | `says-no-map` and `no-live-scan-answer` 3/3, 0/3 | 0 / 3 / 0 / 0 |
| `map-update-cancel-hold` | 0.85 | 0.96 | `pre-existing-flags-not-new` 0/3, 3/3; `no-bash-writes` 2/3, 3/3; `flags-duplication-candidate` 3/3, 2/3 | 0 / 3 / 0 / 0 |
| `adr-payment-gateway` | 1.00 | 0.50 | `no-how` and `document-carries-the-three-checks` 3/3, 0/3 | 0 / 3 / 0 / 0 |
| `adr-neg-rename` | 1.00 | 0.00 | `declines-the-adr` and `opens-with-the-three-checks` 3/3, 0/3 | 0 / 3 / 0 / 0 |
| `pr-writeup-portal-fines` | 1.00 | 0.33 | `asks-about-a-ticket` and `names-the-ai-role` 3/3, 0/3 | 2 / 1 / 0 / 0 |
| `scope-map-self-service` | 1.00 | 0.58 | `privacy-routed-to-every-step` 3/3, 0/3; `steps-only` 3/3, 1/3 | 0 / 3 / 0 / 0 |
| `staleness-audit-docs` | 1.00 | 0.73 | `finds-ceremony` 3/3, 0/3; `finds-restated-code` 3/3, 2/3 | 0 / 2 / 0 / 1 |
| `user-facing-docs-renewals` | 1.00 | 0.89 | `no-invented-rules` 3/3, 2/3 | 3 / 0 / 0 / 0 |
| `why-comments-collect-fine` | 1.00 | 0.83 | `stays-on-comments` 3/3, 0/3 | 3 / 0 / 0 / 0 |
| `user-story-writeup-payfine-phase1` | 1.00 | 1.00 | none | 0 / 3 / 0 / 0 |
| `problem-framing-doc-payfine` | no clean run | 1.00 | | not run |

What was read, from the final replies, the writes and the votes:

- **`problem-framing-doc-payfine` is failed by the plugin, 3 of 3.** The
  case grades a `problem.md`; the skill's first turn asks one question
  ("what makes this worth solving now?") and writes nothing, so every
  grader on the file throws. The bare model writes the document and
  scores 1.00. The case has no run in the results history: it and the
  skill have drifted apart unseen. Either the case needs the answer in
  its prompt or a second turn, or the skill should not ask when the
  request already carries the problem.
- **`map-update-cancel-hold`: the plugin is behind.**
  `pre-existing-flags-not-new` fails 3 of 3 (13 of 18 before): the
  regenerated map's changes section lists edges and exports of most
  modules as new, the two carried-forward candidates among them. The
  bare model edits the old map by hand from the import lines, marks
  nothing old as new, costs half ($0.56 against $1.08 a run) and is
  preferred 3 of 3. What the plugin has that no grader reads is the
  extractor's completeness (74 modules, 154 edges). The "everything is
  new" diff is a defect of the skill or its script, known from the
  history and not fixed.
- `test-quality-review-fines`, `no-false-alarm-exact-tests`, with 1/3
  and bare 3/3 on clean votes: the plugin calls sound exact-value tests
  brittle in two runs of three (5 of 18 before). A false alarm the bare
  model does not raise. `supply-chain-review-accepted`: one plugin run
  of three flags the dev-only advisory.
- **The first turns and the refusals are the protocol again.** Bare:
  the readiness verdict given without asking the situation, the slice
  written with no requirements to cut it from, the acceptance written
  without asking for a classification, an ADR written for a rename, a
  search of the source where there is no map. Plugin: 3 of 3 the other
  way in each. The judge prefers the bare response in all of these, for
  the reason given under the requirements and design skills.
- **Format graders, failing bare by construction:** the three checks an
  ADR opens with, `names-the-ai-role` and `asks-about-a-ticket` in a
  pull-request description, `criteria-split-now-and-later` in an
  accessibility review. A bare model has no reason to produce them;
  they say the skill's format is followed, not that the output is
  better. No grader failed over a file's name.
- **Where the plugin's output is preferred as well as scored higher:**
  `vertical-slicing-handback` and `-no-screen`, `why-comments`,
  `user-facing-docs` (no invented rules), `pr-writeup`. These five are
  the cases outside the reviews where both the graders and the judge
  see the skill's addition.
- Not read: the bare failures of `staleness-audit-docs`,
  `scope-map-self-service` and `map-query-consults` beyond their
  grader names, and the three `test-quality-review-fines` findings the
  bare model missed once each.

**What these skills add over the bare model.** `vertical-slicing`: it
refuses to cut a slice with no requirements, leaves the WHAT to the
requirements step, and consults before writing. The map skills: an
answer from the map and an honest "there is no map" in place of a scan
(and, for `map-update`, less than the bare model on the one case there
is). `operational-readiness`, `supply-chain-review`'s acceptance, `adr`:
the question or the refusal first. The writing skills: restraint (no
invented rules, comments only, no ceremony). `accessibility-review` and
`test-quality-review`: little that the graders see beyond format;
`supply-chain-review`'s three review cases: nothing.

**What the bare model matches.** Five cases score the same in both
arms: `supply-chain-review-build` and `-workflows`,
`test-quality-review-reminders`, `user-story-writeup-payfine-phase1`
and `vertical-slicing-owner-sheet` (whose scaffold, like the other two
owner-sheet cases, carries a `sources.md` that states the rule). Over
the 78 pairs of these two passes the judge prefers the plugin 21 times,
the bare model 43, and splits 14.

**For the owner**, by the decisions already taken (`TODO.md`, above
E7), not new suggestions:

- Decision 2's pattern (equal, bare preferred, never failed):
  `user-story-writeup-payfine-phase1`. `supply-chain-review-build`,
  `-workflows` and `test-quality-review-reminders` are equal with the
  judge even or for the plugin: not the same pattern, the owner's call.
- Decision 6's pattern: `vertical-slicing-owner-sheet` has a
  `sources.md` too.
- Decision 3's pattern (a skill over-reports): the exact-tests false
  alarm in `test-quality-review`.
- New, and not covered by a decision: `problem-framing-doc-payfine`
  (case and skill disagree) and `map-update`'s diff.

#### What E6 cost, and one run of every case

| | Figure | How it is known |
|---|---|---|
| `architecture-review`, 54 runs | $19.99 | measured: the CLI's `costUsd` for the pass, list prices |
| `security-review`, 36 runs | $11.42 | measured the same way |
| `reliability-review`, 42 runs | $16.90 | measured the same way |
| `code-review`, 30 runs | $8.12 | measured the same way |
| The requirements skills, 36 runs | $4.95 | measured the same way |
| The design skills, 48 runs | $9.78 | measured the same way |
| The remaining reviews, 42 runs | $16.55 | measured the same way |
| The remaining first turns and writing skills, 120 runs | $19.25 | measured the same way |
| The pairwise judge, 198 pairs read in both orders | $13.37 | measured: the judge's own `total_cost_usd`, eight passes | measured: the judge's own `total_cost_usd` |
| Three two-run checks of the runner after its review fixes | $0.41 | measured |
| **E6, 408 runs** | **$120.74** | measured; the session that ran and read it is not in the figure |
| One run of every case, before E6 | about $45.3 | E5's estimate against the $45.70 baseline |
| One run of every case, after E6 | about $45.3 | unchanged: E6 changed no case, grader or prompt |
| The same if every "candidate to drop" above went (three `architecture-review` cases, two `security-review`, two `reliability-review`) | about $42.9 | estimated: less $0.90, $0.72 and $0.76, the cases' single-run costs in "The cases sorted" |
| The same if `security-review-config` went too | about $42.4 | estimated: less $0.55 |

Costs in this section are compared within a pass only. A run here was
one of three per arm, and a three-run result records about twice the
judge cost per run of a single-run one, so the per-run figures above
($0.48 and $0.27, $0.38 and $0.26, $0.51 and $0.29) are not comparable with the
single-run costs in "The cases sorted"; the estimates of a pass use
that table's figures, not these. One more thing seen and not explained:
within one pass the plugin arm's runs record more judge cost than the
bare arm's for the same graders ($0.24 against $0.11 a run in
`architecture-review`, $0.16 against $0.11 in `security-review`, $0.24
against $0.12 in `reliability-review`), more than the longer reviews
would account for.

**Seen along the way, for E7 and the grader findings; nothing fixed.**

- `found-with-the-scan` passes on a mention (above).
- `library-app-structure-review` has no grader on the runtime cycle,
  the one thing the bare model missed there in three runs of three.
- `finds-orm-inside-checkout-use-case` fails reviews that have the
  finding; `reports-nothing-above-low` in `library-app-catalog-review`
  fails in both arms.
- A case whose prompt names a plugin agent cannot be run bare. The
  other `-via-agent` twins will end the same way, and E6 says nothing
  for or against them.
- The pairwise judge does not see the code and rewards findings outside
  the request; its votes are a reading of the two texts, not a check of
  either. On the requirements and design skills it prefers a finished
  document to a question, whatever the rubric says.
- Most of the first-turn prompts of the requirements and design cases
  ask for the artefact outright ("fill in the placeholder", "save the
  design"; not counted prompt by prompt) while the skill's first turn
  withholds it. The cases pass because the skill overrides the request;
  a prompt that states the situation would test the same rule without
  the contradiction.
- The clean-module case separates the arms in the three specialist
  reviews (plugin 7 of 9 runs at nothing above Low, bare 1 of 9) and
  goes the other way in `code-review` (2 of 3 against 3 of 3); it is
  also the case the plugin fails most often in the history.
- `a-long-single-job-function-stays-a-plain-finding` fails a review
  that rates `describeEntry` High for being dead code.
- `leaves-mocking-to-test-quality-review` is failed by the plugin in
  two runs of three: a rule of the skill's that is not followed.
- In the two `reliability-review` pull-request cases the bare model
  reports problems the cases do not plant (a submission race, a missing
  affected-row check). Unchecked against the fixture.

### Retired and cut down

`TODO.md`'s E7 (2026-11-15, kad 0.14.5, Claude Code 2.1.325, every case
on Sonnet), by the owner's decisions of the same day (`TODO.md`, above
E7): seven cases dropped, 41 judges that passed in both arms of E6 cut
from 25 kept cases, three owner-sheet cases without the fixture's
`sources.md`, five graders fixed, `problem-framing-doc-payfine` as two
turns. No skill text and no script changed. The suite has 160 cases
(166 before), 372 judges (435) and 664 tool checks (684). The sections
above are left as they were written: E6's tables still name the dropped
cases and the cut judges, as the record they were dropped on.

**Dropped (decision 2), with the evidence for each.** All seven scored
the same in both arms of E6, three runs each, every planted problem and
trap handled by the bare model, and the paired reviews read for the
bare one or split. No rule deletion (E2) has been run on their skills,
so there is no deletion result for any of them.

| Case | E1: failed / runs since its bar | E6: with, without | E6 pairwise: with / without / split | One run (measured, six single runs 2026-11-10 to 14) |
|---|---|---|---|---|
| `library-app-members-review` | 0 / 9 | 1.00, 1.00 | 0 / 3 / 0 | $0.29 |
| `library-app-notifications-review` | 0 / 9 | 1.00, 1.00 | 0 / 2 / 1 | $0.30 |
| `library-app-reporting-review` | 0 / 9 | 1.00, 1.00 | 0 / 3 / 0 | $0.30 |
| `security-review-http` | 0 / 10 | 1.00, 1.00 | 0 / 1 / 2 | $0.43 |
| `security-review-reminders` | 0 / 10 | 1.00, 1.00 | 0 / 1 / 2 | $0.29 |
| `reliability-review-alerts` | 1 / 15 (one judge flip, `no-false-alarm-burn-rate-alerts`) | 1.00, 1.00 | 1 / 2 / 0 | $0.37 |
| `reliability-review-portal-pay-pr` | 0 / 12 | 1.00, 1.00 | 0 / 3 / 0 | $0.36 |

Each one's directory, bar, evidence entry, row in
`tools/case_reading.json` and row in the coverage table are gone; the
two generated tables list them under "no case directory now". Their
plants are still in the fixture's `app/`, which other cases share. One
thing is left over: the overlay
`fixtures/library-app/code-plants/reliability-review/portal-pay/` was
copied by `reliability-review-portal-pay-pr` alone and no case uses it
now (the answer key says so). It was not deleted: removing a fixture
was not in the decision.

`user-story-writeup-payfine-phase1` fits the same pattern (0 / 7; 1.00
in both arms; the bare reply preferred three pairs of three) and **is
kept, by the owner's word during E7**: `user-story-writeup-payfine-phase2`
resumes a history frozen from it, and with phase 1 gone that history
could not be frozen again the next time the skill's text changes. It is
cut down to one judge.

**Cut down (decision 8).** In every kept case that E6 measured, a judge
that passed three runs of three in both arms is gone, except a
false-alarm trap and one judge on the case's most important planted
problem. Every grader that differed between the arms stays, whatever it
is. Tool checks stay: they cost nothing. Where the most important
planted problem is one whose judge differed, no second one is kept
beside it. The comment at the top of each case's graders names what was
cut. Bars are from the gate pass at three runs on 2026-11-15
(`record_thresholds.py --gate-only`).

| Case | Judges before, after | Judges cut | The judge kept on the planted problem, and why that one | Bar before, now |
|---|---|---|---|---|
| `library-app-fines-review` | 4, 3 | `finds-policy-mixed-with-mechanics` | `finds-provider-codes-leaking-through-port`: a provider's codes crossing a port into business logic is the case's dependency problem; the mixed method is a readability one (`finds-premature-waiver-strategy` differed and stays) | 1.00, 1.00 |
| `library-app-lending-review` | 6, 4 | `finds-http-request-in-place-hold`, `finds-use-case-reaching-into-wiring` | `finds-runtime-import-cycle`: the one problem that stops the app loading, and it differed (3/3 against 1/3) | 1.00, 1.00 |
| `library-app-structure-review` | 4, 4 | `finds-payment-sdk-outside-its-adapter` | `finds-technical-role-directories`: the layout is what a whole-app review is asked for; a judge on the runtime cycle is added (below) | 1.00, 1.00 |
| `code-review-days-left-pr` | 7, 5 | `finds-unused-flag`, `finds-rethrowing-catch` | `finds-unused-options`: of the four kinds of unneeded code it is the one on the function's public signature (`finds-impossible-null-check` differed and stays) | 1.00, 1.00 |
| `code-review-fine-notices-pr` | 8, 5 | `finds-triplicated-notice-logic`, `finds-what-comment`, `finds-duplicate-test-names` | `finds-false-dollars-comment`: a comment that states the wrong unit of money is the finding the case ranks first. `finds-wrong-name` stays as a trap: it carries the "vague name ranked below the wrong one" check | 0.97, 0.93 |
| `code-review-fines-report-pr` | 5, 4 | `finds-data-clump` | `finds-run-doing-several-jobs`: the case's first plant, and the one the others hang from | 1.00, 0.95 |
| `design-system-payfine-review` | 4, 3 | `finds-no-focus-state` | `finds-muted-contrast`: a measurable failure the document misstates (2.5:1 claimed as 6.01:1) | 1.00, 1.00 |
| `screen-design-payfine` | 7, 6 | `copy-rules` | none: the case plants no problem; the two that passed in both arms and stay (`no-screenshot-claimed`, `asks-nothing-the-docs-answer`) are traps | 0.97, 1.00 |
| `acceptance-criteria-payfine` | 2, 1 | `rejects-and-rewrites` | `flags-undecided-target`: deciding a time bound nobody agreed is the harm the skill is there to stop; rejecting "quick" is what any model does | 1.00, 1.00 |
| `requirements-refinement-payfine-phase1` | 4, 3 | `asks-before-writing` | none: `asks-trade-off-and-alternatives` and `stays-on-the-what` differed and are on the same subject; `does-not-ask-what-the-sources-answer` is a trap | 0.93, 0.92 |
| `reliability-review-fine-payment` | 4, 2 | `finds-retrying-declines-in-use-case`, `finds-pay-route-hides-unexpected-failures` | `finds-charge-then-settle-without-idempotency`: the member has paid and the fine stays owed | 1.00, 1.00 |
| `reliability-review-http` | 5, 4 | `finds-in-memory-holds` | `finds-respond-conflates-expected-and-unexpected`: every route goes through it (`finds-unbounded-loan-history` differed and stays) | 1.00, 1.00 |
| `reliability-review-nightly` | 8, 4 | `finds-no-isolation-in-fine-loop`, `finds-member-directory-pool-leak`, `finds-mailer-without-timeout`, `finds-postal-queue-swallows-errors` | `finds-unhandled-nightly-rejection`: the job dies with nothing logged, whatever else is fixed | 0.97, 1.00 |
| `accessibility-review-payfine` | 9, 6 | `finds-missing-live-region`, `finds-low-contrast-meta-text`, `finds-unlabelled-name-field` | `finds-unreachable-fine-choice`: the one the case ranks highest, and it differed (3/3 against 2/3). `says-it-read-the-markup` stays as a trap on a false claim | 0.98, 1.00 |
| `accessibility-review-payfine-subtle` | 9, 6 | `finds-hover-contrast`, `finds-broken-error-link`, `finds-no-visible-name-label` | `finds-pay-button-focus-removed`: the primary action, and found only by following the cascade | 1.00, 1.00 |
| `supply-chain-review-accepted` | 5, 3 | `finds-bare-allowlist-entry`, `finds-agpl-transitive` | `finds-unenforced-temporary-acceptance`: the same advisory as the trap that differed (`no-false-alarm-dev-only-advisory`), so the pair reads "flag the date nothing enforces, do not over-rate the advisory" | 1.00, 0.94 |
| `supply-chain-review-build` | 5, 3 | `finds-base-image-tag`, `finds-install-scripts-enabled` | `finds-image-build-ignores-lockfile`: the skill's own question (would the next build pull a bad version) answered yes | 0.96, 1.00 |
| `supply-chain-review-workflows` | 3, 2 | `finds-branch-ref-release-notes` | `finds-tag-pinned-slack-action`: it runs with the cloud credentials and every secret | 1.00, 1.00 |
| `test-quality-review-fines` | 7, 5 | `finds-unwired-mock`, `finds-weak-cap-assertion` | `finds-subject-mocked`: a test that cannot fail, and it differed (3/3 against 2/3) | 0.97, 0.88 |
| `security-review-config` | 5, 3 | `finds-long-lived-aws-keys-in-snapshot-job`, `finds-workflow-wide-secrets-and-default-permissions` | `finds-hardcoded-sendgrid-key`: a live key committed in source | 1.00, 1.00 |
| `security-review-portal-pr` | 5, 4 | `finds-sql-injection-in-history-search` | `finds-member-profile-idor`: it is seen only by reading the mount and the handler together, and the case's two traps are about the same judgement | 1.00, 1.00 |
| `map-update-cancel-hold` | 4, 3 | `untiered-edge-direction-unknown` | `flags-new-wrong-direction-edge`: what the map is regenerated for | 0.80, 0.81 |
| `staleness-audit-docs` | 5, 4 | `finds-orphaned-adr` | `finds-stale-lending-rules`: the page that tells a reader the wrong rules | 0.89, 0.93 |
| `vertical-slicing-handback` | 4, 3 | `owns-the-decision` | `does-not-grow-casually`: the ranked order is the skill's rule, and it cannot pass without a decision taken. `security-criteria-untouched` stays as a trap | 1.00, 0.92 |
| `why-comments-collect-fine` | 4, 3 | `deletes-what-comments` | `flags-the-wrong-comment`: the comment that says the opposite of the code | 1.00, 1.00 |
| `user-story-writeup-payfine-phase1` | 2, 1 | `does-not-ask-what-the-slice-answers` (by the owner's word: one judge) | `asks-where-before-writing`: the first turn's one job | 1.00, 1.00 |

Kept as they are, a reading of the decision and not the owner's words:
a case that plants no problem keeps the one judge on its subject even
though it passed in both arms, because without it an empty reply passes
(`names-what-holds-it-up` in the four clean-module cases,
`asks-before-settling`, `describes-the-change`,
`steps-cover-the-problem`, `real-limits`,
`decision-alternatives-consequences`,
`asks-the-problem-docs-open-questions`,
`finds-untested-email-channel`, `finds-new-code-mixing-levels` and
`finds-refund-created-then-refused-on-retry-unrecorded`, each the only
planted-problem judge of its case). The four `-via-agent`
twins of cut cases were not run bare and are untouched, so they still
carry the judges cut from the direct case.

**Without the fixture's `sources.md` (decision 6).**
`architecture-design-owner-sheet`, `screen-design-owner-sheet` and
`vertical-slicing-owner-sheet` no longer install the listing that
stated the data rule. One sentence of each prompt had to change with
it: it said the export "is listed in `docs/pay-fine/sources.md`" and
never named the file, so each now names `owner-files/desk-fees.csv` in
the words `requirements-refinement-owner-sheet` uses. The skills apply
the rule themselves: in all nine runs the file was listed in a new
`sources.md`, no cell of it reached the session and the owner was told
the examples are invented. Bars: 0.89 (one run of three failed
`fixtures-are-invented` on a split vote, FAIL PASS FAIL, over a reply
that says "I won't copy rows" and "the test data will be invented"),
1.00 and 1.00 (0.95 before). Their judges were left alone: what E6
measured in the bare arm was the old scaffold.

**The five grader fixes (decision 9).**

| Grader, case | What it did wrongly | The fix | Its first gate runs (three, 2026-11-15) |
|---|---|---|---|
| `found-with-the-scan`, `security-review-source-value` | passed three bare runs of three in E6 where no scan ran: the pattern was the script's name and `scan` anywhere in a `Bash` input, and the review, written through a heredoc, recommended the command | the input must run it: an interpreter, the script's path, `scan`, with no heredoc opened before it in the command | 3/3, each on one call that ran the scan. Over E6's six traces, with no model time: the three plugin runs still pass, the three bare runs now fail. Known limits: an `echo` of the command passes, a `--planning` pointed elsewhere passes |
| `a-long-single-job-function-stays-a-plain-finding`, `code-review-structural-high-at-d` | failed reviews that reported `describeEntry` for another reason (a High as dead code, confirmed by search) or said nothing about its length: 6 of 7 runs before E6, 2 of 3 plugin runs in E6 | a trap on the size alone: fails only when the function's length is sent to the architect or rated High or Critical; a finding about it for another reason passes at any severity | 3/3 on clean votes. The three reviews report it as code with no production caller (Medium) and unreachable lines; none hands its size on. Not yet shown to fail a wrong review. Bar 0.80 to 1.00 |
| `finds-orm-inside-checkout-use-case`, `library-app-lending-review` | "a must-fix / top-tier finding" was read as the review's highest severity: a review with the finding at High and the right fix, second to the Critical cycle, failed three votes of three (and five earlier runs) | High or Critical passes, and the criterion says that a High below the Critical cycle does; Medium, Low or optional fails | 3/3 on clean votes; all three reviews rate it High, second to the cycle at Critical. Not yet shown to fail a Medium. The `-via-agent` twin keeps the old wording (not in E7) |
| `finds-runtime-import-cycle` (new), `library-app-structure-review` | no grader read the one thing the bare model missed there three runs of three, so both arms scored 1.00 | a judge on the `Loan`/`LoanPolicy` cycle as a load problem to fix; another cycle does not count, and no rank is asked for | 3/3 on clean votes; each review has it, rated Critical. Its bare arm has not been run: by E6's reading the bare reviews would fail it, by the grader that is unmeasured |
| `listing-names-the-location`, `requirements-refinement-owner-sheet` | with no `sources.md` written, the CLI reported "grader threw" and the bare runs counted as errored, not failed | the scaffold leaves an empty `sources.md`; `source-listed` (the file exists) went, since it could no longer fail | 3/3; each run read the empty file, wrote the listing and asked. The bare arm was not run again |

**`problem-framing-doc-payfine` as two turns (decision 11).**
`-phase1` keeps the prompt and grades the question: the skill invoked,
nothing written (a regex on the trace), a question about what the
description leaves out, and one question, not a list. Three runs of
three asked why it is worth solving now and wrote nothing. `-phase2`
resumes run 1 of that pass (`history.jsonl`, frozen with
`freeze-history.sh`) with an answer that covers every section left, and
grades the document with the three judges the one-turn case carried.
Bars 1.00 and 1.00. One grader was corrected twice on its first runs,
which is the rule of "Judges turned into tool checks" at work:
`why-now-is-the-users` began as a judge (the reason is the user's, no
trigger invented) and failed four right documents of six, on full and
split votes, whose section said that nothing forces it, that there is
no deadline, and that the cost is desk time every shift; rewording the
criterion changed nothing, and two documents worded the same way
passed. It is a regex now (a Why now section that holds the user's
reason), passes the six documents already written, and no longer reads
an invented trigger.

**`map-update`'s diff (decision 12), diagnosed with no model time.** The
cause is the script's, not the model's: `extract_map.py`'s `parse_prior`
reads a prior row's edges, packages and exports only from names between
backticks, and the fixture's prior map (written two weeks before the
script) has bare cells, so every module's prior edges and exports are
empty and all of them come out as new: 151 change lines with the script
alone on the case's scaffold, the same 151 as the failed run's map.
With its own output as the prior the script reports no change. The
full account and the two ways to fix it are `TODO.md`'s B9. Nothing was
fixed; `pre-existing-flags-not-new` failed three runs of three again.

**What it cost, and one run of every case.**

| | Figure | How it is known |
|---|---|---|
| E7's gate runs: 34 cases at three runs (102), two more passes of `-phase2` after its grader changed (6), the `--stale` pass (2), one single run of the 34 (34) and its re-runs (18) | 162 runs, $47.38 | measured: the CLI's `costUsd`, list prices; the session that ran and read them is not in the figure. One usage window, not cut |
| The seven dropped cases, one run each | $2.34 | measured: the mean of each case's six single gate runs of 2026-11-10 to 14 |
| The 27 changed cases that had single runs before, one run each | $9.02 before, $7.76 after | measured: the same means before; one single gate run each on 2026-11-15 after. Judges $3.42 to $2.26; the agent's own cost $5.60 to $5.50, which is noise |
| Five changed cases with no single run before (`staleness-audit-docs`, the three `supply-chain-review` cases, `why-comments-collect-fine`) | $1.10 after; about $0.15 less than before | after measured; the saving estimated, their seven cut judges priced at the mean of the fifteen left |
| `problem-framing-doc-payfine`, now two cases | $0.15 | measured; the one-turn case had never run and was not in the baseline |
| **One run of every case** | **about $41.7**, against $45.70 at the baseline and about $45.3 after E5 and E6 | estimated from the measured parts above: $45.3, less $2.34, $1.26 and $0.15, plus $0.15. Not measured as a whole: that takes one run of all 160 cases |
| The table above ("The cases sorted") | $46.81 over 147 cases, $48.13 before | not the measure: it averages three-run results in, where the CLI records about twice the judge cost per run |
| The gate's re-run rate, the 34 changed cases | 6 of 34 first runs re-run (18%) | measured on the one single pass, too few to be a rate; 7.9% over all cases before E5, 12.8% for E5's changed cases. Five of the six were a judge on a long review failing once, one a skill not invoked (below); all six passed on the re-run |

Fewer graders in a case make one flip weigh more, which is the likely
reason the changed cases re-run more often than the suite did; it was
not tested.

**Found by E7 and left for phase B or the grader list; nothing fixed.**

- `map-update`: the diff, above (`TODO.md` B9). And one run of three
  left the new module untiered where the design names its tier, so the
  wrong-direction edge was listed as direction unknown: the kept judge
  caught it.
- The data rule in the owner-sheet cases: the skills list the file and
  quote nothing, but they look at its shape with `Read` and `Grep` on
  the file itself (nine of twelve runs; these cases grant no `Bash`, so
  `source_scan.py describe` cannot run), and one `vertical-slicing` run
  searched the export for the names it had invented. The fixture's old
  `sources.md` said "never `cat`, read or grep one".
- `code-review` was not invoked in `code-review-days-left-pr` in three
  of four runs of the single pass and its re-run (0 of 3 in E6's plugin
  arm, 3 of 3 in the three-run pass): the review is written without the
  skill about as often as with it.
- `test-quality-review`: `no-false-alarm-exact-tests` failed 2 runs of 3
  again and `no-false-alarm-fake-ledger` 1 of 3 and 2 of 3 (decision 3's
  pattern, `TODO.md` B7).
- `requirements-refinement`'s first turn asks something the sources
  answer in one run of three in each pass of the day
  (`does-not-ask-what-the-sources-answer`), as `security-requirements`
  did in E6.
- `supply-chain-review-accepted` rates the dev-only advisory in one run
  of three, as in E6. `staleness-audit-docs` misses the ceremonial
  sign-off log one run of three. `code-review`'s mocking rule fails two
  runs of three, as before (`TODO.md` B8).
- Grader findings, with the older open ones: `fixtures-are-invented`
  (`architecture-design-owner-sheet`) failed a reply that says it, on a
  split vote; `library-app-lending-review-via-agent` still has the ORM
  wording E7 fixed in the direct case; the four `-via-agent` twins
  repeat judges their direct cases no longer carry.
- A judge asked two things about one section of a long document was
  noise (`why-now-is-the-users`, above): a new case's judge on a file
  wants its first runs read before its bar is believed, as a check's
  do.
- Seen in E6's traces while fixing the scan grader: two bare runs of
  `security-review-source-value` listed the plugin installed under the
  home directory's plugin cache while looking for the script. E6 read
  them as not finding it, and no scan ran; but the bare arm can see an
  installed copy of the plugin on this machine.
- The overlay `code-plants/reliability-review/portal-pay/` has no case.

### The review rebalance

`TODO.md`'s phase B, part 2 (B1 to B6; 2026-11-15 and 16, kad 0.15.0,
Claude Code 2.1.325, every case on Sonnet). The owner's order: this
part before part 1 (B7 to B10, G1, G2), then part 1 checked again
against what these runs show (the last table here). What changed: the
gate holds eight more categories from a per-project file, the chunk
reviewer no longer reports what the gate holds, the slice review runs a
mutation pass on the changed lines and a cold read, the slice's
deferrals are listed once by a script, and CI runs on two systems. 166
cases (160 before): six new, graders added to four.

**Per item: what was built, its "done when", and what it fails without.**

| Item | Built | "Done when", and the counts | Fails without |
|---|---|---|---|
| B1 gate categories per stack | `validation_gate.py` reads `gate-checks.json` at the project root: one entry per category, as a command that passes on exit 0, a command whose violations are counted against a `baseline`, `covered_by` a check the gate already runs, or `not_picked` with a reason; `--record-gate-baselines`; changed-line coverage from the lcov report. `technology-bootstrap` picks the tool per stack and records a `Gate checks` section; the orchestrator's A.5 launches the wiring | `tools/gate_checks_test.py`, no model (15 tests): on the library fixture, whose loop base now carries the eight categories, a clean chunk passes with every category on the `gate covers` line and the older code's violations as the baseline (unused exports 10, deep nesting 4, duplication 1), and one planted violation per category fails the gate on that category's line and no other. `technology-bootstrap-phase2`'s `gate-checks-recommended-with-the-set` 3 of 3 and `-phase3`'s `gate-checks-section-holds-the-eight` 3 of 3 | reference `gate-checks-recorded` on `technology-bootstrap-phase3` (the section removed from the skill): below |
| B2 the chunk reviewer's brief | `code-review`: "What the gate holds is not yours to report", and the same exemption at the top of its Duplication section; one sentence each in `test-quality-review` and `reliability-review` | `code-review-chunk-gate-covers` (new): chunk 1's queue finds a hold by the start of its card number and opens each of its four methods with the same four lines, short of what the duplication check counts, so the gate passes. `wrong-match-is-a-finding` 3 of 3, `duplication-left-to-the-gate` 3 of 3 | reference `gate-holds` |
| B3 the cold read in the slice review | the `cold-read` skill; the orchestrator's D.4 launches it with round 0's reviewers in place of the stranger test, and its confirmed findings go to the fix round | `cold-read-new-beside-old` (new, capability): the reader finds, by running it, that a hold's stored position is wrong after the slice's new cancel (the older `PlaceHold` numbers a new hold from the queue's length). `positions-bug-confirmed-by-execution` 3 of 3; the finding is in the report of all nine runs made (the first, single, run failed two checks that were narrower than its right answer) | reference `pair-new-with-old` |
| B4 mutation on the changed lines | `mutation_pass.py` moved beside the orchestrator's scripts, with `changed` (one mutant per operator on the lines a range added) and `run --allow-dirty`; D runs both after the Definition of Done; `test-quality-review` reads every survivor | `tools/mutation_pass_test.py` (13 tests): on the fixture's built slice the pass gives 11 mutants, 9 caught, 2 survived, one of them the card-length rule no test holds. `test-quality-review-survivors-at-d` (new): `unguarded-rule-is-a-finding` 3 of 3, `equivalent-survivor-read-not-reported` 3 of 3. `orchestrator-mutation-before-review` (new): the pass run after the Definition of Done and before any reviewer, 3 of 3 | references `survivors-read` and `mutation-before-reviewers` |
| B5 deferrals listed once | `deferrals.py` writes the body's `Deferred with this slice` section from the slice file; `delivery` splices it in; the restating paragraph is gone from `architecture-review`, `security-review`, `reliability-review` and `accessibility-review` (the item named three; the fourth carried the same text) | `tools/deferrals_test.py` (5 tests). `security-review-deferrals-not-restated` (new): `no-deferral-restated` 3 of 3. `orchestrator-delivery-foreground`: `deferrals-listed-by-the-script` 3 of 3, `body-carries-the-deferrals-section` 3 of 3 | references `deferrals-not-restated` and `deferrals-by-script` |
| B6 CI on two systems | `ci-pipeline`'s checks job on `[ubuntu-latest, macos-latest]`, the audit job on Linux alone, gate checks that are manifest scripts as steps | `ci-pipeline-os-matrix` (new, the skill's first case): `checks-run-on-linux-and-macos` 3 of 3, every action pinned to a looked-up commit 3 of 3 | reference `two-operating-systems` |

**Known-bad references** (`skill_mutation.py run`, three runs each on
a scratch copy with the rule's text removed; 2026-11-16). Each must
fail the graders named, and does:

| Reference, case | The text removed | Graders that failed (passes of three) |
|---|---|---|
| `gate-holds`, `code-review-chunk-gate-covers` | the "What the gate holds" paragraph and the exemption at the Duplication rule | `duplication-left-to-the-gate` 0 of 3. With the paragraph alone removed it still passed 3 of 3: the exemption at the rule holds by itself |
| `pair-new-with-old`, `cold-read-new-beside-old` | step 4, "Pair the new with the old", and the report's Pairs section | `pairs-probed-listed` 0 of 3 and `positions-bug-confirmed-by-execution` 0 of 3: without the step no run reported the position bug |
| `survivors-read`, `test-quality-review-survivors-at-d` | "At the slice review, the survivors" | `equivalent-survivor-read-not-reported` 0 of 3 |
| `mutation-before-reviewers`, `orchestrator-mutation-before-review` | D's mutation step and the three other places the skill names the pass | `mutants-written-for-the-changed-lines` and `mutation-pass-run-on-the-loop-tree` 0 of 3. With the step alone removed the pass still ran 3 of 3 |
| `deferrals-not-restated`, `security-review-deferrals-not-restated` | the new sentence, replaced by the old restating one | `no-deferral-restated` 0 of 3 |
| `deferrals-by-script`, `orchestrator-delivery-foreground` | `delivery`'s deferrals paragraph and body part | `body-carries-the-deferrals-section` 0 of 3; the script itself still ran 2 of 3, since the orchestrator's E step names it too |
| `two-operating-systems`, `ci-pipeline-os-matrix` | the two-systems rule, back to one `ubuntu-latest` job | `checks-run-on-linux-and-macos` 0 of 3 |
| `gate-checks-recorded`, `technology-bootstrap-phase3` | "Gate checks, picked per stack", its output-format part and its re-entry line | `gate-checks-section-holds-the-eight` 0 of 3 |

A rule the skill states in several places survives the removal of one:
three of the eight references passed their case on a first run for that
reason and were widened.

**Not held by a case.** The orchestrator's A.5 (a present file, the
wiring launch, "after chunk 1", the route back to the bootstrap) and its
launch of the cold reader. One unplanned run is the only evidence for
the second: the first form of `ci-pipeline-os-matrix` left a handoff
file in its state, the model resumed the loop instead of writing CI,
and the orchestrator ran D.3 whole: the test-quality reviewer handed the
mutation report, the cold reader launched with `cold-read` named and no
planning document in its task. That run cost $4.85 and its result is
kept outside the results history. Slice 3 is the first real run of
both.

**B1's check without a run: the picked checks on the first project.**
Applied to `personal-finance-tracker-3` at `main` on a scratch clone,
counts only; its existing gate is clean there (typecheck, lint and
format at 0, 495 tests pass).

| Category | Picked check (TypeScript, the survey's list (a)) | `src/` | `test/` | Baseline form |
|---|---|---|---|---|
| Type-aware lint | typescript-eslint `strictTypeChecked`, already installed (its lint resolves TypeScript 6.0.3) | 96 | 945 | ESLint's suppressions file |
| Stricter compiler flags | `noUncheckedIndexedAccess` | 5 | 263 | a count in `gate-checks.json` |
| | `exactOptionalPropertyTypes` | 35 | 16 | |
| | `noPropertyAccessFromIndexSignature` | 37 | 115 | |
| | `noImplicitReturns` | 1 | 0 | |
| | `noImplicitOverride`, `noFallthroughCasesInSwitch` | 0 | 0 | |
| Complexity and length | ESLint core: `complexity` over 10 | 8 | 4 | ESLint's suppressions file |
| | `max-params` over 4 | 8 | 3 | |
| | `max-lines-per-function` over 40, IIFEs counted | 8 | 12 | |
| | `max-statements` over 25 | 5 | 3 | |
| | `max-lines` over 300 | 0 | 11 | |
| | `max-depth` over 4 | 0 | 0 | |
| Duplication | jscpd 5 (5 lines, 50 tokens) | 0 clones | 93 clones, 988 lines, 8.5% | a count |
| Unused code | knip 6 | 2 files, 3 exports, 3 types | | a count |
| Changed-line coverage | the gate's own lcov read | 5 uncovered lines of 3,849; 32 untaken branches of 1,339 | | none: only changed lines are judged |
| Test timeouts and random order | `--test-randomize`, five seeds | 0 failures | | none |
| | `--test-timeout=5000` | 3 tests cancelled, and the run then never exits | | those three fixed, or a higher limit |
| Secret scan | gitleaks 8.30.1, history and tree | 0 | 1 | gitleaks' baseline file |
| Workflow scan | actionlint 1.7.12, zizmor 1.31.1 offline | 0 and 0 | | none |

Whether the limits measure the cold reads' readability findings ("140-column
lines and two 190-to-220-line IIFEs"): the long functions, yes, with one
option set (`src/` has two functions over 80 lines at `main`, 154 and
189, both function expressions called on the spot, which ESLint skips by
default and the gate's own size line never saw); the wide lines, no lint
does (the formatter's width is 140 and `eslint-config-prettier` switches
`max-len` off: 418 `src/` lines are over 100 columns, 204 over 120), so
the bootstrap records a width with this category. 474 of the 945 test
hits are `no-floating-promises` on the runner's own `test()` calls,
which a configuration exempts instead of baselining.

**Read from the first failures** (the rule of "Judges turned into tool
checks", and what it found this time):

- Two of my checks stopped at the first brace of a shell command
  (`[^{}]*` before `git clone` and before the body's heading), so
  `${TMPDIR:-/tmp}` in the command failed right runs. Both are
  `tool_used` checks on the command now.
- `body-carries-the-deferrals-section` looked for the heading in the
  body's text; all three runs had spliced the script's file in
  (`cat "$TMPDIR/kad-pr-deferred.md" >> body`), which is the verbatim
  the skill asks for. It reads the splice or the heading.
- `positions-bug-confirmed-by-execution` asked for `PlaceHold` by name
  and failed a right finding that said "at placement".
- **B2's paragraph did not hold on its first run**: the review reported
  the repeated lines as a Medium under the skill's own Duplication
  rule, further down the file. The exemption now also stands at that
  rule. A rule that exempts something wants to sit where the thing is
  prescribed.
- `duplication-left-to-the-gate` then failed three runs that reported
  no duplication: one finding was the test lens's "two tests assert the
  same thing" (Category "duplicate"), two said the repeated lines are
  needless in themselves ("a ternary that does nothing"). The planted
  block is ceremony as well as repetition. The check now reads a
  finding on the source whose title or Category is duplication; a
  review that reports the copies under another Category passes it,
  which is its limit.
- `orchestrator-definition-of-done` first carried B4's orchestrator
  checks. My reworded stopping point ("before any slice reviewer") made
  two runs of three stop before the comments review, which is a
  reviewer; restored. Then two runs of three never reached the pass: a
  gate failure after the fix sent a second fixer, the review's fix
  budget was spent and the flow stopped for the owner. Two of those
  gate failures were the older "a file no test loads"; one was a new
  check at work (an export nothing imports, 11 against a baseline of
  10). The step has its own case and state now.
- `technology-bootstrap-phase3-reject`'s `asks-only-what-the-first-test-forces`
  failed documents whose `Gate checks` section names a workflow scanner
  "for when a workflow exists" (a judge on a 9,000-character file: split
  and full votes on like documents). Its criterion now says what the
  section is, in the three phases that carry it.
- `code-review-comments-chunk`: the reviewer applied the test-quality
  and reliability lenses without invoking their skills in 7 of the first 13 runs
  on this branch (11 of 44 before), and said so in its hand-back. One
  sentence in `code-review` ("a lens applied without its `Skill` call
  has not been applied"): 3 of 3 invoke both since. The case's prompt
  now hands the gate output the real launch always hands. With the
  lenses invoked and the cold pass's probes, two runs of three call the
  fixture's "why only the first hold is removed" comment false, and by
  the code they are right (it says a doubled hold "must not take two
  cancels to clear" and one cancel removes one): `why-comment-is-not-flagged`
  is a trap on a comment that is wrong. Not fixed: the fixture is shared.
- `tdd-implementation-lite-cancel-hold`'s `escalates-queue-question`
  failed three reports on split votes that say what nineteen earlier
  passing reports say; left alone, it passed 3 of 3 on the next pass.

**The external review's round** (Sourcery, 13 comments on the first
commit; the owner's instruction for this round: a fix that sends a
batch of cases back through the gate is weighed before it is applied).
Applied, at one to four cases each: `ci-pipeline` runs a gate check in
CI only when its exit code is its verdict (a counted entry with a
baseline above 0 exits non-zero on violations already accepted, so it
is listed as not run in CI), and names every runner it supports, not
two; `mutants-file-outside-the-tree` refuses any relative `--out`;
`a-probe-was-run` (new) wants a `node` run in the trace beside the
report's "confirmed by execution"; `no-deferral-restated-in-a-finding-body`
(new) reads a finding's body for the slice file's own words. Declined
with the reason on the thread: failing a counted check on any non-zero
exit (the tools exit non-zero on every finding; the count against the
baseline is the verdict), treating lines lcov does not instrument as
uncovered (they are the non-executable ones; a file missing from the
report already fails), a time-bounded regex engine for the project's
own `count` pattern, and a job-scoped matrix check. Deferred to the
next change under `skills/orchestrator/` (each would stale that
directory's 38 cases, about 115 runs, for hardening and no defect in
ordinary use; `TODO.md`, under B1 to B6): the mutants file written
with private permissions and removed after the pass, the mutation pass
in a disposable clone so a killed run cannot leave a mutant in the
tree, `deferrals.py --out` creating its parent directory, and a
`nosemgrep` note on `added_lines`' git call. One more check of mine was
wrong on its first runs: `a-probe-was-run` used `\bnode`, and the
input is matched as JSON, where a line break is the two characters
`\n`, so a probe written and run in one command failed it.

**Every bar that moved** (`record_thresholds.py --gate-only`, from
three-run gate results only; a first recording took the single pass
below as each case's newest result and was redone with it excluded).
110 cases were re-recorded; these 31 moved, and six are new.

| Case | Bar before | Now | The graders behind it (passes of three, before→now) |
|---|---|---|---|
| `architecture-design-owner-sheet` | 0.89 | 1.00 | `fixtures-are-invented` 2→3 of 3 |
| `code-review-catalog` | 0.89 | 0.94 | `nothing-above-low` 1→2 of 3 |
| `code-review-days-left-pr` | 1.00 | 0.92 | `skill-invoked-display` 3→1 of 3 |
| `code-review-fine-notices-pr` | 0.93 | 0.89 | `consults-why-comments` 3→2 of 3 |
| `code-review-fine-notices-pr-via-agent` | 0.83 | 0.92 | `consults-why-comments` 0→3 of 3 |
| `code-review-fines-report-pr` | 0.95 | 1.00 | `finds-month-as-raw-string` 2→3 of 3 |
| `delegation-consult-without-file` | 0.92 | 1.00 | `recommendation-only-named-as-undelegated` 2→3 of 3 |
| `library-app-catalog-review` | 1.00 | 0.93 | `reports-nothing-above-low` 3→2 of 3 |
| `library-app-lending-review-via-agent` | 1.00 | 0.96 | `finds-orm-inside-checkout-use-case` 3→2 of 3 |
| `orchestrator-backward-route` | 0.91 | 1.00 | `log-names-the-hand-back` 2→3 of 3; `routes-back-to-the-owner` 2→3 of 3 |
| `orchestrator-budget-exceeded` | 0.80 | 0.87 | `flow-ends-saying-what-is-built` 0→1 of 3 |
| `orchestrator-chunk-runner-launch` | 1.00 | 0.96 | `handoff-says-the-runner-is-in-flight` 3→2 of 3 |
| `orchestrator-delivery-foreground` | 0.96 | 0.91 | `body-carries-the-deferrals-section` new→3 of 3; `cost-script-run` 2→1 of 3; `deferrals-listed-by-the-script` new→3 of 3; `pr-writeup-invoked` 3→2 of 3 |
| `orchestrator-issue-fix-records` | 0.97 | 1.00 | `branch-names-the-slice-and-the-issue` 2→3 of 3 |
| `orchestrator-plan-check-seam` | 0.95 | 1.00 | `plan-sent-back-not-edited` 2→3 of 3 |
| `orchestrator-readiness-gate` | 1.00 | 0.96 | `backward-routes-name-the-checks` 3→2 of 3 |
| `orchestrator-readme-stale-not-done` | 0.83 | 0.89 | `one-fixer-for-the-batch-plus-at-most-a-gate-fixer` new→2 of 3 (the bar on main still named `one-fixer-for-the-batch`) |
| `orchestrator-route-accessibility` | 0.96 | 1.00 | `screen-design-only-after-the-review` 2→3 of 3 |
| `orchestrator-route-reliability` | 1.00 | 0.96 | `log-names-row-and-artifact` 3→2 of 3 |
| `orchestrator-route-scope-decision` | 0.94 | 1.00 | `stops-after-the-routed-step` 2→3 of 3 |
| `orchestrator-route-screen-design` | 0.95 | 1.00 | `log-names-row-and-artifact` 2→3 of 3 |
| `orchestrator-route-tech-bootstrap` | 1.00 | 0.95 | `log-names-row-and-artifact` 3→2 of 3 |
| `reliability-review-fine-payment` | 1.00 | 0.93 | `no-false-alarm-settled-fine-guard` 3→2 of 3 |
| `tdd-implementation-lite-cancel-hold-via-agent` | 0.91 | 0.89 | `escalates-queue-question` 3→2 of 3; `final-review-runs` 1→0 of 3; `no-queue-behaviour-built` 3→2 of 3; `tests-check-behaviour` 1→3 of 3 |
| `tdd-implementation-lite-named-fix` | 1.00 | 0.95 | `final-review-runs` 3→1 of 3 |
| `tdd-implementation-lite-rename-fix` | 1.00 | 0.98 | `no-shell-writes-into-the-tree` 3→2 of 3 |
| `technology-bootstrap-phase2` | 1.00 | 0.96 | `gate-checks-recommended-with-the-set` new→3 of 3; `recommends-the-built-in-default-set-once` 3→2 of 3 |
| `technology-bootstrap-phase3` | 0.89 | 0.96 | `asks-only-what-the-first-test-forces` 3→2 of 3; `gate-checks-file-left-to-the-build` new→3 of 3; `gate-checks-section-holds-the-eight` new→3 of 3; `records-non-choices-and-open-categories` 1→3 of 3 |
| `technology-bootstrap-phase3-reject` | 0.91 | 0.95 | `does-not-relitigate` 1→2 of 3 |
| `vertical-slicing-handback` | 0.92 | 1.00 | `leaves-the-what-to-requirements` 2→3 of 3 |
| `vertical-slicing-payfine-phase1` | 1.00 | 0.96 | `stays-in-confirmed-scope` 3→2 of 3 |

New, as recorded after the external review's round (below):
`ci-pipeline-os-matrix` 0.96 (one run left the lint step out: the
manifest has the script and no `eslint` dependency),
`code-review-chunk-gate-covers` 1.00, `cold-read-new-beside-old` 1.00
(the position bug is in the report of 14 of the 15 runs made; one
paired it, ran no probe on it and said "nothing older reads
`position`"), `test-quality-review-survivors-at-d` 0.95 (one run read
the equivalent survivor as equivalent and also raised its redundant
guard as a finding), `security-review-deferrals-not-restated` 0.94 (one
run wrote no criteria pass, another did not open the slice file),
`orchestrator-mutation-before-review` 1.00 (0.92 on its first pass: one
run launched a fixer first and did not carry the count).
Most moves are one grader by one run in either direction. Three are
this change: `technology-bootstrap`'s (a longer document, more judge
noise on it), `orchestrator-delivery-foreground`'s (two new checks at 3
of 3; `cost-script-run` 1 of 3, the script not readable from the
sandbox in those runs) and `code-review-days-left-pr`'s, which is not a
move so much as E7's finding measured again (the review written without
the skill: 8 of 13 runs on this branch).

**What it cost, and one run of every case.**

| | Figure | How it is known |
|---|---|---|
| This change's gate runs: the affected cases at three runs (two passes cut by the usage limit and resumed with `--stale`), the re-runs after each fix, the single pass, the references | 626 runs, $231.92 | measured: the CLI's `costUsd`, list prices; four usage windows, cut three times. The session that ran and read them is not in the figure |
| One single run of the 110 affected cases (2026-11-16) | $37.95 | measured |
| The 104 of them that had single runs before, one run each | $35.46 before, $36.65 after | measured: before is the mean of each case's single gate runs of 2026-11-10 to 15 |
| The six new cases, one run each | $1.31 | measured ($0.16 to $0.35 each) |
| **One run of every case** | **about $44.2**, against about $41.7 after E7 | estimated from the measured parts: $41.7, plus $1.19 on the existing cases and $1.31 for the new ones. The 56 cases this change does not reach were not run |
| The gate's re-run rate, the single pass | 7 of 110 first runs re-run (6.4%) | measured; 7.9% over all cases before E5, 6 of 34 on E7's changed cases. Four passed on the re-run. Three did not: two bars recorded from a clean three-run pass that the next runs did not repeat (`code-review-comments-chunk`, `code-review-days-left-pr`), one the judge on the bootstrap's longer document, above |

The first estimate given to the owner was 370 runs and $100 to $115;
the fixes read from failures and the second code-review pass are the
difference.

**Part 1, checked against these runs.** Nothing was fixed.

| Item | Verdict | The evidence here |
|---|---|---|
| B7 nothing above Low on a sound module | still needed | the four clean-module cases at three runs: `library-app-catalog-review` 2 of 3 (3 of 3 at its bar), `code-review-catalog` 2 of 3 (1 of 3), `reliability-review-catalog` and `security-review-catalog` 3 of 3; `test-quality-review-fines`' `no-false-alarm-exact-tests` 1 of 3 and `no-false-alarm-fake-ledger` 2 of 3, both as before. B2 narrows the chunk review only; these cases are standalone reviews and no gate line reaches them |
| B8 a serious problem read past is handed on; the mocking rule | still needed | `leaves-mocking-to-test-quality-review` 1 of 3 on `code-review-fine-notices-pr` and 0 of 3 on its `-via-agent` twin, both as before |
| B9 `map-update`'s diff | still needed, unchanged | the case is not reached by this change and was not run; the cause is the script's |
| B10 owner-sheet cases open the owner's file | still needed | `Read` or `Grep` on the export in 2 of 3 runs of `architecture-design-owner-sheet` and of `vertical-slicing-owner-sheet` |
| B10 `map-update` untiered module; `requirements-refinement`'s first turn | still needed, no new evidence | neither case is reached by this change |
| B10 `code-review` not invoked in `code-review-days-left-pr` | still needed, and worse than recorded | not invoked in 8 of 13 runs here; its bar is now 0.92 with the grader at 1 of 3 |
| B10 `test-quality-review` on the designated fake | still needed | `no-false-alarm-fake-ledger` 2 of 3 |
| B10 the `-via-agent` twins' old judges and wording | still needed | untouched; `library-app-lending-review-via-agent` lost its ORM judge once (2 of 3) on the old wording |
| B10 the overlay with no case | still needed | untouched |
| G1 the runner hands back while its builder works | still needed before slice 3 | `hand-back-is-one-line-for-what-ran` 3 of 3 on `chunk-runner-waits-for-handback`, as at its bar; no run showed it, and one case cannot (the wait cannot be held in the eval) |
| G2 a paragraph before the one line | still needed | `hand-back-is-one-line-and-nothing-else` 2 of 3 on `chunk-runner-one-fix-round`, as before. `chunk-runner`'s text was not touched by this change, so G1 and G2 are still one edit |

Two things part 2 adds to part 1's list: the planted block of
`code-review-chunk-gate-covers` is ceremony as well as repetition (a
block that is reasonable once would make its check exact), and the
fixture's "why only the first hold" comment is false
(`why-comment-is-not-flagged`).

### The loop's fixes

`TODO.md`'s PR 1 (2026-11-16, kad 0.15.1, Claude Code 2.1.325; runner
cases on Opus, the rest on Sonnet). One edit each to `chunk-runner`,
the orchestrator and its scripts, `delivery` and the loop fixture. 170
cases (166 before): six new, the two replay cases dropped.

**How it was gated** (the owner, 2026-11-16: three runs where a bar can
move, one run elsewhere). 20 cases at three runs: the six new ones, the
seven older `chunk-runner` cases, and seven whose graders, prompt or
state changed in purpose. The other 41 cases the change reaches ran
once against the bar they had, all 41 at or above it. A miss that
happens one run in three passes such a single run two times in three:
those 41 bars did not move and say nothing new.

**Per item: what was built, its "done when", and what it fails without.**

| Item | Built | "Done when", and the counts | Fails without |
|---|---|---|---|
| G1 the wait | A turn ended to wait ends on nothing or on `waiting: <agent>`, and is said not to be the hand-back | The cause, from the trace `gate-20261114T222734-rerun-chunk-runner-waits-for-handback-run2`: **the runner did not hand back early.** The builder's launch ran in the background, the runner ended its turn to wait as the skill told it to, and that turn ("The chunk 1 builder is running. Next I'll wait for its report") is the trace's first `result` row. The builder's notification woke it, it ran the gate, and the last `result` row is its reply, which failed for a paragraph before the line (G2). `hand-back-is-one-line-for-what-ran` on `chunk-runner-waits-for-handback`: 10 runs of 10 on the new text (one single run, three passes of three) | reference `handback-one-line` on that case, 0 of 3. The wait itself has no reference: an eval cannot hold a runner in it. One run of `orchestrator-autopilot-counts-over` showed the marker read: woken by a runner that had stopped on `waiting: reviewer, smoke`, the orchestrator wrote "that notification isn't a hand-back" |
| G2 the one line | The Hand-back section says where the line starts and ends and that a paragraph before it is read by nobody; the stopping-point rule says `stopped at` is the whole of what a stop says; the orchestrator reads the last line of a hand-back | First, whether it matters: all 11 real runner hand-backs in the audit transcripts were the one line, and each C line took its hash, so the paragraph shows in the eval, where the runner is the session and speaks to a user. `hand-back-is-one-line-and-nothing-else` on `chunk-runner-one-fix-round`: 3 of 3 (2 of 3 at its bar), and `skill_mutation.py run --case chunk-runner-one-fix-round --rule handback-one-line` exits 0 | reference `handback-one-line`, 0 of 3. Not gone for good: 1 run of 6 under two unrelated deletions still put a paragraph first |
| F2 a gate's own fixer | Step 4: a `FAIL` on a fix's gate gets its own one fixer, and the two capped fixers are the review's (`Fix r1`, `Fix r2`) | `chunk-runner-fix-gate-fails` (new): fix r1 carries a file outside the modules, its gate fails, one gate fixer, the gate again, the re-review, 3 of 3. `chunk-runner-one-fix-round`, whose state now has a gate fixer already run: the regression still gets its `Fix r2`, 3 of 3 | nothing: with F2's text removed both cases passed 3 of 3 (step 2's "a `FAIL` goes to one fixer" and the regressions sentence carry it). The run that left a regression as "no third fixer" is not reproduced; the text now says it and no case shows the miss |
| F5 the last-fix review | The runner's step 5 after a `Fix r2`; the same review at D after its last fix and once at E over CI and triage fixes; `rounds_record.py --last` (its findings stand; before, they were classed as regressions and never listed, so their Mediums would not have been filed) | `chunk-runner-last-fix-review` (new): a fix r2 that still prints a short card number whole, under a test whose name says otherwise. One reviewer launched on the diff, no fixer after it, the defect in the report, 3 of 3. `chunk-runner-one-fix-round`: a real fix r2 gets one last-fix review and no fixer, 3 of 3. `tools/rounds_record_test.py` (2 tests) | reference `last-fix-review`: `one-last-fix-reviewer` and `last-review-written` 0 of 3 |
| C2 autopilot | `autopilot.md`, asked once per project at A.2. Under it the clock is the only cap; a Critical or High left standing gets up to two rounds of verify, fix and last-fix review; a readiness correction that changes no decision is written without a question (the owner's three answers, 2026-11-16) | One stop taken: `orchestrator-autopilot-counts-over` (new), four reviewer launches against two, one hour into five: chunk 2's runner launched, no `budget exceeded`, 3 of 3. One still the owner's: `orchestrator-budget-exceeded`, the same file and the loop time exceeded: the flow ends, 3 of 3 | no reference: with the skill's sentences on the counts removed the run still went on, 3 of 3, from the fixture's `autopilot.md`, which states the rule in the owner's words as a real one does |
| F6 the external review's wait | `delivery` asks the repository's history whether a bot has ever commented before it waits | `orchestrator-delivery-foreground`: `review-history-asked-before-any-wait` 2 of 3, `no-wait-for-a-bot-that-never-reviewed` 3 of 3 | not run as a reference |
| F7 the target from the project | Step 1 takes the directory the project's memory or `CLAUDE.md` names, and the first log entry carries `target: <dir> (named by <where>)` | `orchestrator-target-from-project` (new) 3 of 3; `orchestrator-asks-for-target` still asks, 3 of 3 | reference `target-from-project`: no log written, 0 of 3 |
| The two 0.15.0 steps | cases only | `orchestrator-gate-checks-route-back` (new): the route to `technology-bootstrap` as its own entry, nothing launched, 3 of 3 (6 of 7 over every run made: one wrote the route as a bullet). `orchestrator-slice-review-launches` (new): the cold reader named `cold-read` on Opus with no planning document, the mutation report handed to the test-quality reviewer alone, 3 of 3 | references `gate-checks-route-back` and `cold-reader-launch`, each 0 of 3 |
| E2's proposals | Five graders (below); the resume lines and the fixture's handoffs name the step and not the command; two rules dropped ("Keep its agent id", "Read its last line"); the weak `--planning` reference dropped | Each new grader 3 of 3. The deletions the prompts were thought to hide, run again on the reworded cases, and three on the new one: all eight survived (the two `rounds_record.py` commands, the resume rule twice, a gate `FAIL` to one fixer, the gate on fix r1, the re-review, the smoke agent only after smoke findings). The prompts were not what hid them: the run does these with or without the sentence | E2 closes as: every survivor is a new grader, a dropped rule or an accepted gap, these eight among the gaps |
| F1, B1a | `validation_gate.py` reads an absolute `--allow`, `--module-dir`, `--deviation-zone` or `--protect` inside the project as relative (an absolute `--protect` matched no changed file, so a changed document passed); the `nosemgrep` note | `tools/validation_gate_test.py`, 8 tests | the test |
| B4a, B4b | `changed` writes the mutants file for its owner alone; `run --remove-mutants`; under `--allow-dirty` the pass runs in a disposable clone | `tools/mutation_pass_test.py`, 17 tests, among them a run killed between a mutant's write and its restore that leaves the project's tree as it was | the test |
| B5a | `deferrals.py --out` creates its directory | `tools/deferrals_test.py`, 6 tests | the test |
| F3, F4 | the log checker reads an r2 fix of several hashes with spaces between them; `cost_by_role.py` skips a named session with no transcript and ends on `cost $<n>, not covering <id> (no transcript)` | `tools/orchestrator_log_check_test.py` (4 tests, new), `tools/cost_by_role_test.py` (5 tests, new) | the tests |
| The fixture's false comment | "each entry is a hold of its own that takes its own cancel", which the code does | `code-review-comments-chunk`'s `why-comment-is-not-flagged` 3 of 3 (1 of 3 at its bar) | — |
| The fixture's planted repetition | the ISBN's normalisation written out in each of four methods, a line that is reasonable once | `code-review-chunk-gate-covers`' `duplication-left-to-the-gate` reads "repeated" in a title again, 3 of 3 | reference `gate-holds` on the new fixture, 0 of 3 |

**The replay cases are gone.** The rule was to keep them only if G1's
fix, removed, makes one fail. Their frozen histories carried the old
wait rule, which is the fix removed, and both passed every grader at
their bars; no new capture was needed to know.

**Every bar that moved** (`record_thresholds.py --gate-only`, the
twenty three-run cases by name; three runs each).

| Case | Bar before | Now | The graders behind it (passes of three, before→now) |
|---|---|---|---|
| `chunk-runner-one-fix-round` | 0.97 | 1.00 | `hand-back-is-one-line-and-nothing-else` 2→3; `one-last-fix-review-and-no-other` and `no-other-review` new→3; `no-third-review` gone |
| `chunk-runner-gap-handback` | 1.00 | 1.00 | `no-report-opened`, `no-report-opened-through-the-shell` new→3 |
| `chunk-runner-gate-deviation` | 1.00 | 1.00 | `allow-list-not-widened`, `gate-run-with-the-protect-list`, `gate-reads-the-done-when-from-the-report`, `gate-handed-the-builders-agent-id` new→3 |
| `chunk-runner-gate-outside` | 1.00 | 1.00 | `fixer-launched-as-sonnet`, `sandbox-checked-before-the-fixer` new→3 |
| `code-review-comments-chunk` | 0.90 | 0.93 | `why-comment-is-not-flagged` 1→3; `hand-back-is-counts-and-path` 2→1 (replies over its 480 characters) |
| `orchestrator-delivery-foreground` | 0.91 | 0.95 | `cost-script-run` 1→3; `pr-writeup-invoked` 2→3; `body-carries-the-deferrals-section` 3→2; `review-history-asked-before-any-wait` new→2; `no-wait-for-a-bot-that-never-reviewed` new→3 |
| `orchestrator-budget-exceeded` | 0.87 | 1.00 | the judge `flow-ends-saying-what-is-built` (1 of 3) gone; the regex `flow-ends-on-the-clock-and-says-what-is-built` new→3 |

New, each at 1.00: `chunk-runner-fix-gate-fails`,
`chunk-runner-last-fix-review`, `orchestrator-target-from-project`,
`orchestrator-autopilot-counts-over`,
`orchestrator-gate-checks-route-back`,
`orchestrator-slice-review-launches`. Unmoved at 1.00 over three runs:
`chunk-runner-gate-sources`, `-review-round`, `-waits-for-handback`,
`code-review-chunk-gate-covers`, `orchestrator-asks-for-target`,
`-mutation-before-review`, `-issue-fix-records`.

**Read from the first failures.**

- `allow-list-not-widened` knew only literal paths and failed three
  right runs that wrote `--allow "$D/implementation/"`.
- `duplication-left-to-the-gate` read "duplicate" in a title about a
  duplicate position in the queue, twice.
- `flow-ends-on-the-clock-and-says-what-is-built`, written to replace a
  judge that failed a right reply three votes of three, passed 1 of 3
  in its own first form: it did not know "have not been started".
- A regex on a file that was never written throws and voids the run.
  Two references errored on all three runs for that reason, the rule's
  absence being exactly that the file is not written; those checks read
  the write in the trace now.
- `orchestrator-delivery-foreground`: two runs of three read the `gh`
  stand-in's header ("nothing here reaches GitHub"), declined to call
  the slice delivered and stopped before the review and the cost. The
  case's scaffold strips the header's comments.
- Two rules of the new text did not hold and were changed, not
  re-worded a third time. The "say where the target came from" sentence
  held 1 run of 3 as a line of the reply and holds 3 of 3 as a bullet
  on the log entry. A "taken as recommended" bullet for a count over
  held 1 run of 4 while every run went on to the next chunk; with the
  clock as the only cap there is nothing taken to log, and the skill
  now says the C line's budget field is the record.
- A "launch and hand off" case costs what the launched agents cost: the
  harness wakes the session for each one's end and lets them finish.

**What it cost.** From the result files: 286 runs, **$225.78** (the
gate's 208 runs, $144.82; the references' and deletions' 78 runs,
$80.96). The estimate given before the first run was about 325 runs
and $150, or $210 if a defect forced one more pass of the orchestrator
group; after the owner chose the split it was about $120. Fewer runs
than estimated and more money, for these reasons: the new launch cases
are dear (`orchestrator-slice-review-launches` about $12 for three
runs, and its reference as much again); the eleven orchestrator cases
ran a second time after the two rules above changed (about $28); the
references and deletions cost $81 against $34 estimated; and about $19
was the order of work, the `--stale` pass twice re-running the six new
cases once each (a new case with no bar counts as stale, and recording
a bar stales its evidence). Bars are to be recorded before the single
pass, not after it.

**Not held by a case.** The autopilot round (verify, fix, last-fix
review) at any scope; the last-fix review at D and at E; a readiness
correction written without a question; the A.2 autopilot question
itself; the A.5 wiring launch and "after chunk 1" (slice 3's); F6 with
a bot in the repository's history (the wait itself); the mutation
pass's disposable clone inside a real D step (the tool test holds the
script). Without a known-bad reference: `chunk-runner-fix-gate-fails`
and `orchestrator-autopilot-counts-over`, and F6's two graders.

### The screen-change check

`TODO.md`'s PR 3 (2026-11-16, kad 0.16.0, Claude Code 2.1.325, every
case on Sonnet): C1, and cases for three things PR 1 left unheld. 178
cases (170 before): eight new. No cost figure is kept for this change,
by the owner's word.

**What the owner decided on the way** (after the six decisions in
`TODO.md`): the fixture's screen is the holds desk's notice; a state's
name is its mockup's file stem; the comparison runs in CI from a copy of
the plugin's script in the project; one fixer at E writes the capture of
a listed state nothing drives; the threshold lives in
`visual-ux/baselines/screen-check.json`; a workflow in this repository
shows the check with a real browser. Settled without a question: the
check has two red verdicts (`FAIL` for a state not listed, `BASELINES
OWED` for listed ones, which gets no fixer); "listed" is a line the
branch added to a screen design's section; the capture side is a
self-contained `screens/` folder with Playwright 1.64.1 pinned by a
lockfile, so the project's manifest is not touched; the job runs on
`ubuntu-24.04`, not `-latest`; a project with no baseline yet takes
every capture as a first baseline.

**Per item: what was built, its "done when", and what it fails without.**

| Item | Built | "Done when", and the counts | Fails without |
|---|---|---|---|
| C1 the comparison | `skills/orchestrator/scripts/screen_check.py` (`compare`, `adopt`, `states`, `check-section`): an 8-bit PNG reader and pixelmatch's rules in the standard library; more than the owner's 0.1% of a state's pixels, anti-aliased pixels not counted | **On the fixture, a style change meant for one state that moves another is reported, and the intended change is not**: `tools/screen_check_test.py` (27 tests) on images Chromium made, and the `Fixture screens` workflow on every change to the script or the fixture. Planted: `hold-cancelled` STRAY at 0.610% of its pixels (1,235 anti-aliased ones ignored), `hold-not-cancelled` read as listed. Intended: nothing reported, one baseline changed and one new owed | the test |
| C1 the list | `screen-design`'s `## States this slice changes`; the readiness gate's eleventh check (`changed-states-listed`) | `screen-design-payfine`: `changed-states-section-lists-three-states` and `a-listed-state-is-named-as-its-mockup-file` 3 of 3. `tools/readiness_check_test.py` (25 tests, five new) | reference `changed-states-section`: both 0 of 3 |
| C1 the CI job | `ci-pipeline`'s section 3: `screens.yml` on one named image, read-only, the plugin's harness and pinned browser copied, the threshold file | `ci-pipeline-screen-job` (new): 16 graders, 3 of 3 | reference `screen-job`: no workflow, no harness, no copy, no threshold, 0 of 3 |
| C1 the capture of a listed state | the orchestrator's E.2: `screen_check.py states`, then one fixer for `screens/states.mjs` | `orchestrator-capture-states` (new): the script asked, nothing pushed, no capture code written by the orchestrator, the handoff names the fixer and `queue-failure`, 3 of 3 | reference `capture-for-listed-states`: the script not run, the branch pushed, 0 of 3 |
| C1 a stray difference | `delivery`'s "The screens check" and the orchestrator's E.4: the artifact read, the red-CI path, the check not weakened | `delivery-screens-stray` (new): artifact downloaded, `hold-cancelled` in `pr-ci-r1.md`, its images in the records, no baseline staged, copied or pushed, the fixer briefed, 3 of 3 | reference `screens-verdicts` (both skills' text removed): no download and no images 0 of 3, the brief 1 of 3 |
| C1 baselines from the artifact | the same section: `adopt`, one commit of the paths it printed, the push, the watch again | `delivery-screens-owed` (new): the two listed baselines pushed in one commit, `hold-cancelled`'s untouched, no fixer, the checks watched again, the E line green with its baselines, 3 of 3 | the same reference: the commit 0 of 3, the download 1 of 3. `baselines-adopted-by-the-script` is not in it: the project's own copy of the script documents `adopt`, and runs found it |
| The autopilot round | case only | `orchestrator-autopilot-round` (new): from a hand-back with one High standing and the owner's yes, one verify reviewer on Opus with the round's report path and the finding's report, after a sandbox check, no chunk 2, 3 of 3. The verifier reproduced the High in every run read | reference `autopilot-round`: 0 of 3. The state's `autopilot.md` says yes and names no stop, so the skill's account is the only one |
| The last-fix review at D | case only | `orchestrator-last-fix-review-at-d` (new): after D's second fix, exactly one launch, a code reviewer on Opus on that fix's range, 3 of 3 | reference `last-fix-review-at-d`: 0 of 3 |
| The autopilot question | one sentence in A.2: a session with no question tool asks in plain text and ends its turn | `orchestrator-autopilot-question` (new): asked once, nothing written, no branch, nothing launched, 3 of 3. `orchestrator-autopilot-recorded` (new): the answer in the owner's message, the file written with their words, the stops and the always-asked, the A line naming it, 3 of 3. Two cases because a run cannot be answered | reference `autopilot-question` on each: the question 0 of 3 (three clean runs over two passes; the others ran out of time building the slice nobody was asked about); the file's content 0 of 3, though a file is still written from the owner's "yes to autopilot" |

**What a case shows, what only a tool test shows, what only a real CI
run with a real browser shows.**

| Shown by | What |
|---|---|
| A case | What the model does around the check: writes the list, writes the job and copies the harness, asks the script which states nothing drives, reads the verdict from the artifact before thinking of a fixer, commits only what `adopt` printed, never touches a baseline while a finding stands, briefs the fixer not to weaken the check. The `gh` stand-in gives the artifact: the fixture's real captures, and the report `screen_check.py` really writes from them when the state is built |
| A tool test only | That the comparison is right: the PNG reader against each row filter and colour type, the threshold at exactly 0.1% and one pixel over, anti-aliased edges, two sizes, each status and verdict, "listed" as a line the branch added, `adopt` refusing a stray state or an artifact from other code, the readiness check. No case can show a pixel count |
| A real CI run only | That a real page renders the same twice in the fixed environment, that the pinned Playwright installs and its Chromium starts, that the harness drives a state and the workflow's steps work together. `Fixture screens` (Ubuntu 24.04) shows it for the fixture: the desk captured within the threshold of its committed baselines, then the two changes judged. For a real project the first run is the first project's baselines from `main`. Not shown anywhere yet: `gh run download` against GitHub, the adoption commit on a real pull request, a capture written by the E.2 fixer |

**Read from the first failures.**

- With no question tool the orchestrator did not ask the autopilot
  question: it wrote "I couldn't ask", assumed no, and built on. The
  skill had no sentence for it. It has one now, and that run is what
  the reference reproduces.
- `ci-pipeline` left the screen job out four runs of four once the
  fixture stopped contradicting itself by accident ("nothing to capture
  yet; it would fail on every pull request"). An "only when" at the top
  of the section read as leave to judge. The decision moved into section
  1, as a fact read from the project, with the first state named as the
  ordinary one: 3 of 3 since.
- The fixture said two things: a screen design in `visual-ux/` and a
  slice file whose accessibility line said "this slice has no screen".
  Three runs believed the slice file. The states with a screen rewrite
  the line.
- Four graders of mine knew only `Write` when the runs used a heredoc,
  and one knew only a literal hash when two right runs wrote `@$UA`. The
  workflow's content is read from the command or the Write that made it.
- The stand-in answered `run view` with the failing log and `run list`
  with one run after the baselines push, beside a green `pr checks`. The
  run refused to call that green, which was right.
- Two references named a grader that does not depend on the text
  removed (above); the lists were corrected, not the cases.

**Every bar that moved** (`record_thresholds.py --gate-only`, twelve
cases by name, three runs each).

| Case | Bar before | Now | The grader behind it (passes of three, before→now) |
|---|---|---|---|
| `orchestrator-readiness-open-item` | 1.00 | 0.94 | the judge `puts-the-blocker-to-the-owner` 3→2 |
| `orchestrator-readiness-gate` | 0.96 | 0.93 | the judge `backward-routes-name-the-checks` 2→1 |

Both are the prompt's change, below, measured again: each prompt now
answers the autopilot question (and the gate case the browser one).
`orchestrator-readiness-sources`, changed the same way, stays at 1.00.
New, each at 1.00 over three runs: the eight cases above.
`screen-design-payfine` stays at 1.00 with its two new graders at 3 of 3.

**How it was gated, and the gate's own change.** The nine cases above
ran three times. Under the rule as it stood, 62 more were stale and owed
one run each; the owner asked whether they had anything to do with the
change, and 46 did not. The three rules under "Eval gate" (the state a
case is built from, the scripts it ran, the orchestrator's steps it
reaches) were built in this pull request and bring the list to 25: the
nine, and 16 that ran once against the bar they had (below). What the
third rule gives up is said there.

**The cases that ran once** (16, against the bar they had): 13 at or
above it on the one run (`ci-pipeline-os-matrix`,
`delivery-ci-red-not-done`, `orchestrator-delivery-foreground` at 0.92
against 0.95, inside the tolerance, `-delivery-removal`,
`-gate-checks-route-back`, `-issue-fix-records`, `-route-accessibility`,
`-route-implementation`, `-route-implementation-prenamed`,
`-route-open-pr`, `-route-screen-design`,
`-route-slicer-accessibility-mistake`, `screen-design-owner-sheet`).
Three fell under their bar and were re-run at three:
`orchestrator-readiness-gate`, `-readiness-open-item` and
`-readiness-sources`. All three start at the A step with the autopilot
question unanswered, and the orchestrator now asks it in plain text and
ends its turn before the readiness gate they grade. That is the new
sentence at work, on the cases it was said beforehand would be exposed
to it; their prompts now carry the owner's answer, they ran three times
and their bars were recorded again (above). Six of the nine new cases
ran once more as well, their state or the scheme having moved after
their three runs; all at 1.00.

**Not held by a case.** The gate-checks wiring launch and "after chunk
1"; the last-fix review at E; F6 with a bot in the repository's history;
a readiness correction written without a question (PR 2); the second
autopilot round, its fix and its last-fix review (the case stops at the
verify launch); a state owed twice running reported as unstable; the
E.2 fixer's launch itself (the case hands off before it); `adopt`
through a real `gh`. Without a known-bad reference: nothing new.
`tools/fixture_screens.sh` is run by CI only. `verify.sh` fails on an
overlay this change did not touch (`monthly-statement`'s test imports
with a `.ts` extension, which the TypeScript 5 it installs refuses).

### Why fixers regress

`TODO.md`'s H1 (2026-11-16; no eval run). One in four actionable findings
has been a regression a fixer introduced (incident 19). Every row the
four sidecars of the first project class `regression` was read against
its entry in the re-review's report, the fix commit and the batch the
fixer was handed, and, where the audit kept one, the fixer's transcript:
116 rows (slice 1: 47, slice 2's two passes: 50, the two issue fixes: 11
and 8), 83 of them Critical, High, Medium or `needs-decision` and 33
Low. About 107 distinct defects: at the slice review several reviewers
report the same one. Counts and causes only; nothing of the project is
quoted.

**How each was sorted** (the owner's choice of the six-way sort,
2026-11-16): one primary cause per row, tried in this order. Three
readers did the sorting, one per sidecar group, each marking its
confidence: 54 rows high, 53 medium, 9 low. The low and medium ones are
mostly a choice between the last two causes.

| Cause, in the order tried | Actionable (of 83) | Low (of 33) | What it looks like |
|---|---|---|---|
| 1 Not a regression: the problem was there before the fix | 8 | 9 | A line the fix only moved in a file split; a round-0 Low never handed to the fixer; a reviewer (the smoke or the stranger run) that first looked at round 1; a criterion written between the rounds. The sidecar classes by "the fix touched the line" |
| 2 Finding misread: the fix did something other than what was asked | 2 | 0 | One defect seen by two reviewers |
| 3 The fix grew past its finding | 2 | 0 | Both in a second commit written to satisfy the coverage gate |
| 4 A neighbour left inconsistent: the asked change made, and a test, caller, name or comment that depended on the old behaviour left as it was | 11 | 3 | 8 of the 14 are names, 6 of those a test whose body the fix changed under a title that could not change |
| 5 The fix's own new code is defective: the right place, as asked, and what it added has a defect of its own | 58 | 21 | Of the 58: 26 in tests the fix added or rewrote (a test that cannot fail or asserts less than its name, a new branch nothing tests, an assertion lost in a rewrite), 24 in source, 7 names or comments, 1 a style rule |
| Unclear | 2 | 0 | The fix needed a rule no planning document held |

**What the transcripts say about "not read".** A fixer's transcript was
kept for 69 of the 116 rows (none for slice 1). In 66 of them the fixer
had read the file the regression sits in before it committed; the three
exceptions are documents the fix never touched. No row is a fixer that
did not look. In 8 of slice 2's 10 rows of cause 4 the fixer had opened
the inconsistent test or caller and edited around it: `TODO.md`'s
"a neighbouring test or caller not read" is not what happens.

**Batch size is not a cause that shows.** Regression rows per finding
handed to the fixer, by the size of the batch:

| Batch (actionable findings handed) | Batches | Findings handed | Regression rows | Actionable rows of causes 2 to 5 |
|---|---|---|---|---|
| 4 to 8 (a chunk's round, a pull request's triage) | 24 | 139 | 54 (0.39 a finding) | 52 (0.37) |
| 14 to 30 (a slice review's round) | 5 | 108 | 56 (0.52) | 17 (0.16) |

The slice-review batches raise more rows a finding and fewer that are a
fixer's own serious defect: their rows run to Lows, to duplicates across
six reviewers and to cause 1, and those fixes are also the large
restructurings, so size and kind of work cannot be told apart. One more
batch, a browser review of one finding and three decisions to build, gave
6 rows. "A batch too large for one fixer" is not supported by these
numbers; "a fix that restructures" may be, and no row count separates
it.

**One pattern the six causes do not name**, seen by all three readers:
**the fixer did what the finding's suggested fix said, nearly word for
word, and the re-review then found fault with exactly that** (a
suggested signature with a parameter nobody uses, a suggested removal
that bypasses an existing routine, a mechanism too weak for its job, a
fix at a layer no real client reaches). At least 21 rows by the readers'
notes (6 in slice 1, 10 in slice 2, 5 in the issue fixes), filed mostly
under cause 5; it was not sorted row by row, so 21 is a floor. The
origin is the round-0 report, not the fixer's care.

**One proposed change per cause with six or more actionable rows**,
each with the file group it would send through the gate. None is built
here.

| Cause | Rows | Proposed change | File group, and its cases today |
|---|---|---|---|
| 5 The fix's own new code | 58 (26 in its tests) | A handed-back fix shows each test it adds or rewrites failing: break the line the fix wrote, see that test fail, restore; the `Fix` line names the test and the break. Today the contract asks for one break per fix, in the place the slice's main rule lives. And a rewritten test keeps every assertion it had, or its `Fix` line names the one dropped and why | `skills/tdd-implementation-lite` (its handed-back path), 17 cases |
| 5, the suggested fix followed to the letter | at least 21 | In the same edit: a finding's suggested fix is the reviewer's guess at a mechanism, and the finding is its "What's happening". A fixer that sees the suggestion add something nothing uses, go round an existing routine or sit at the wrong layer fixes what the finding describes and says on the `Fix` line where it left the suggestion | the same group, the same gated change |
| 4 A neighbour left inconsistent | 11 (6 a test's title) | A test whose behaviour a fix changes is renamed to say what it now checks, the rename on the `Fix` line (`renamed <old> → <new>`), and the gate's `tests` check reads that line, so a plan's test name is no longer frozen for a fix. Today a renamed plan test fails the gate, and fixers were briefed to leave the names alone | `skills/tdd-implementation-lite` and `skills/orchestrator/scripts/validation_gate.py` (the cases that ran it) |
| 1 Not a regression | 8 (17 with the Lows) | `rounds_record.py` classes a round-1 finding as a regression only when the fix wrote the line's content: a line it moved (the same text in the parent commit, found with move detection) is `pre-existing`, and a report from a reviewer with no round-0 report in the scope is `first-seen`. Incident 19's one in four is then measured on what fixers did | `skills/orchestrator/scripts/rounds_record.py`, 15 cases |

Causes 2 and 3 have two rows each and get no change. Whether the light
cadence (a fix by the chunk's own builder) lowers cause 5 is still the
experiment it was; nothing here predicts it, since the fixers did read
the code.

### The final list

`TODO.md`'s final pull request (#66, 2026-11-16, kad 0.16.1, Claude Code
2.1.325; runner cases on Opus, the rest on Sonnet): PR 2 (B7 to B10, C3,
the readiness-correction case), every item PR 1 and PR 3 left open, and
H1, whose table is the section above. 180 cases (178 before): two new;
graders added to twelve and cut from four. No cost figure is kept, by
the owner's word.

**What the owner decided on the way** (one question at a time): H1's
six-way sort and six rows as "more than a handful"; on a sound module a
Low or a missing-case note passes and anything Medium on the sound code
fails; the hand-on line is graded on one existing case per review skill,
on problems the fixture already holds; C3's case plants a lock file with
a process number, in one turn. And, when the list was nearly done: close
every loose end, which turned three things recorded as accepted into
fixes (the last three rows of the table).

**Per item: what was built, its "done when", and what it fails without.**

| Item | Built | "Done when", and the counts (three runs) | Fails without |
|---|---|---|---|
| B7 nothing above Low on a sound module | "Above Low needs a cost you can point to today" in `code-review`, `architecture-review` and `reliability-review`, each with what a preference looks like in its subject; in `test-quality-review`, a sound exact-value test is under no category, a thin one's finding is the missing case (Medium at most), and one method of the designated fake set for one test is not a finding | `code-review-catalog` 3 of 3 (2 of 3 at its bar), `library-app-catalog-review` 3 of 3 (2 of 3), `security-review-catalog` 3 of 3, `reliability-review-catalog` 3 of 3 once the rule was in that skill too: it went 2 of 3 twice running without it, and its history (4 of 8 on 2026-11-11) says its bar of 1.00 was luck. `test-quality-review-fines`: `no-false-alarm-exact-tests` 3 of 3 (1 of 3), `no-false-alarm-fake-ledger` 3 of 3 (2 of 3) | the bars before, which are the same cases on the text without the rule. No reference was run: a grader at 2 of 3 without the rule passes a three-run reference one time in three |
| B8 a serious problem that is another review's | `## A serious problem that is another review's` in the six review skills: one line under `## Handed on`, above the findings (what, where, the severity it appears to have, the owner), never rated down, never a finding. `code-review`'s mocking rule is this rule | A grader pair per skill on a problem the fixture holds (answer key, `H1` to `H6`): the line, and no finding's heading about it. Line 3 of 3 on all seven cases (`code-review-fine-notices-pr` and its twin, `test-quality-review-fines`, `library-app-structure-review`, `security-review-config`, `reliability-review-http`, `accessibility-review-payfine`). The mocking judge 3 of 3 on the direct case (1 of 3) and on the twin (0 of 3) | reference `handed-on` on each of the six: the line 0 of 3, six times. Without the rule `code-review` again made the mock a ranked finding (the judge 0 of 3) |
| B9 `map-update`'s changes section | the script half (`extract_map.py` reads a bare cell and names a row it cannot read); the skill says both | `pre-existing-flags-not-new` 3 of 3 (0 of 3), 4 of 4 over every run made. `tools/extract_map_test.py`, 9 tests | the bar before; the test |
| B10 the twins | the four `-via-agent` twins lose the eleven judges their direct cases lost in E7; `library-app-lending-review-via-agent` has the ORM wording | each twin 3 of 3 on what is left; the ORM judge 3 of 3 (2 of 3) | — |
| B10 the overlay with no case | deleted, with its four rows of the answer key | `verify.sh` passes | — |
| B10 the owner-sheet cases | `Bash` granted; a check that the export is not opened with `Read`, `Grep` or a command that prints it | `requirements-refinement-owner-sheet` 9 runs of 9 clean, `screen-design-` 6 of 6, `architecture-design-` 6 of 7 (one `Read` of the first line, which the skill allows only with no shell), `vertical-slicing-` 8 of 9: one run ran `head -5` on the export in its first command, before the skill was loaded, and cells reached the session. So the shell made one case worse once, and no text in a skill's body is read before that command. Fixed where it can be: see the last row | — |
| B10 `code-review` not invoked | read from 21 traces: the review written without the skill starts with `Read`, `Read`, `Glob` on a plain "review it before I merge". The description now leads with that request | `code-review-days-left-pr` `skill-invoked-display` 3 of 3, 4 of 4 over every run (1 of 3 at its bar, 8 of 13 not invoked before). The negative-trigger cases still hold | the bar before |
| B10 `map-update`'s untiered module | read from traces: every run patched the map by hand after the script (a `sed` or a small program) to set the new module's tier and move its edge, and one in three did not. `extract_map.py --tier <path>=<n>` puts the tier on the row and the edge in the right list, and its last line names new modules it left untiered | `new-rows-extracted` and `flags-new-wrong-direction-edge` 3 of 3 (2 of 3 each); the case 1.00 (0.81). Four tests | the bars before; the tests |
| B10 `test-quality-review` on the designated fake | with B7 | above | above |
| C3 the concurrency pass | `architecture-design`'s "Two things at once": a decision about keeping two things apart is put with its interleavings listed and answered (two starts at once, a crash at each step, a stop during each wait, a leftover removed by hand, a reused process number), before approval | `architecture-design-concurrency-interleavings` (new, capability; the planning set `nightly-single-run`, the engineer's lock file with a process number): the decision put with a table of interleavings answered for the proposal and for the recommendation, both holes of the proposal named, nothing written: 9 graders, 3 of 3, 5 of 5 over every run | reference `interleavings`: `stop-during-a-wait-answered` 0 of 3, `reused-process-number-named` 2 of 3, the rest 3 of 3. Without the section the model still walks most of them: the rule's measurable share is the stop during a wait |
| The readiness correction under autopilot | case only | `orchestrator-readiness-correction-autopilot` (new, regression): the design holds its `Kept for later slices` content under another heading; the route to `architecture-design` inline, the correction written with no question, the gate passed on its second run, the A line `PASS after kept-for-later-slices`: 3 of 3 at its bar. Over the 12 runs made: the A line 12 of 12, the approved text under the heading left as it was 9 of 12 (three runs reworded it while "changing no decision") | nothing: with the autopilot text of A.4 removed the run did the same, 3 of 3. No reference is kept. The skill's bullet `taken as recommended: <check> (autopilot)` was not written on the first run; the grader reads the route's own entry |
| Added on "close every loose end": `requirements-refinement`'s first turn | the skill holds each question against what was read before it goes out, and "I couldn't tell from the code" means look once more | `does-not-ask-what-the-sources-answer` 3 of 3 (2 of 3) | the bar before |
| The same: the owner's file opened before the skill is read | the descriptions of `vertical-slicing` and `requirements-refinement` say to invoke the skill before opening a file the owner points at | `vertical-slicing-owner-sheet` 3 of 3 after it, no cell in the session. `architecture-design` and `screen-design` do not carry the sentence: their runs with a shell were clean of it | — |
| The same: the external review of #65 | one comment (a `nosemgrep` note on `screen_check.py`'s `git` call, an argument list with no shell), first declined for its eleven stale cases, then applied | the eleven cases at one run | — |

**The loose ends of PR 1 and PR 3, each closed how.**

| Loose end | How |
|---|---|
| F2 has no case that fails without its text | Closed with a reference that removes every place the rule stands, step 2's "a `FAIL` goes to one fixer" among them, as the rule for references asks: `gate-fixer` on `chunk-runner-fix-gate-fails`, `the-gates-one-fixer` and six more graders 0 of 3. The run that left a regression as "no third fixer" was tried once more on `chunk-runner-one-fix-round` with the same removal and did not reproduce (the regression still got its `Fix r2`, 3 of 3): that sentence is an accepted gap |
| `chunk-runner-fix-gate-fails` has no reference | It has `gate-fixer` now |
| `orchestrator-autopilot-counts-over` has no reference | Still none, for another reason than was thought. The state now carries the owner's short answer (yes, no stop spelled out), so the fixture no longer states the rule; with the skill's three sentences on the counts removed the run still launched chunk 2, 3 of 3. The orchestrator does not end a flow on a per-chunk count with or without the sentence. Accepted gap |
| `baselines-adopted-by-the-script`, `autopilot-file-written` do not fail without their text | Accepted, and not gaps in what the cases hold: each sits beside a grader that does fail on the same reference (the adoption commit 0 of 3; the file's content 0 of 3). The project's copy of the script documents `adopt`, and a file is written from the owner's own "yes" |
| The slice-review state has no gate output | `slice-review-r0` runs the gate on D's own two commits and its handoff names the file. The planted commit gained one test that runs the length rule far from its limit: without it the gate failed on changed-line coverage, which is what a real gate would have done to that commit; the survivor (`>` to `>=`) is unchanged. `orchestrator-slice-review-launches` 3 of 3 |
| `verify.sh` fails on an overlay | Two causes: the slice-size overlay's test imported with a `.ts` extension, and two delta snapshots added since (`chunk1-r2-fixed`, `slice-unguarded`) were checked without the snapshot they sit on. It passes |
| `loop_states_before.json` | Deleted with its readers |
| The external reviewer never read #65 | It had, on 2026-11-16, with one comment nobody answered. Answered, then applied (above) |
| The steps rule is a bet | Unchanged, and no miss turned up in a case that was not run |

**Read from the first failures.**

- The security case's hand-on check wanted the migration and failed a
  run that handed on the image build that ignores the lockfile and the
  tag-pinned action, which are as much another review's. It reads any
  of the three. The migration itself was handed on in 3 runs of 4.
- Three "not a ranked finding" checks read a word in a heading: a
  finding that the app and the migration share a database user, and one
  that configuration is read in several places, are those reviews' own.
- The owner-file check failed a `sed -i` on `sources.md` whose text
  names the export.
- `chunk-two-runner-launched` allowed one launch; a run the harness kept
  waking went through chunk 2's whole round and relaunched its runner
  at the fix, which is the loop working.
- The first B7 text for `reliability-review` made one run of three rate
  the unbounded loan history Low ("one member's history is small"). It
  now says it lowers nothing the skill names as a finding whatever the
  load; 3 of 3 since.
- A state of the loop fixture contradicted the gate: a commit planted
  to be unguarded could not have passed a gate with changed-line
  coverage. Found by building the state, not by a run.

**Every bar that moved** (`record_thresholds.py --gate-only`, 26 cases
by name, three runs each; passes of three, before→now).

| Case | Bar before | Now | The graders behind it |
|---|---|---|---|
| `code-review-catalog` | 0.94 | 1.00 | `nothing-above-low` 2→3 |
| `library-app-catalog-review` | 0.93 | 1.00 | `reports-nothing-above-low` 2→3 |
| `test-quality-review-fines` | 0.88 | 1.00 | `no-false-alarm-exact-tests` 1→3; `no-false-alarm-fake-ledger` 2→3; two new at 3 |
| `code-review-fine-notices-pr` | 0.89 | 1.00 | `leaves-mocking-to-test-quality-review` 1→3; `consults-why-comments` 2→3; two new at 3 |
| `code-review-fine-notices-pr-via-agent` | 0.92 | 0.97 | `leaves-mocking-to-test-quality-review` 0→3; `consults-why-comments` 3→2; three judges cut; two new at 3 |
| `code-review-days-left-pr` | 0.92 | 1.00 | `skill-invoked-display` 1→3 |
| `map-update-cancel-hold` | 0.81 | 1.00 | `pre-existing-flags-not-new` 0→3; `new-rows-extracted` 2→3; `flags-new-wrong-direction-edge` 2→3 |
| `library-app-lending-review-via-agent` | 0.96 | 1.00 | `finds-orm-inside-checkout-use-case` 2→3; two judges cut |
| `test-quality-review-survivors-at-d` | 0.95 | 1.00 | `equivalent-survivor-is-no-finding` 2→3 |
| `requirements-refinement-payfine-phase1` | 0.92 | 1.00 | `does-not-ask-what-the-sources-answer` 2→3 |
| `architecture-design-owner-sheet` | 1.00 | 0.92 | the judge `fixtures-are-invented` 3→2 (a split vote on a reply that says it, as in E7); the new check at 3 |

New, each at 1.00: `architecture-design-concurrency-interleavings`,
`orchestrator-readiness-correction-autopilot`. Recorded again at 1.00
with graders added or cut: `library-app-structure-review`,
`security-review-config`, `reliability-review-http`,
`accessibility-review-payfine`, `reliability-review-nightly-via-agent`,
`supply-chain-review-build-via-agent`, `screen-design-owner-sheet`,
`vertical-slicing-owner-sheet`, `requirements-refinement-owner-sheet`.
Unmoved at 1.00 over three runs: `reliability-review-catalog`,
`security-review-catalog`, `orchestrator-slice-review-launches`,
`orchestrator-autopilot-counts-over`.

**How it was gated.** 112 cases are reached by the change. 26 ran three
times and had their bars recorded by name before any single pass. 76 ran
once against the bar they had, in two passes (the second after the
three late fixes), all at or above it; the gate re-ran five of them at
three for a first run under the bar and all five passed
(`chunk-runner-last-fix-review`, `security-review-deferrals-not-restated`,
`test-quality-review-seam-fake`, `ci-pipeline-screen-job`,
`orchestrator-readiness-open-item`), each on a grader its bar already
records as missing one run in three or on a hand-back over its length,
read. Fifteen of the 76 are negative-trigger cases that only a
description can reach, and three descriptions changed. The last ten
needed no run: their state's entry changed with the hasher and their
state did not. 246 gate runs, the wording trials and the re-runs after
each grader fix among them, and 33 reference runs. Two frozen histories
were frozen again (`architecture-design-payfine-phase2`,
`requirements-refinement-payfine-phase2`).

**Still not held by a case.**

- Nothing in the loop acts on a `## Handed on` line: it is for the
  report's reader, and at D all six reviews run anyway. Whether a
  chunk's combined reviewer writes one for a problem none of its three
  lenses owns has no case.
- The hand-on line is graded where the fixture has a problem to hand
  on; that a review with nothing serious in sight leaves the section
  out is seen in the clean-module runs and graded by no check.
- B7's rule on real code: the cases are one clean module and one test
  file. Slice 3's slice review is the first real measure, against the
  findings per chunk of the runs before.
- `architecture-design-concurrency-interleavings` grades the reply, not
  the design document that follows approval.
- A readiness correction that changes no decision is written without a
  question with or without the skill's text, and 3 runs of 12 reworded
  approved text while doing it.
- `orchestrator-autopilot-counts-over` and F2's "no third fixer"
  sentence have no reference (above).
- Carried from PR 1 and PR 3 unchanged: the gate-checks wiring launch
  and "after chunk 1"; the last-fix review at E; F6 with a bot in the
  repository's history; the second autopilot round with its fix; a
  state owed twice running; the E.2 fixer's launch; `adopt` through a
  real `gh`.
- H1's four proposed changes are proposals.

### Loop time

`TODO.md`'s 0.17.0 list (2026-11-18, kad 0.17.0, Claude Code 2.1.327;
runner cases on Opus, the rest on Sonnet): groups A to D after slice 3,
whose run time and stops, not its code, were the finding. 190 cases (180
before): ten new, all tool-judged. Groups A's scripts are held by the
script tests; this section is the model's half.

**The gate, one pass.** 38 cases at three runs (the ten new cases, seven
changed in purpose, the eight whose frozen history was captured again,
and every case of `chunk-runner` and `tdd-implementation-lite`, whose
text the change rewrote most), the 37 known-bad references at three
runs, and the other 74 affected cases at one run each, eight of which
landed under their bar on that run and were run again at three. 360
runs, $228.36 by the result files ($127.00 the cases, $101.36 the
references). Bars were recorded for the 38 by name.

**Bars that moved.** New at 1.00: `chunk-runner-check-fail-second-fixer`,
`chunk-runner-suite-fail-ends`, `chunk-runner-light-no-review`,
`cold-read-refusal-no-exit`, `reliability-requirements-refusal-phase1`
and `-phase2`, `reliability-review-criterion-no-exit`,
`tdd-implementation-lite-checks-before-commit`; new at 0.97
`tdd-implementation-lite-fix-test-renamed` (one run of three saw the
rewritten test fail through a `grep` that kept the assertion and
dropped the runner's `fail` count, which is what the grader reads; the
grader was left as it is); new at 0.93
`orchestrator-recommended-not-asked` (below). Up:
`architecture-design-payfine-phase2` 0.93 to 0.97 (its noisiest judge
is a tool check now), `orchestrator-delivery-foreground` 0.95 to 1.00,
`reliability-requirements-payfine-phase2-stop` 0.92 to
1.00, `technology-bootstrap-phase3-reject` 0.95 to 1.00. Down, each on a
judge or a report's wording and none on the rule the case is for:
`reliability-requirements-payfine-phase3` 1.00 to 0.96
(`decisions-all-approved`, a judge on an 11,000-character file),
`tdd-implementation-lite-chunk-plan` 1.00 to 0.96 (its one judge failed
a right plan: 8 FAIL votes of 9 on the first pass, 15 PASS of 15 voted
again on the same three plans), `tdd-implementation-lite-rename-fix`
0.98 to 0.95 (two reports of three gave the rename as a sentence and a
file list, not the `renamed <old> → <new>, <n> sites` line),
`tdd-implementation-lite-cancel-hold-via-agent` 0.89 to 0.87.

**Per rule: the case, and what three runs showed.**

| Rule | Case | Three runs | Fails without |
|---|---|---|---|
| B1 the gate's checks run before the commit | `tdd-implementation-lite-checks-before-commit` (new) | 3 of 3, and 3 of 3 again: the count the change leaves over its baseline is seen by `--checks-only` and cleared before the commit | `checks-before-commit`: no checks run, the commit made, the helper left exported, 0 of 3 each |
| B2, B4 a rewritten test shown failing, and renamed | `tdd-implementation-lite-fix-test-renamed` (new) | the declaration and the rename 3 of 3; the failing run read by the grader 2 of 3 (the third was seen failing through a `grep`) | — |
| C1 the mutation pass beside the reviewers | `orchestrator-mutation-before-review`, `orchestrator-slice-review-launches` | the pass started in the background, bounded, logged, on the loop's tree, before any reviewer: 3 of 3; five launched at once and the test-quality reviewer after the pass exits, alone handed its report: 3 of 3 | `mutation-before-reviewers`: 0 of 3 on four graders |
| C2 a second gate fixer for a mechanical failure only | `chunk-runner-check-fail-second-fixer`, `chunk-runner-suite-fail-ends` (new) | 3 of 3 each | `gate-fixer` on `chunk-runner-fix-gate-fails`: 0 of 3 on seven graders |
| C3 `light` without the per-chunk smoke run | `chunk-runner-light-no-review` (new) | 3 of 3 | — |
| C4 recommended questions are taken | `orchestrator-recommended-not-asked` (new) | the design saved with no approval turn and the readiness check run: 3 of 3; the log's `taken as recommended: <choice>, over <alternatives> (<skill>)` bullet 1 of 3 (one run gave six decisions one bullet with no alternatives, one listed them in its reply alone) | — |
| C6 the log's last lines are pushed | `orchestrator-delivery-foreground` | 3 of 3: the E line is in the pushed log and the tree is clean | — |
| D1 a refusal says whether it can be permanent | `reliability-requirements-refusal-phase1`, `-phase2` (new) | 3 of 3 each | — |
| D2 every action left after a refusal is run | `cold-read-refusal-no-exit` (new) | 3 of 3 | — |
| D3 a criterion that leaves no exit | `reliability-review-criterion-no-exit` (new) | 3 of 3 | — |
| D4 the planning skills run their own readiness checks | `reliability-requirements-refusal-phase2`, `orchestrator-recommended-not-asked` | 3 of 3 each | — |

**What the first failures changed.** Every case under its bar was read
in its traces before anything was run again. No skill's wording changed
at the gate.

| Case | What the traces showed | Changed |
|---|---|---|
| `orchestrator-mutation-before-review` (0.50, 3 of 3) | the prompt's hand-off point, "when the next thing is launching round 0", includes the pass since C1: the runs stopped before it | the prompt: once the pass is started, no reviewer launched |
| `orchestrator-recommended-not-asked` (0.56, 3 of 3; then 0.85) | the shared slice describes a screen and has no accessibility line, which the skill sends back to the slicer; with that fixed, two runs stopped on questions that are the owner's (a leak in older code, a double charge left possible) | the case scaffolds an API-only slice; the request answers the two |
| `orchestrator-slice-review-launches` (0.79) | the right agents in the right order; two runs named the reports `slice-r0-security-review.md`, and the skill says `slice-r0-<reviewer>.md` | the graders read both names |
| `tdd-implementation-lite-checks-before-commit` (0.87, at its second pass) | the checks passed before the commit; the run piped the script through `grep`, so `checks: PASS` opened the output and followed no line break | the two graders read the line after a quote too; the reference's three runs still fail them |
| `orchestrator-issue-fix-records` (0.88) | C9 at work: the fixture's CI runs `npx audit-ci`, `gate-checks.json` does not, and two runs of four launched the A step's fixer to add it, which `nothing-launched` and the judge counted as a builder | the grader does not count a launch that names `gate-checks.json`, the judge says so too. The three runs after made no launch, so the new form passed without being exercised |
| `tdd-implementation-lite-chunk-plan` (0.88) | judge noise, above | nothing; 0.96 on the next three |

**The references.** 31 of 37 failed as recorded. `gate-fixer`: the
re-anchored deletion left "Any other `FAIL`" with nothing after it, and
the sources rule's "that one fixer" still implied one; it leaves "ends
the round" now. `handback-template`: with the runner's template gone,
two runs of three opened the orchestrator's skill and copied its C line
template; the reference removes that too. `screens-verdicts` on
`delivery-screens-stray` no longer lists the hand-off's brief, which the
red-check rule states as well. `mutation-before-reviewers` had run on
the old prompt, and `gate-checks-route-back` lost two runs to an
authentication error. Those four run again: 0 of 3 on every grader they
list. `deferrals-by-script` failed its grader 3 of 3 and was not counted
only because the bar then recorded that grader under 1.

**The external review** (14 comments on the code alone, 266,000
characters). Seven fixed: `mutation_pass.py` ends the suite's process
group when the pass is interrupted and sends the second signal to a
group whose leader left on the first, and counts only
`screens/capture.mjs` and `screens/states.mjs` as outside the suite;
`audit_sync.py` reads a token whose payload cannot be parsed as live; a
trial's results are named `trial-`, so one can never be read as a bar;
`orchestrator_log_check.py` adds `first <n>` to the split and holds
`review none` or `smoke none` against an A line that says `loop`. Three
deferred to the next change of their script, for the cases they would
stale (`screen_check.py`, 13 through `readiness_check.py`'s import;
`validation_gate.py`, 20). Four declined, the reasons on the pull
request. The eight cases the two changed scripts reach ran once more at
their bars: 12 runs, $13.95, which makes the pull request's total 372
runs and $242.31.

**Seen and not fixed.**

- C4's log bullet, one run of three in the form the skill gives. The
  fix is wording in the orchestrator, which reaches every orchestrator
  case and four frozen histories: the owner's to weigh.
- `tdd-implementation-lite-rename-fix`'s report line, above.
- `orchestrator-issue-fix-records`: one run of four ran
  `tools/gh issue create --help`, which the stand-in logs as a second
  issue filed.
- `technology-bootstrap-phase2` keeps two judges that have each failed a
  right reply once; both passed here.
- `delivery-ci-red-not-done`'s canned CI log does not match its tree
  (passed its one run).
- C9 (every command CI runs is a gate check) has no case of its own; it
  showed in `orchestrator-issue-fix-records` by accident.

### The instruments after slice 4

Eight script fixes from the review of the first project's slice 4
(2026-11-18, `TODO.md` part 1a), no skill text: `rounds_record.py` (a
line past the end of its file is classed by the file; `--resolve` marks
a round's findings fixed or declined), `validation_gate.py` (the
shell-edit count is the agent's own commits and leaves out a refused
write; a failing suite's line names its tests; the two items deferred
from #67), `screen_check.py` (two sizes compared over what they share;
`not captured`; the patch deferred from #67), `cost_by_role.py`,
`orchestrator_log_check.py`. Each has script tests on a synthetic
fixture of the shape the slice produced.

The gate, 2026-11-18: 42 cases the three scripts reach, one run each;
four dipped on their run and passed at three (`delivery-screens-stray`,
`orchestrator-autopilot-recorded`, `orchestrator-readiness-open-item`,
`orchestrator-slice-review-launches`); `orchestrator-definition-of-done`
errored in the harness (its run directory could not be listed) and
passed on the next pass. 65 runs, $51.93 by the result files. No bar
moved.

The external review of #68 (11 comments): three fixed (`capture.mjs`
removes an earlier run's `capture-errors.json`, so a capture that
succeeds into a folder a failed run left is not read as failed; two
tests that could not tell a wrong rule apart), three deferred
(`TODO.md`), four declined with the reason on the pull request, one
answered by the later push. The five cases `capture.mjs` reaches ran
once more (two by its file, three through the delivery states it is
part of, which the loop states manifest showed only after the push):
5 runs, $1.71; 70 runs and $53.64 in all.

One grader changed. `reliability-requirements-refusal-phase2`'s
`own-two-checks-pass-in-the-last-run` wanted a line break before the
first `PASS` line; four runs of four piped the script through `grep`,
so the line opened the output and the grader failed a run that had done
the right thing. It now takes a line break or the opening quote (the
same lesson as 0.17.0's: a pattern on a script's output must let the
line open the output). At three runs after the change: 0.89, two runs
whole and one that did not run the script at all.

Seen and not fixed: in that one run of eight the model looked for
`readiness_check.py` in the installed plugin's cache, was refused by
the eval's sandbox, wrote the document, and said plainly that its two
checks were unconfirmed. The skill gives the path from its own
directory and seven runs used it. The bar stays at 1.00: the miss is
the behaviour the case exists to show, and a run that repeats it is
re-run at three.

### The planning changes

Step 2 of `TODO.md` part 2 (kad 0.18.0, 2026-11-19), the part both arms
of the comparison share: a `domain-model` stage before slicing (one
state table per outside system or lasting thing, every state with its
way out or the owner's word that it is unsupported, held by a twelfth
readiness check), the thinnest cut written first with a size line, a
criterion only for what someone could observe going wrong (the rest
under `## Design notes`), and the plan opened as its own pull request
that the build waits for.

Seven new cases, all tool-judged: `domain-model-bank-phase1` and
`-phase2`, `orchestrator-route-domain-model`,
`vertical-slicing-thinnest-cut`, `accessibility-review-design-notes`,
`orchestrator-planning-pr-open`, `orchestrator-planning-row`. Each ran
once and its trace was read before the pass. What that showed:

- The slicer's thinnest cut held eight criteria, five of them refusals
  the security and reliability stages write again (a loan that is not
  the member's, a signed-out visitor, a double click). The skill said
  "the essential refusals a person would meet"; it now says an
  essential refusal is one the behaviour's own rule makes, and names
  what belongs to the two stages. Four criteria on the next run; 0.95
  at three (one run of three wrote more than five).
- `accessibility-review` wrote the count as `(Criteria: 8)` and quoted
  the designer's sentence inside a criterion. The pointer line's form is
  now given once, and a criterion names a message, never quotes it.
- Two graders failed correct runs. `domain-model-bank-phase1` wanted a
  question mark (the run ended "Please answer each of the four").
  `orchestrator-planning-row`'s `tool_order` could not order a branch
  and a gate run that share one Bash call, which every run did; it is
  two patterns on the trace now.

Eleven frozen histories carried the old text of four skills and were
captured again from runs on the new text; the two phase-3 judges are
pinned to the forks those runs presented (five for reliability, three
for security).

The gate, 2026-11-19: 109 cases. The seven new at three runs (bars
1.00 but `vertical-slicing-thinnest-cut` at 0.95); 102 at one run, of
which nine dipped and passed at three
(`accessibility-review-payfine-subtle`, `delegation-consult-with-file`,
`delivery-screens-stray`, `library-app-structure-review`,
`orchestrator-autopilot-round`, `orchestrator-gate-checks-route-back`,
`orchestrator-recommended-not-asked`, `orchestrator-route-open-pr`,
`orchestrator-slice-review-launches`). No bar moved. The sixteen
known-bad references the changed text reaches still fail with their
rule removed, at three runs each; four of those runs ended on `OAuth
token revoked` and their two references were run again. 180 runs and $88.79 for the cases,
48 runs and $57.85 for the references: 228 runs, $146.64 by the result
files.

No case holds: the A step's own refusal of a build whose plan is not
merged (reached only with no planning pull request open), `delivery`'s
planning section past the push and a comment on a planning pull request
(the fixtures have no network), and `domain-model` reading a provider's
documentation (the eval sandbox has no web tool). The first real test
of the last is the fourth project: whether its model names the states
the first project met one slice at a time.

### The solo cadence

Step 3 of `TODO.md` part 2 (kad 0.19.0, 2026-11-19), the light arm of
the comparison as a third cadence, `solo`: one builder for the slice on
Opus under a new skill (`slice-build`: one test per criterion at the
level that reaches it, written first and seen failing), the mechanical
checks reused unchanged, one fresh fixer for what a check, the builder
or a reproduction confirmed, and one combined review whose findings go
to the pull request's body and are not fixed. The heavy arm's text is
untouched.

Six new cases, all tool-judged: `orchestrator-solo-from-message`,
`orchestrator-solo-from-standing-file`, `orchestrator-solo-build-launch`,
`orchestrator-solo-confirmed-only`, `orchestrator-solo-nothing-confirmed`,
`slice-build-cancel-hold` (on Opus). The trial of each showed no fault
in the skill text and three in the graders: an inline `(?i)` the
grader's regex engine refuses, a check that counted a launched fixer's
edits as the orchestrator's (a launched agent's trace lines carry
`parent_tool_use_id`; the session's own carry `null`), and the
builder's hand-back line checked as the whole message when the run,
asked by a person, had summarised above it. That check now reads the
last line; that the message is nothing else has no check.

Of three known-bad references written with the cases, one holds:
`confirmed-only` on `orchestrator-solo-nothing-confirmed` (with the
rule removed, a High that did not reproduce is sent to a fixer, three
runs of three). Two did not fail and were removed. With the A step's
`solo` paragraph deleted, three runs of three still took `solo` from
the standing file's line and step S's own text. With `slice-build`'s
one-test-per-criterion rule deleted, three Opus runs of three still
wrote six tests for six criteria and no adapter test: the fixture's
slice is too small to show the rule, and the comparison on the fourth
project is where it is measured.

The gate, 2026-11-19: 25 cases. The six new at three runs, all 1.00;
19 at one run, of which seven dipped and passed at three
(`delivery-ci-red-not-done`, `orchestrator-delivery-foreground`,
`orchestrator-delivery-removal`, `orchestrator-gate-checks-route-back`,
`orchestrator-issue-fix-records`,
`orchestrator-readiness-correction-autopilot`,
`orchestrator-readiness-open-item`). No bar moved. Seven existing
references still fail with their rule removed.
`orchestrator-autopilot-question`'s gave one clean run of three in each
of two passes, both failing as recorded; the others timed out at 1,200
seconds, which is its recorded pattern (with no question the run goes
on to build the slice). 73 runs and $41.21 for the cases, about $34 for
the references by the result files kept: about $76.

No case holds: S.1's check of the builder's report, the gate's fixer at
S.2, the builder asked about survivors, the verify launch for a
Critical or High and the stop when one still reproduces after the fix,
`delivery`'s "Review findings" part, and `slice-build`'s wording table
(the fixture slice has no screen). Their first real run is the
comparison.

### Run backlog

Emptied: the eight emulated cases it listed were all run, then replaced by
real cases and deleted (the table is in git history).

### Known coverage gaps

- **A launch blocks under the eval and runs in the background in a real
  session (0.14.5, 2026-11-12).** The chunk runner had six cases at 1.00
  when two real runners invented their agents' results (incident 31): the
  failure needs a launch that returns before the agent does, and `claude
  plugin eval` never gives one. `chunk-runner-waits-for-handback` holds
  the rule's mechanical half (no background command, no poll, the commit
  confirmed with `git cat-file -e`); whether a runner waits is only shown
  by a real run, which is what the test of 0.14.5 on an issue fix
  measures. A replay of a real runner at its wait does not show it
  either ("Replay cases": the harness ends the wait itself on resume). The gate's scope rule and the readiness gate's issue-fix mode
  are held without a model: `tools/validation_gate_test.py` (5 tests: the
  log and the sidecar in scope with no `--allow`, a stray file and a
  look-alike name still outside, the whole gate on a scratch repository)
  and `tools/readiness_check_test.py` (14 tests: the fixture's
  `cancel-hold-readiness` set committed as merged, then revised; older
  gaps listed and never routed; a criterion the fix adds or rewords
  failing by name; a base that is not a commit refused; a control's label
  not read as a wait, the wait beside it still read).
  Against main's skill text (a worktree with `skills/` from main, the
  four new cases at three runs): 0.88, 0.86, 0.77 and 0.30, all below
  their bars; the runner case and the unverified-line case lose only
  their `git cat-file -e` grader there.
  Sourcery's round on PR #52 (16 comments, 14 fixed, 2 declined with the
  reason on the thread; tests now 6 and 20): the gate's exemption holds
  only inside the target directory (a file named like the log anywhere
  else is outside); the readiness base must be an ancestor of `HEAD`, is
  read through a literal pathspec and written only under its temp
  directory, a document named outside the planning directory is refused,
  a routed question is compared by its whole line; a quoted span is a
  label only beside a word that says so, and a number inside a label
  excuses no wait; the log checker reads an issue fix's own sidecar and
  fails checks that are green on a commit the E line did not push; the
  skills say a chunk's commit is in `<base>..HEAD`, the runner carries
  the records prefix, each watch call has a timeout and the head is read
  again before the report. Declined: failing a builder's hand-back for
  notes beside it (three correct runs failed that grader; the rule is
  about ending on something else), and counting an older item as the
  fix's because the fix edited the same document (that is the four
  routes of incident 35 again).
  `orchestrator_log_check.py` warns on an E line with no `checks` field
  and fails one that says `clean` over red checks.
- **The skills name no project (0.14.4, 2026-11-10).** `tools/skill_words_test.py`
  (2 tests, no model) fails a skill, agent or hook that carries a word of a
  project the plugin ran on (a payee, a provider, an account store, a run by
  its number) and checks every `(incident n)` it cites exists in
  `INCIDENTS.md`; the owner's coupling check of 2026-11-10 found about a
  hundred such passages, each a war story beside a rule, and the pass moved
  the stories there.
- **The Definition of Done's README check is held by `tools/done_check_test.py`
  (6 tests, no model; 0.14.4, 2026-11-10): the sections, and the "does not"
  list read against the slice's acceptance criteria (an item sharing three
  meaning-carrying words with a criterion, or every word of a short item,
  fails naming both; "does not" inside a "does" bullet is behaviour, not
  the list). The orchestrator case `orchestrator-readme-stale-not-done`
  carries the flow around it.
- **The audit sync's transcript rules are checked without a model
  (0.14.3, 2026-11-10, handoff-slice2 P5).** `tools/audit_sync_test.py`
  (8 tests) builds a project, an audit directory with session logs and
  transcripts, a bare audit remote and its clone, and shows: a transcript
  the hook never snapshotted is carried by session id with its subagents';
  one holding a value of the invented sheet is withheld (the log still
  copied, the line and the last line saying so, no value printed or
  written); a hit in the log withholds the whole session; the larger of
  the live copy and the snapshot wins and a copy that grew is refreshed;
  a session without a SessionEnd is `open`; an unreadable transcript, or
  an unreadable listed source, withholds; without a `sources.md` nothing
  is scanned and the line says so; the lock refuses a second sync (exit
  5) and a stale lock is taken over. Measured on the owner's Mac (counts
  only): the scan over the fourteen slice 2 sessions, 73 MB of
  transcripts, takes about 23 s with a seven-row catalog. Sourcery's
  round on PR #47 (21 comments, 19 findings, all fixed, two tests added):
  every session file is staged whole under the audit directory and the
  staged copy is what the scan reads and the clone receives (nothing
  appended between the two slips through); a listed source the scan
  cannot scan (a PDF) withholds every session, log included, as does a
  catalog that prevents the scan; a `--sources` named and missing is a
  failure, never a scan skipped; a line that is not JSON is scanned as
  text (`source_scan.scan_transcript`); a session is this project's by
  its payload's own `cwd` and complete by its own event, parsed, never by
  text in a prompt; the lock is taken before the plan, a stale one is
  renamed away (one taker wins) and a live one touched after the copy; a
  withholding that changes is recorded when nothing else changed; a
  session whose transcripts have gone from the machine keeps the clone's
  earlier copy; an unreadable session log is said on the line and the
  last line. The report checks withheld before kept and finds a copy the
  sync carried into the clone; only each slice's latest sync line
  withholds. The mutation runner refuses a path outside the clone or
  untracked, restores the mutant in a `finally` (SIGTERM included), and
  counts a runner failure (a timeout, a broken import) as an error, not a
  kill. Its third round (22 comments) fixed: a transcript path a payload
  names is read only under the projects directory or the audit
  directory's snapshots (a planted log cannot make the sync copy any
  readable file); paths compare resolved and case-folded only where the
  system folds them; each run stages under a folder of its own; the lock
  file is removed if its details cannot be written; a transcript already
  in the clone is never replaced by a smaller copy, and a session folder
  is no longer rebuilt from scratch; a copy kept after its sources went
  is rescanned against today's `sources.md` and withheld if it now holds
  a listed value; the whole withheld text, not the id set, decides
  whether the sync log gets a line, and a sync without `--transcripts`
  says so on its line so the report never reads it as a clean scan; the
  report takes the chronologically latest transcript-syncing line across
  slice folders and uses the sync's projects-directory fallback; the
  mutation runner refuses a symlink, runs the typecheck on the baseline
  first, reports a command that cannot start or times out as an error,
  writes the mutant inside the restoring block, and holds a lock in the
  clone's `.git`; the audit-review skill says a withheld transcript is
  not opened in a model session. Declined with the reason on the thread:
  a project with no `sources.md` has nothing listed to scan (the line
  says so); a session's cwd is one directory, so a mixed-project session
  does not arise; the lock's stale rule (an hour, an atomic rename) is
  the accepted window for a sync that takes about a minute; the opengrep
  audit rule on the runner's one command call, as on PR #44. The orchestrator
  text change this needed is two sentences (the `; withheld: <session…>`
  suffix recorded as printed and reported to the owner), covered by the
  orchestrator cases the diff reaches, not by a case of its own: an eval
  cannot stage an audit clone inside the sandbox. `tools/mutation_pass_test.py`
  (8 tests) covers the mutation runner on a scratch Python repository
  and the reading of node's TAP and spec reporters, under forced colour, with a suite summary and after a timeout; a base that is not a ref said, not swallowed
  (a mutant that matches once and one that does not; a dirty tree and a
  failing baseline refused; a caught and a surviving mutant, the file
  restored, the report and the log carrying names and counts and never
  the replaced text); `tools/cold_read.md` is a brief and has no test.
  Also in this PR: `orchestrator_log_check.py`'s order check no longer
  counts the state table's accessibility-line repair row (a hand-back to
  `product-slicer`) as a stage the implementation entry skipped, so
  `orchestrator-log-format/check.sh` counts every error again;
  `chunk-runner-gate-outside`'s `runner-edits-no-code` grader is gone
  (the judge's FAIL clause carries it); and the `delivery-ready` loop
  state creates `tools/gh-calls.log` empty, so a run that never calls the
  stand-in fails that grader instead of voiding the run.
- **The planning-data rule is checked on an invented sheet (0.14.2,
  2026-11-09).** Nine cases and `tools/source_scan_test.py` (22 tests,
  no model) use `fixtures/library-app/source-plants/desk-fees.csv`,
  seven made-up rows; no real file can be committed. What that leaves
  unproven here, and what was checked once by hand on the owner's
  machine (counts only, nothing quoted or kept): against the real
  workbook, slice 2's planning as it was before the scrub fails the scan
  on the merchant and its fee, 39 cells in all with the workbook listed
  at the commit before that slice; the scrubbed planning still raises 48
  cells in 44 files, every one a word the workbook shares with the
  documents (category names and the like), which is one batch question
  to the owner and then lines under "Allowed by the owner". The literal
  rule of the handoff (`--strict`: no listed-commit rule, every amount
  counted) gave about 7,000 hits on the scrubbed planning. The owner
  confirmed the two rules on 2026-11-09 and asked for the partial-cell
  gap closed: a single word of a longer cell (a surname, a brand) is
  matched since, and counted only when it is a word of 1% of the rows or
  fewer and something else of its row is in the same file (a whole cell
  of as few rows, or an amount of that row); measured the same way it
  adds five cells to the scrubbed planning's 48 and keeps the pre-scrub
  failure. Sourcery's round on that PR (#46) fixed a real rewrite
  bug (a map holding a whole cell and a word of it replaced the word
  and skipped the cell: the longer hit now wins, test 20), made the
  cutoff and the listed-commit baseline per source, split camel-case
  runs in a cell as scanned text is split, and strengthened test 19. Known gaps of the scan itself, in its docstring: a file
  listed after something has read it must carry a dash under `Listed
  at` or the leak is taken as already there; an image or a PDF is listed
  and not scanned. Grader lessons of these rounds: a
  regex grader on a file a run may never write throws and voids the run
  instead of failing, so the scaffold creates the file empty and the
  grader asks for content (`orchestrator-delivery-removal`'s
  `tools/pushed-history.txt`); a `not_contains` for a command (`git push
  --force`) matched the loaded skill's own sentence about it, so it is
  anchored on `"name":"Bash","input":{"command":"`; a judge told to fail
  a reply that "decides on its own that the values are the owner's"
  failed the prescribed question three votes in three, so the criteria
  say what the reply must contain and list only failures a reply states
  about itself; and a nested agent's own tool calls are in the main
  trace too, so "the runner edits no code" cannot be a trace regex
  (`chunk-runner-gate-outside`'s grader of that name is written with
  doubled braces and matches nothing: removed in 0.14.3, the judge
  carries it). Three tool defects found re-freezing the phase histories and
  fixed: `history_stale.py` read every skill that names a script by
  `${CLAUDE_SKILL_DIR}` as stale the moment it was frozen (the CLI
  substitutes the variable on load); `freeze-history.sh`, freezing a
  resumed phase, replaced `./` in every string because the inherited
  entries' working directory is `.`, which turned the skill text's
  `/../` into `/.`; and `eval_gate.py` matched only the CLI's old name
  for a run's kept directory, so since the CLI renamed it no directory
  was removed after a run and `--keep-scaffold` recorded none.
  Sourcery's round on PR #44 (25 comments; one opengrep rule four times
  on list-form `subprocess.run`, declined) fixed eleven things in the
  scanner and delivery: a value in a file or directory name is found in history and
  renamed by the rewrite; a listed source git would commit, and a
  byte-for-byte copy of one (a workbook is binary and never matches as
  text), are problems in a history scan too; files not read as text are
  counted and said; the map and an extract are created with mode 0600
  and never through a symlink (the destination resolved first); a
  UTF-16 export is read; a transcript's keys and numbers are scanned and
  an unreadable one is not reported clean; a rewrite is refused while
  earlier backups exist under `refs/original/` instead of deleting them;
  delivery notes the head its scan passed and rescans a head that moved.
  Declined by design, each with its reason on the thread: the
  listed-commit rule is about the value, not the occurrence; the whole
  workbook is scanned whatever tab was named; a whole amount is not
  matched as a bare count of cents; each tab's first row is its column
  names; the transcript count applies the same two rules as the tree.
  Deferred to P5.1 and done there (0.14.3): withholding a transcript that
  holds a value from the audit sync. `orchestrator-delivery-foreground` lost one run to the
  missing-file throw (`tools/gh-calls.log`, which the `delivery-ready`
  state did not create empty as `delivery-ready-source` does): fixed in
  0.14.3.
- **Persona rules the orchestrator can't reach.** The orchestrator now
  invokes a routed skill and never reads the persona's `AGENT.md`, so any
  rule a routed step needs must be in the skill. `devsecops-engineer`,
  `software-architect`, `product-manager`, `product-slicer` and
  `docs-writer`, `tdd-coach`, `code-reviewer`,
  `architecture-cartographer`, `ux-designer` and `accessibility-engineer`
  have had that pass, so every persona has. Keep it that way: a new
  persona rule goes in the skill, not only the `AGENT.md`.
- **The orchestrator's chunk loop has no end-to-end case, but every step
  has one (v4 PR 3, 2026-10-31).** A whole slice is hours of launches, so
  no case runs the loop from A to E. What runs is one step from the state
  a previous session left: `fixtures/library-app/code-plants/loop/state.sh`
  builds it for real (the commits the loop makes, the gate files
  `validation_gate.py` printed, the sidecar `rounds_record.py` wrote from
  planted reports, the open log entry, the handoff) and the
  `orchestrator-*` loop cases resume the orchestrator from the handoff and
  grade that step, launches included (`tool_used` with `tool: Agent`
  counts the runner, persona and planner launches); since 0.14.1 the
  mid-chunk steps are the chunk runner's, so the five `chunk-runner-*`
  cases invoke `kad-dev-team:chunk-runner` directly from the same states
  (an eval trace sees the main agent's launches, not a nested agent's)
  and `orchestrator-chunk-runner-launch` and `-handback` grade the
  orchestrator's side of the hand-over. What the 0.14.1 gate taught
  (2026-11-09, five rounds): a nested agent's launches do appear in the
  main trace (the runner's builder, reviewer and smoke agent showed as
  `Agent` calls in `-launch`), so a count of builder launches cannot say
  who launched them; a `tool_order` grader fails when its "after" tool is
  never called, so "X before any Y" where no Y is the right outcome wants
  a `tool_used` with `max: 0`; a trace regex on a script's name matches
  the skill's own text once the skill is loaded, so "the script was not
  run" is a `tool_used` on Bash; a commit-message regex must cross the
  JSON-escaped quote (`[\s\S]{0,300}?`, not `[^"]*`); and a judge on
  `last_message` failed a reply that was exactly the prescribed one-line
  hand-back three votes in three, twice, so the line's shape is a regex.
  Two real defects the same rounds found and fixed in the skills: the
  runner ended its round on a sandbox FAIL the owner had opted out of at
  A (the orchestrator's own rule now applies to it), and the open-work
  step stopped every routing where `gh` could not reach GitHub (it now
  asks only when `origin` is on `github.com`, decided from the remote
  and never from a planning read). The implementer
  steps are their own cases (`tdd-implementation-chunk-plan`,
  `-lite-chunk-plan`, `-one-chunk`), as is the triage
  (`external-review-triage-cancel-hold`). What still needs a real run: the
  log entry end to end across sessions and the stall rule; read the run's
  `orchestrator-log.md` with `tools/orchestrator_log_check.py`
  (`orchestrator-log-format/check.sh` runs it on a v4 template entry
  always, and on the second real run's private log when given), the way
  the quarantine flow was proven (H6, 2026-10-18; I, 2026-10-19, both in
  `TODO.md`). Two more model-free checks since 0.14.0: `bash
  tools/kad_test.sh` runs the launcher `bin/kad` against stub `claude`,
  `srt` and `gh` in a scratch home (the permission set shown once and
  approved with one yes, the stored file never deleted, Chrome's
  native-messaging files written when missing, `--reset` and
  `--no-chrome`), and `python3 -I tools/sandbox_check_test.py` reproduces
  the write check's false FAIL on the launcher's own folders and shows it
  fixed; since 0.14.3, `python3 -I tools/audit_sync_test.py` and `python3
  -I tools/mutation_pass_test.py` (above).
  J4 in `TODO.md` lists what each real run must show.
- ~~**The main agent acts before `tdd-implementation` loads.**~~ **Closed
  for the parent.** It used to write its own answers to a design's open
  questions into the design doc before invoking the skill or delegating
  (2/3 runs). The skill's and `tdd-coach`'s descriptions now say to leave
  those questions to the skill: 0/3 direct, 0/2 through the agent. What
  remains on the agent path is the subagent's own process (see
  `tdd-implementation-cancel-hold-via-agent`).
- **The eval's judge can't be checked from outside.** A re-ask with
  `tools/rejudge.py` disagreed with the eval on three of five checked
  verdicts, and a probe showed the eval failing a long review as
  `last_message` while passing the same text as a file. Borderline
  verdicts flip. Prefer graders on saved files, keep criteria to plain
  checks, and read a single failure as possibly noise until it recurs.
- ~~**software-architect has no `Skill` tool.**~~ **Closed.**
  software-architect and product-slicer now list `Skill` (their skills
  consult `map-query`, the devsecops skills and `acceptance-criteria`).
  The eval can't show the difference: it doesn't enforce an agent's
  `tools:` list, so a subagent called `Skill` and `Agent` before either
  was listed. What the agent path does show is covered by
  `architecture-design-payfine-via-agent`.

~~- **`devsecops-engineer` has one case out of six skills.**~~ **Closed —
  all six skills now have a case, all passing.** `security-requirements`
  (7/7), `reliability-requirements` (5/5), `security-review` (7/7),
  `reliability-review` (6/6), `supply-chain-review` (7/7), and
  `operational-readiness` (6/6) are all covered. `operational-readiness`
  was written from a gap with no source material at all — its case tested
  both halves of the skill's central judgment call at once (correctly
  scaling down formal incident process and monitoring for a solo project,
  while correctly *not* scaling down an untested rollback or a schema
  change coupled to code) and passed clean.
- ~~**The hand-back rule is tested from one side only.**~~ **Closed.**
  `devsecops-engineer:security-requirements` now tests the producing side —
  reports a login gap forced by the slice being hosted-and-reachable, names
  `product-slicer` by name, and doesn't enumerate a resolution menu — all
  passed clean. Independently auditing `evals/example/security-requirements-001.md`
  against `SKILL.md` directly (not assuming it was correct) also surfaced a
  real, narrower gap: it never addresses monitoring/telemetry/analytics as
  an exit for its sensitive data, though four of the five named exits are
  covered. A new `addresses-all-five-exits` grader now checks this, and it
  caught the same gap in this case's own first draft too (missing
  exception/stack-trace, distinct from error-response) — fixed and
  re-verified. That emulated case has since been replaced by the
  `security-requirements-*` real cases; its summary is in git history.
- ~~**`agent-eval`'s "Read/Grep/Glob only" dry-run grant isn't actually
  enforceable.**~~ **Moot:** the emulated harness is retired, with its last
  case (`orchestrator`) replaced by real routing cases.
- ~~**`tdd-coach:tdd-implementation` couldn't be checked running for real.**~~
  **Closed.** The real cases run Node's test runner in the sandbox (the
  `code-plants/tdd/` overlay's `test/ts-resolve.mjs` lets
  `node --experimental-transform-types --test` load the app's TypeScript
  with no install) and grade the trace mechanically.
- ~~**`technology-bootstrap`'s advisor-consult path is only softly graded.**~~
  **Closed.** `technology-bootstrap-phase2` now checks the trace: it
  consults `supply-chain-review` for the pinning question, inline rather
  than by spawning an agent, and doesn't consult `security-requirements`
  reflexively. All 18 kept phase-2 traces pass.
- ~~**`ux-designer` has no case run yet.**~~ **Closed — both run**, and
  since replaced by real cases (see the UI personas entry below); what
  follows describes the emulated cases, now in git history.
  `design-system` (9 graders, three-phase — reference-vs-generate, then the
  candidate choice: 9/9 PASS after one re-run) and `screen-design` (9
  graders, single-phase: 9/9 PASS) were both written straight from
  `agents/ux-designer/AGENT.md` and the two skills' `SKILL.md` text, before
  either was checked against a real dogfooded artifact — the same
  order-of-operations correction this plugin's methodology settled on
  after `security-requirements`. All graders in both cases are
  `portable-*`, since most of what these two skills get right or wrong is
  process (ask vs. generate, resolve-before-asking, reuse-before-invent,
  render-for-real), not one fixture's particular facts. `design-system`'s
  first run failed `candidate-choice-is-real-question` — not a skill-text
  gap (the skill already explicitly names and warns against "three
  variations on the same idea wearing different colors"), but that run's
  own three generated candidates did exactly that: varied by
  color/type/shadow, shared one layout and density. Re-ran with
  structurally distinct candidates (single-column ruled feed vs.
  two-column card grid vs. dense icon-led list) and it passed clean —
  confirmed single-run variance, not systemic; no skill-text change made.
  Separately, a judge grading `portable-rendered-artifact-referenced`
  checked the real filesystem for referenced HTML/screenshot paths and
  failed the case because an emulated dry run never writes real files —
  overridden to PASS with reasoning recorded in that grader's own
  `eval-score` file; the fix (explicitly telling the judge not to check the
  filesystem) was applied on `screen-design`'s equivalent grader and held.
  `screen-design`'s fixture also had a case-authoring gap caught before
  running: its acceptance criteria didn't originally include an unfilled
  accessibility placeholder for `portable-carries-forward-unresolved-
  upstream-placeholders` to actually check — added to `prompt.md` before
  running, matching the `reliability-requirements` precedent.
- **`architecture-cartographer` has no case run yet.** **Closed — both run,
  both clean.** `map-query` (6/6 PASS) and `map-update` (6/6 PASS) were
  both written straight from `agents/architecture-cartographer/AGENT.md`
  and each skill's own `SKILL.md` text, before any real dogfood output
  existed, same order as every prior case. Neither needed a skill-text
  fix on its first run — the strongest first-pass result of any two-skill
  persona built in this roster, plausibly because the mandate is
  mechanical fact-reporting rather than a judgment call, leaving less room
  for the kind of interpretive drift `tdd-implementation` and
  `test-quality-review` each needed real fixes for. Worth noting as a
  positive counter-example to the two gaps above about this harness's
  Read/Grep/Glob-only dry-run grant: `map-update`'s real work is itself
  grep/import-statement text search with no build step or installed
  tooling, so the dry run's tool restriction doesn't understate what a
  real invocation would do here the way it does for `tdd-implementation`'s
  "run the test suite" moments or `accessibility-review`'s browser
  driving — this is one of the only cases in the plugin where the
  emulation's tool grant and the real persona's actual working method are
  the same shape. Full run detail, including the three deliberate traps
  each fixture's fixture data was built to test (shape-not-name matching
  and map staleness for `map-query`; tier carry-forward vs. honest
  `untiered`, a duplication candidate, and a wrong-direction candidate for
  `map-update`), in each case's own `eval-score/summary.md`.
- **`software-architect:architecture-review` went through three generations
  of real-CLI cases before the suite above; what each one found is the
  reason the current design looks the way it does.** The emulated case
  covered 4 of the skill's checks; 7 inline-snippet cases with answer-key
  graders followed, then the same 7 with substance-only graders, then the
  library-app suite. Across all of them, every apparent failure but two
  traced to the fixture or grader, not the skill: fixtures that gave the
  answer away in comments, fixtures with accidental bugs the no-plugin
  review got credit for finding (an inert `Number.EPSILON`, an S3 key with
  no year, a reminder that re-sent every run), graders that required the
  skill's own vocabulary, graders that assumed one correct framing. The
  two real skill findings, both fixed and re-verified in the library-app
  suite:
  - **The composition-root exemption was too lenient.** The skill said a
    factory call returning the interface type was fine wherever it sat;
    both arms, including the plugin's, correctly argued that a use case
    importing `main/wiring` depends on everything wiring imports.
    `skills/architecture-review/SKILL.md` and `architecture-design/SKILL.md`
    now say the exemption covers the composition root knowing both sides,
    not business code knowing the composition root; the fixture's
    `return-book.ts` moved from trap to planted violation.
  - **The foundation lived only in `AGENT.md`, which `claude plugin eval`
    never loads.** The importance-as-risk test, the four rule definitions
    and "state the ordering you assume" sat in the agent prompt;
    `architecture-design` already carried its own copy, `architecture-review`
    didn't, so it ran without them whenever invoked as a skill (eval,
    direct `/architecture-review`, inline consult). The review skill now
    carries them and opens its report with the assumed ordering;
    `AGENT.md` points at the skills instead of restating the rules.

  **Uplift evidence, honestly stated.** On every planted architecture
  defect the no-plugin Sonnet baseline is as good as the skill at one run
  each. Where the skill measurably differs is behaviour the skill text
  spells out and the baseline does inconsistently: stating the importance
  ordering (lending), respecting a documented tradeoff instead of demanding
  unification (fines), noticing policy mixed with mechanics (fines),
  scoping pre-existing problems as non-blocking in a PR review
  (reporting-pr). Restraint on the clean module (catalog) is not uplift:
  both arms report nothing above Low there. The blind pairwise judge
  preferred the no-plugin review 5 of 9 times, the plugin's once, and
  split 3 (`results/20261009-204439-calib2/pairwise.json`, reasoning
  included). Its reasons are consistent: the baseline reviews more
  broadly and gets credit for product gaps and reliability notes the
  skill scopes out (holds never enforced, a fine that never grows, a
  nightly job with no error handling), while the skill stays on
  architecture, hedges less, and writes no code sketches. Read that as a
  measurement of the judge's preference for breadth against a skill that
  is deliberately narrow, not as the skill losing on its own ground; on
  its own ground the grader table above is the evidence. Single-run numbers;
  `runs: 3` has not been paid for yet.

  **Which model, and why it mattered.** The first two calibrations ran
  with no `execution.model`, so both arms used the session default,
  `claude-fable-5-1`, and on Fable the skill fired 9/9 and the baseline
  matched it on every planted defect. Every real case now pins
  `execution.model: sonnet`, and the first Sonnet run
  (`results/20261009-212430-sonnet1`) showed what Fable had been
  covering: the skill fired in only 5 of 9 cases, and where it fired the
  reviewer still missed the runtime cycle, policy mixed with mechanics,
  the premature strategy interface, the missing channel abstraction, the
  technical-role directories and PR scoping — things the skill named but
  did not say how to detect. Two skill changes followed: a trigger line
  in the description ("invoke first, before reading any code, for any
  request to review a module/directory/PR for architecture, structure,
  boundaries, dependencies, layering or design; never review architecture
  without it"), and a concrete check for each of those smells
  (value-position vs type-position imports for cycles; label each line
  policy or mechanism; count implementations and ask what the interface
  isolates; an `if/else` over same-job concretes is a visible axis; strip
  the suffix from each top-level directory; a mandatory "Pre-existing,
  not blocking" section). Second Sonnet run
  (`results/20261009-213816-sonnet2`): skill fired 9/9, with-plugin 92%
  of scored graders vs 65% before, baseline 62%, mean delta 0.38 vs 0.08.
  Two further single-case fixes (PR scoping: skim the module; inconsistent
  abstraction level: a concrete check) and one case-prompt fix (verbatim
  relay in the agent path) followed, each verified on its own case. A
  confirmatory full pass on the final skill text
  (`results/20261009-221953-sonnet-final`, $5.17 + $1.68 judge): skill
  fired 9/9, with-plugin 100% of scored graders in all nine cases,
  baseline 60%, mean delta 0.43; the baseline missed the runtime cycle,
  policy mixed with mechanics, the premature strategy interface, the
  documented rounding split, the missing channel abstraction, the CSV
  smell, PR scoping and the ordering line, and raised a Medium on the
  clean module. Blind pairwise judge on that pass: plugin 6, baseline 3,
  split 0.
  The blind pairwise judge went plugin 3 / baseline 3 / split 3 on the
  first Sonnet run, 4 / 3 / 2 on the second and 6 / 3 / 0 on the
  confirmatory pass; with both arms on the same model the breadth
  preference it showed on Fable is gone. All single-run numbers. The lesson for the next skill:
  verify on the model the plugin's sessions actually run, and write the
  skill so a mid-tier model can apply it, not only recognise it.

  **One Opus comparison run.** On 2026-10-10 the suite was re-pinned to
  Opus for one pass on the pre-security fixture
  (`results/20261010-082244-opus-final`, $7.58 + $2.18 judge, negative
  cases in `-opus-neg`): with-plugin 100% in all nine cases, baseline
  lower on lending, notifications, reporting-pr and the agent path (mean
  delta 0.18, against 0.43 on Sonnet). The blind pairwise judge went
  plugin 2 / baseline 6 / split 1 — the same breadth preference it showed
  on Fable, where the stronger baseline also writes the broader review.
  Opus costs more per pass than Sonnet and showed a smaller delta, so the
  suite stays pinned to Sonnet; fixes are made in an Opus session and
  verified on Sonnet.

  **Re-verified on the security-extended fixture (2026-10-10).** Planting
  the security material changed `main/`, `infra/http/` and the catalog
  port, and one Sonnet run on the new fixture then raised a Medium on the
  clean catalog module about a *neighbouring* module (loans' adapter using
  the ORM where catalog's uses raw SQL).
  `skills/architecture-review/SKILL.md` now says a module-scoped review
  puts what it notices in other modules under "Pre-existing, not
  blocking", and that adapters using different idioms behind their ports
  is not a finding. Confirmation on that text, Sonnet, one run per arm:
  `results/20261010-093922-arch-final` (catalog, fines, lending, members,
  both negative cases; the rest of that pass hit the account's spend
  limit) and `results/20261010-101700-arch-rest` (the other five).
  With-plugin 100% of scored graders in all nine cases; baseline catalog
  0/1, fines 2/4, lending 73%, members 2/3, agent path 18%, notifications
  3/3, reporting-pr 1/3, reporting-review 1/3, structure 3/4.

  **Agent path.** `library-app-lending-review-via-agent` routes the same
  review through the `software-architect` agent (`allowed_tools` includes
  `Agent`). It confirms delegation and that the agent-wrapped review
  matches the skill-only one on every grader. The interactive design loop
  (`architecture-design` asking for approval) needs the phase-chained
  cases described under "Interactive skills" above.

  Cost of the whole architecture-review eval effort, all generations: about
  $40.

- **`devsecops-engineer:security-review` moved to the library-app fixture
  in one generation, following the playbook above.** The fixture had no
  authentication at all, which every security reviewer would have
  reported first, so a session layer went in before any plant: staff
  routes behind `requireRole('staff')` per path prefix, a member portal
  behind `requireRole('member')`, tokens looked up by SHA-256 digest. Ten
  plants and seven traps followed (`S`/`ST` rows in the fixture's
  `answer-key.md`), each tied to a section of `skills/security-review/SKILL.md`.
  The emulated `devsecops-engineer:security-review` case it replaces is
  deleted. Three calibration passes found three skill gaps, each fixed in
  the skill and re-verified:
  - **Pre-existing problems leaked into a PR's findings.** On the portal
    PR the reviewer numbered the old `respond.ts` problems among the PR's
    own findings (one at High) because the new routes call it. The skill
    now requires a separate "Pre-existing, not blocking" section for any
    problem in code the change didn't write, *including* one the change
    newly routes traffic through, with the new exposure stated there.
  - **Ordinary request volume was promoted to a security finding.** On
    the clean catalog module the reviewer rated "public search, no rate
    limit, table scan" Medium every time; the baseline said Low. The
    skill now says availability is a security finding only when one
    request costs out of proportion to its size; volume and capacity need
    a scale story and belong to `reliability-review`.
  - **"Log an opaque ID" didn't say what opaque means.** The reviewer
    proposed logging the library card number in place of the whole member
    object, then flagged card numbers in logs two findings later. The
    skill now defines opaque (row id, surrogate key, request id) and says
    a natural identifier the person carries is part of the subject.
  - **The error-disclosure check was a principle, not a procedure.** One
    Sonnet run never looked at what the catch-alls return and called the
    pay route's catch "handled correctly". The skill now says how to check:
    for every catch that writes a response, ask what the caller gets when
    the error is one nobody anticipated (a driver or SDK error).

  Two fixture accidents were fixed rather than graded around: the catalog
  route was the only one left without error handling after the
  responder refactor, and the public search had no result cap (moving
  the cap into the `CatalogReader` port, not the adapter's SQL, was needed
  to keep the architecture catalog case clean). Two graders were narrower
  than a good review (the SQL-injection fix wording, the error-text
  grader expecting `/portal` to be named) and were loosened.

  **Uplift.** Confirmatory pass on the final skill text
  `results/20261010-093922-sec-final` ($3.39 + judge): skill fired 5/5,
  with-plugin 100% of scored graders in all seven cases. The baseline
  missed the error-text disclosure and both reminders plants; across the
  earlier Sonnet passes it also called the Stripe publishable key a
  leaked secret and rated a catalog rate-limit note Medium. Blind
  pairwise judge: plugin 4, baseline 0, split 1. Single run per arm; the Opus calibration
  passes before the switch back to Sonnet showed the same shape. Cost of
  the migration, all passes including the Opus ones: about $30.

Root-cause notes for any bug a case caught live in that case's own
`eval-score/summary.md`, not here — check there before touching a skill,
grader, or the `agent-eval` harness that a case already covers.

- **Clean an agent before migrating its skills: the rules a skill needs
  move out of `AGENT.md`, the routing stays.** `devsecops-engineer`'s
  `AGENT.md` held review standards (verify a Critical/High first, don't
  inflate severity, read and never run), stop rules (a slice that has to
  grow, a control with no boundary) and the consult-mode rule, none of
  which a direct, inline or eval invocation of its skills ever saw. Each
  moved into the skills that need it; who a hand-off goes to
  (`product-slicer`, `docs-writer`, back to the architect) stayed in
  `AGENT.md`, as did choosing among the persona's own skills. The pass also
  found `AGENT.md` calling real-looking values in fixtures "noise", against
  `security-review`'s own five-exits rule. Done before calibration so each
  suite is calibrated once; the `security-review-*` regression after the
  change (`results/20261010-secrev-regress`) stayed 7/7 with the plugin.
  Output location is still `AGENT.md`-only across the roster, queued as its
  own pass.
- **`devsecops-engineer:reliability-review` moved to the library-app
  fixture in six calibration passes.** Most of its 13 plants were already
  in the app as ungraded "known observations" for the other two suites;
  new plants were a postal adapter that swallows failures, a retry on
  declines in `CollectFine`, and `ops/alerts.yml`. Skill fixes that
  survived the answer-key/grader/fixture order: (1) the description now
  says *invoke first, before reading any code* — it did not fire on two of
  five scoped cases; (2) its finding format, with a required fix line, is
  written into the skill instead of pointing at `security-review`'s,
  which a lone invocation never loads (`supply-chain-review` and
  `operational-readiness` had the same dependency and got the same fix);
  (3) concrete checks for resource lifecycle (follow every constructor and
  factory, ask what it acquires and who releases it), unbounded results
  (find each query's limit, and report it even when the same query has a
  louder problem), and state that must outlive the process; (4) scale
  discipline: growth with stored data is never "by construction", a
  missing bulkhead needs a named resource, a load and a reason the load is
  plausible, and verifying a High capacity finding means doing the
  arithmetic with the repo's numbers. Fixture lessons: every concrete
  number a fixture states becomes material for a capacity finding, and a
  fix to one persona's plant can plant another's (moving a vendor error
  into a route was an Invasive Species violation for the architecture
  suite; a separate public pool invited a least-privilege finding for the
  security suite). A restraint case's prompt must be as neutral as the
  other suites' ("review X for production-readiness"): asking how a clean
  module behaves "when the database is slow or down and as it grows"
  produced a Medium/High capacity finding in every run of both arms, and
  the neutral prompt stopped it. Regressions after the final fixture: security 7/7,
  architecture catalog fixed; `library-app-lending-review` missed the
  runtime cycle twice in a row in unchanged code (the review called
  `LoanPolicy.sample` dead code) — a watch item for `architecture-review`,
  not caused by this work.
- **`devsecops-engineer:supply-chain-review` moved in three calibration
  passes, including the first phase-chained case.** The fixture gained a
  real v3 lockfile (CI's `npm ci` had nothing to read), a `Dockerfile` the
  deploy job actually builds and ships, `dependabot.yml`, a release-notes
  workflow, a tag-pinned Slack step and `audit-ci.jsonc`. Skill fixes: the
  description now covers accepting, suppressing or recording a finding
  (the accept flow never fired before); a check that lists every
  reference in all three places (lockfile installs, `uses:` lines, `FROM`
  lines) before writing findings; and recording an acceptance as three
  explicit parts (the entry, no unenforced expiry, an ADR-worthy flag for
  `docs-writer`). Methodology: a frozen history embeds the skill text
  loaded when it was frozen, so a skill edit reaches a later phase only
  after the earlier phase is re-run and re-frozen; and a frozen history
  must be checked for account identifiers before it is committed (these
  carry sandbox paths, session and request ids, nothing personal).
  Regressions on the new fixture: `security-review-config` 1/1,
  `library-app-structure-review` 1/1.
- **`devsecops-engineer:operational-readiness` moved onto the fixture as
  two phase-chained scenarios** (a release carrying an irreversible
  migration, and the running service) plus two negative trigger cases.
  The fixture gained `ops/migrate.sh`, migrations `0011` and `0012` (the
  latter copies `stripe_charge_id` into `charge_id` and drops the old
  column), a deploy step that runs them before the release, and a note in
  `types/vendor.d.ts` that an empty monitoring DSN turns reporting off;
  plants `OR1`–`OR6` and traps `ORT1`–`ORT3` are in the answer key. Skill
  fixes: the description says to invoke it first for any "can we ship
  this?" question, and the first response is the situation questions,
  not a review (both phase-1 cases reviewed straight away before); a
  "how to check" step for section 1 (list everything that runs, and say
  what tells someone it failed, stalled or never started — error
  reporting can't see a run that never started) and for configuration
  (what happens when each variable is absent); a never-rehearsed rollback
  is its own finding, fixed by rehearsing it, even when a migration also
  breaks it; a missing 2am note is fixed by one short note now; every
  bold check is walked before Findings is written; and a broken way back
  is described as broken, not as "no rollback path"; and the output
  template requires a **Rehearsed** and a **Written down** line, each a
  finding when the answer is no. The prose rules alone left the
  rehearsal finding at 2/3 and the 2am note at 1/3; the template lines
  took both to 3/3. Phase 2 went from 0.5 to 0.93 (release) and 1.0
  (ops). Case lessons: a run that starts a
  background subagent can end on a short postscript after its report, and
  `focus: last_message` then grades the postscript; the
  `no-false-alarm-no-rollback-path` criterion failed accurate,
  change-scoped claims until it said what *does* count as a false alarm;
  and a resumed run writes its session transcript next to
  `history.jsonl`, now gitignored. A `release-phase1-via-agent` variant
  never asked the situation questions in two calibration passes and was
  dropped. Regressions: `security-review-config` 5/5,
  `supply-chain-review-workflows` 3/3.
- **Phase D of the audit (2026-10-14): the chains re-frozen and the forks
  moved before the document.** Both requirements skills said "get
  approval before writing them in" and "a criterion that depends on a
  pending decision waits; write the rest", so every phase-2 run wrote the
  whole document with its decisions pending, and the judge failed two
  runs in three on a three-thousand-word message. The skills now say
  approval comes before the document (forks one at a time through
  `AskUserQuestion`, all in one plain-text turn without it; the document
  once, after, complete), which is what the real flow does with the
  question tool. Phase 2 is then a short message graded on
  `last_message`; phase 3 is the saved file. A history staleness check
  (`tools/history_stale.py`) found five stale chains, not the audit's
  three; all are re-frozen from gate runs kept with `--keep-scaffold`.
  `technology-bootstrap-phase3-reject` is the suite's first chain whose
  answer rejects the recommendation. `requirements-refinement` gained
  two rules from its phase 2: an answer that skips a question is recorded
  as not yet confirmed and asked again, and a finding names what is
  forced and its owner rather than the code change. Full account under D
  in `TODO.md`.
- **`devsecops-engineer`'s two requirements skills moved onto the fixture
  as three-phase chains** over one slice that isn't built yet — a member
  pays an outstanding fine from the portal — plus a negative trigger case
  each. Nothing new is planted: the existing code is what the criteria
  must cover (`SR`/`RR` rows in the answer key), and each prompt carries
  an engineer's proposal so phase 2 has a known fork for phase 3 to
  reject. Skill fixes: the first response is questions, after reading the
  code and without asking what it answers (both skills reviewed straight
  away in every first run); obligations and who may see whose data are
  never in the code; the document is the second response, so questions
  can't be parked under "Open questions" while criteria get written
  anyway (the security skill did exactly that until this went into the
  output section); a decision stays pending until the user approves it
  and criteria depending on it wait; a proposal already on the table is a
  decision whenever the skill would change it; values public by design
  aren't secrets; a retry is only for transient faults; after approval
  the finished document is complete, and accepting a risk with a manual
  remedy adds a criterion that the cases are findable. Case lessons:
  phase 2 can't demand finished criteria when the skill correctly stops
  at a fork, so criteria are graded in phase 3; later-phase graders must
  agree with the user's answer (one demanded duplicate prevention after
  the user accepted duplicates); a grader whose PASS condition lists
  examples gets read as a checklist; and `freeze-history.sh` now also
  freezes a resumed phase, from the transcript it writes next to
  `history.jsonl` plus text from the chosen run's final message. Only the
  last `--case` flag counts.
- **`orchestrator` got four real cases alongside its emulated one**, on
  planning folders for the same pay-a-fine slice
  (`fixtures/library-app/planning/`, copied into `docs/pay-fine/` by each
  case's scaffold). The first probe found that step 4's "read the target
  persona's `AGENT.md`" can't work: the file sits outside the project, the
  read was refused, and the run fell back to invoking the skill. Step 4
  now invokes the routed skill with the `Skill` tool and never looks for
  an `AGENT.md`, which makes "everything a routed step needs lives in the
  skill" a requirement for every persona; only `devsecops-engineer` has
  had that pass so far (see Known coverage gaps). The log entry also moved
  to routing time: a routed skill that stops to ask the user ended the
  run before the old end-of-step entry was written. One fixture lesson:
  the hand-back case's requirements doc listed member refunds as out of
  scope, contradicting the hand-back's "nobody scoped it", and
  `product-slicer` rightly raised the contradiction instead of slicing.
  Observed, not graded: once routed, `product-slicer` grew the slice on
  its own judgment and superseded it without asking — since covered by
  `vertical-slicing-handback`, see below.
- **`software-architect`'s other two skills moved to the real suite.**
  `architecture-design` runs on the pay-a-fine slice before its design
  (two phases plus a negative case); `technology-bootstrap` can't use the
  library-app, which already has a stack, so it moved the emulated case's
  empty repo into `fixtures/bootstrap-empty/` (three phases). Skill fixes:
  the persona's where-to-save and vocabulary rules moved into the skills;
  a consult invokes the consulted skill with the `Skill` tool instead of
  reading its file, and both sides now say the consult returns an answer,
  not the turn — a consulted skill that "stops" ended the whole run, and
  the first wording ("hand control back") was read as handing back to the
  user; a delegation covers only what it names (the bootstrap settled a
  UI framework nobody delegated); and the design template records each
  decision's approval, fix-now-or-defer included. Case and tool lessons:
  `freeze-history.sh` now makes the frozen run's sandbox paths relative,
  because a resumed phase that wrote to the old absolute path was refused;
  a skill that saves its document needs its graders on that file
  (`focus: {source: file, path}` — `focus: files` gives only the list of
  file names), and the answer should name the file so the path is fixed;
  an answer that says "go ahead and write it up" approves everything still
  open; a later phase must be frozen from a run whose question the next
  answer actually answers; a grader written for a question needs
  rewording for the record written after approval; and one design grader
  ("chooses no new technology") was dropped after judges failed it on
  three documents that plainly chose nothing new — the CLI's own
  long-input warning applies. Regression after the consult change:
  `supply-chain-review` unchanged (7/8, `build` 4/5 as committed); the
  requirements phase-1 and orchestrator cases showed `security-requirements`
  skipping its questions about one run in four, worse under the
  orchestrator, fixed by an orchestrator step-4 line (routing doesn't
  hurry a skill whose first response is questions): 4/4 on both after.
- **The non-code personas got a lighter pass: rule cleanup plus one real
  phase-1 case per skill**, not full chains. `product-manager`,
  `product-slicer` and `docs-writer`'s three skills with cases moved their
  persona rules into the skills (where to save; the first response is
  questions for `requirements-refinement`; `vertical-slicing` hands back
  when there's no Active requirements doc, never reaches past "confirmed
  in scope", names the scope-map step in the title and invokes
  `acceptance-criteria` before writing criteria; write for skimming). Six
  real cases on the pay-a-fine planning folders, plus a new larger
  `self-service` problem for `scope-map`. Calibration found three skill
  gaps: `user-story-writeup` never fired on "ready to track" because the
  run filled the slice's security placeholder first (the description now
  says placeholders don't block a story); an `acceptance-criteria`
  rewrite settled what a member sees on a gateway error (a rewrite can't
  decide what the vague criterion never decided); a problem doc listed an
  assumed limit as a constraint and the same thing as an open question
  (an assumed limit is an open question). Grader lessons, again: a
  "steps only" grader failed one-liners that restate the problem doc's own
  constraints, which the skill allows, until it became a concrete list of
  violations; "FAIL if it does" after a negative PASS sentence was misread
  and the grader was dropped. The emulated cases are kept for depth and
  marked stale; they feed `AGENT.md` to the model, so re-running them
  can't show the skills stand alone.
- **`vertical-slicing`'s hand-back path got its own case**
  (`vertical-slicing-handback`), the problem `orchestrator-backward-route`
  had only observed. The first run grew slice 1 to include member refunds,
  wrote the refund requirement into the Active requirements doc itself,
  authored security criteria for it and edited the design: the skill only
  said a *new* slice needs a requirements pass. It now says any capability
  added mid-flight, new slice or growth, gets its WHAT from the user in
  `requirements-refinement`, and that the slicer's output is the scope
  decision: it names which documents the choice invalidates and which
  skill redoes each, and edits none of them. Grader lesson: the first
  ranked-order grader asserted a separate slice was "available", which
  is the answer key's opinion, not a fact; a run that rejected it with a
  concrete reason deserved a pass.
- **`docs-writer`'s last five skills got real cases**: `adr` (plus a
  negative), `why-comments`, `pr-writeup`, `user-facing-docs` and
  `staleness-audit`. Their plants live in `fixtures/library-app/docs-plants/`
  and only the owning case copies them in, so no other case's app changes
  (answer key `D`/`DT`). Two skill fixes: `adr` now opens with its three
  checks as yes/no lines and stops at any "no" — asked for an ADR on a
  rename, it had fired and asked how to scope one; `user-facing-docs`
  states only what it checked and names no screens it can't see — it had
  written "My Loans → Renew" and "no late fines" after reading only
  `lending/`, and its description now says "help page", which one run
  needed to fire. Graders: a "no invented rules" grader failed accurate
  consequences of the code (renewing clears the overdue status) until it
  listed what follows from the code; the no-click-path grader was dropped
  after failing plain pages twice.
- **The code personas moved to real cases**: `tdd-coach`
  (`tdd-implementation`, `test-quality-review`), `code-reviewer`
  (`code-review`) and `architecture-cartographer` (`map-query`,
  `map-update`), 14 cases on case-only overlays in
  `fixtures/library-app/code-plants/` (`verify.sh` type-checks each overlay
  and runs its tests; answer key `Q`/`QT`, `C`/`CT`). The emulated cases are
  deleted. Skill fixes:
  - `tdd-implementation` now stands alone (gap sorting, missing
    collaborators, reused wording, boundaries, a fix with no tests yet).
    Its trigger names what users say and says to invoke it first: before
    that it never fired on "build it" or "apply the fix".
  - Calibration also added minimal GREEN (the next entry's `else` waits
    for its test), a `test-quality-review` `Skill` call every cycle (a
    "review: clean" line without one is a skip), no edits to the design
    or other stages' documents, and reverting such an edit made earlier
    in the conversation.
  - `test-quality-review` and `map-query` fire on the user's wording.
    `code-review` sweeps every function past its checklist before judging
    (feature envy was missed otherwise). `map-update` templates its
    candidate lines ("not decided here") and compares export names
    mechanically.
  - The map now lives at `docs/architecture-map.md` at the app root (the
    user's call), so no consulting skill passes a location.
  - tdd-coach and code-reviewer gained the `Skill` tool, which their own
    consults need.

  The tooling lesson outranks the skill fixes. An `llm` grader on
  `focus: trace` sees only 24 messages, so every trace-judged TDD grader
  was really grading the final report until the process checks moved to
  `regex`/`tool_order`. Validate such graders offline against kept traces
  before spending runs. Grader lessons: a revert counts as an edit (grade
  the doc's final content instead); a scratch script in the sandbox's
  temp dir isn't "editing the project"; a formatter reading another
  object's fields isn't feature envy, and reviews were right to pass it;
  when a gap has a half the code answers, the grader shouldn't demand it
  be escalated. Two misses were a last-message artifact: a postscript
  about a stopped background task replaced the review as the final
  message.
- **The UI personas moved to real cases**: `ux-designer` (`design-system`
  as a three-phase chain, `screen-design`) and `accessibility-engineer`
  (`accessibility-review` plus a negative trigger), six cases on the
  pay-a-fine slice with case-only overlays in `fixtures/library-app/ui-plants/`
  (a slice copy with an accessibility placeholder, a binding design system,
  a declined-state mockup; answer key `A`/`AT`). The emulated cases are
  deleted. Every persona has now had the rules pass. Skill fixes:
  - All three skills say where output goes (`visual-ux/` for the
    designer), hand back what isn't theirs, and handle a session with no
    browser: write the HTML, say it couldn't be viewed, never claim or
    promise a screenshot. `accessibility-review` still computes contrast
    from the CSS as it resolves when it can only read the markup.
  - `design-system` needs a ratio for every text colour, muted and
    secondary included: a first run declared a 3.77:1 muted grey and called
    it exempt as "secondary copy only".
  - `design-system` keeps candidates out of `visual-ux/` by name: one run
    wrote them to `/tmp`, where the user couldn't open them, then moved them
    into `visual-ux/` as `.scratch-*` files.

  No rendering exists in the sandbox, so nothing here checks how a mockup
  looks; the graders read the HTML and the written documents. A
  `design-system` chain also needs its later graders updated whenever it
  is re-frozen: the chosen candidate's name changes with each frozen run.
  `accessibility-review-payfine` gives no uplift, since the baseline finds
  textbook plants too; harder plants (a focus ring that is declared but
  invisible, a contrast failure only after `:hover`) would be the next step.
- **The last multi-phase product skills moved to real cases.**
  `requirements-refinement` and `user-story-writeup` gained a real phase 2
  (the user's answers, resumed from a frozen phase 1), and
  `vertical-slicing` a case for its no-requirements stop. The remaining
  emulated cases for `docs-writer`, `product-manager` and `product-slicer`
  are deleted, which leaves `orchestrator` as the only emulated case.
  - `vertical-slicing` cut a slice with no requirements doc when the user
    said "just decide, we don't need to talk it through". It loaded its
    stop rule, read on, and cut the slice anyway with a note that the
    scope was its own judgment. The stop now opens the skill: no Active
    requirements doc means no file and no slice sketched in the reply,
    whatever the user says about skipping it.
  - Re-asking the judge outside the eval is not a reliable check. A
    grader that failed 9/9 in the eval passed 6/6 when re-asked with
    `claude -p --model sonnet` (and failed with `claude-sonnet-5-5`), and
    later cases went the other way (see playbook step 4). Earlier
    "re-asked, the judge passes it" notes in this README are hints, not
    verdicts.
- **software-architect and product-slicer got the `Skill` tool, and the
  architect's agent path got a real design case.** The eval doesn't
  enforce an agent's `tools:` list, so the case passed before the tool was
  added; it caught something else. Through the agent, a `map-query`
  consult ended the turn: the subagent's final message was the map report,
  and the design never resumed. `map-query` now says that when another
  skill consulted it, its report is that skill's input and the caller's
  work carries on in the same response; 3/3 clean after. One earlier run
  also read the map directly instead of consulting `map-query`; it didn't
  recur in the final three.
- **Closing the remaining gaps: judge checks, harder plants, restraint,
  the parent's edits, and the routing table.**
  - `tools/rejudge.py` replays a grader against a result file. Using it
    showed that re-asking the judge is a hint only (playbook step 4), and
    settled the two "judge error" notes: `scope-map-self-service` is
    borderline, and design-system phase 3's direction grader stacked
    conditions; it is now two graders.
  - `accessibility-review-payfine-subtle` (answer key `A5`–`A8`,
    `AT4`–`AT6`) plants what only the cascade, a state or an id shows.
    Both arms caught three of four; neither caught the link that fails
    contrast only on `:hover`. The skill now names state rules (`:hover`,
    `:focus`, `:active`, `:disabled`) as pairs to check, in the markup-only
    fallback too, where the first wording didn't reach: the hover plant is now
    found 2/3 with the plugin and 0/2 without, the suite's first
    accessibility uplift.
  - `reliability-review` had a bulkhead rule (a finding only with a named
    shared resource and plausible load) and nothing like it for retries,
    so runs rated a missing read retry Medium on the clean catalog module.
    A missing retry is now a finding only when a transient failure loses
    something a retry would save. `reliability-review-catalog` went from
    1/2 vs 1/2 to 2/3 vs 0/3.
  - The parent's pre-emptive design edits (gap above) stopped once the
    `tdd-implementation` and `tdd-coach` descriptions said to leave a
    design's open questions to the skill.
  - The emulated `orchestrator` case (13 dry-run directories) is replaced
    by twelve `orchestrator-route-*` cases, one per routing row, on
    planning folders cut to each stage (`fixtures/library-app/route-plants/`
    adds a non-UI cancel-hold set, a backward-route set and a screen-design
    artifact). Two lessons from calibration: an empty directory doesn't
    reach the sandbox, and an `architecture-design` run legitimately
    consults `security-requirements`, so "never invokes X" checks have to
    allow consults. Real miss found: after `scope-map` decided a problem
    needs no map, the orchestrator chained into `requirements-refinement`
    without asking (1/2). Four wordings were tried, each followed by all
    16 orchestrator cases re-run (`results/h1-*` to `h4-*`). Every one that
    stopped the chaining (15/15) also made other rows stop and ask before
    running their routed skill at all (design-system, technology-bootstrap,
    implementation; 1 or 2 runs in 2 each), and the neutral wording that
    didn't ("a no-map decision is this step's result") let the chaining
    back in (2/3). Any extra "ask" near routing spreads to every row. The
    skill is back to its committed text and the chaining stays a known
    miss: it only affects a problem small enough to need no scope map.
  - `.claude/skills/agent-eval` is retired with its last case.
- **`tdd-coach` lost its own TDD paraphrase.** Its `AGENT.md` restated the
  process from before the persona rules moved into
  `tdd-implementation`, without any of the skill's later fixes. It now
  keeps only the mandate, the no-asking rule and where output goes, and
  says to follow the skill. The agent path scored the same before and
  after (77% vs 80%), so the paraphrase wasn't the cause of the gap, but
  one source can't drift. Looking closer, the gap is smaller than the
  score: `red-runs-seen` counts runs, and the agent sees as many distinct
  tests fail as the direct path. What remains is judgment: through the
  agent, the notification question gets settled in the report instead of
  handed to its owner (3/4), likely because a background agent that can't
  ask leans toward deciding.
- **The chunk loop's steps became cases, and the first pass caught two
  real defects (v4 PR 3, 2026-10-31).**
  - `fixtures/library-app/code-plants/loop/state.sh` builds eleven states
    of the loop for real (commits, gate files, sidecar, open log entry,
    handoff), and ten `orchestrator-*` cases resume from them; the eval
    does offer the `Agent` tool, so launches are graded with `tool_used`.
    Seven more cases cover the consult under a delegation, the combined
    review's comments rule, the seam check, and three planning rules.
  - `rounds_record.py` read the first real smoke agent's report, whose
    `**Severity:**` sat in a list item, as zero findings and printed
    `smoke PASS`; the orchestrator noticed and tallied the report itself,
    which the skill forbids. The parser now tolerates a list marker, and a
    smoke report with no parsed finding must say `PASS` or the script
    exits 1. The smoke agent's instructions spell the shape out.
  - The E step never committed the log, and `delivery` stops on a dirty
    tree, so no real delivery could run; E.1 now commits the log and the
    records (handoff removed) as `Records: slice <nnn> delivery`.
  - Fixture and grader fixes from reading the runs: the gap state carries
    the reliability document its review cites; the scope-consequence
    criterion was vacuous for an in-memory queue (true after any restart),
    so it now needs the other holds to survive; the handoff is committed
    as the skill says; the readiness case hands off at the A line, since
    the skill rightly continues once the gate passes (the first run built
    chunk 1, 12 minutes, $2.76); the consult may revise its document
    through a shell script.
  - The Mac's eval sandbox cannot run `git` by name (the gate section), so
    the loop cases are recorded from WSL; the orchestrator's scripts now
    fall back to a working git.

- **Direct `tdd-implementation` runs now get the orchestrator's review, and
  `code-review` looks for code the change doesn't need.**
  - Outside the orchestrator, `tdd-implementation` ends with a final
    review: the changed files checked against the slice and the design
    doc, then `architecture-review`, `code-review`, `security-review` and
    `reliability-review` (and `accessibility-review` for UI) on those
    files, Critical and High fixed through the loop. The orchestrator's
    quarantine flow tells its instances it grades them, so they skip it.
    A `final-review-runs` trace grader on the three TDD cases passed in
    every gate run.
  - `code-review` gained "More than the change needs": unused options, a
    flag nothing sets, impossible-case checks, a catch that only
    rethrows; the fix is to delete. `code-review-days-left-pr` plants all
    four. The skill wasn't firing at all on a plain "review it before I
    merge": its description led with scope and named readability as the
    trigger. Leading with "invoke first" and the general-review trigger
    got it to 2/3.
  - These changes were the eval gate's first real use: it picked 26
    affected cases from the diff (code-review, orchestrator, TDD and one
    negative) and all 26 met their bars.
