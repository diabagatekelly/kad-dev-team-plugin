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
| `chunk-runner-replay-not-the-handback` | new 2026-11-13 (E2, "Replay cases"): resumes a real runner's transcript at "Waiting for the builder's hand-back."; the next turn is a background-task notification for another agent, a sibling's build of chunk 2 with a commit of its own. The sibling's commit is never on the runner's line and chunk 1 is never reported built on it; nothing is started to poll. Bar 1.00 at three runs. |
| `chunk-runner-replay-unheld-commit` | new 2026-11-13 (E2, "Replay cases"): the same history; the next turn is the builder's real hand-back naming `72ba4bb`, which the replayed repository does not hold. The runner checks the hash against the repository and never puts it on its line. Bar 1.00 at three runs. |
| `orchestrator-runner-handback-unverified` | new 2026-11-12 (0.14.5, finding 1, answer key L11): the `chunk1-handback-phantom` state, a runner's line naming an r1 fix commit the repository does not hold; the orchestrator checks the line with `git cat-file -e`, writes no C line and no records commit from it, launches nothing (the prompt forbids a launch), and hands off with the runner's relaunch as the next action. 1.00 in 3/3 twice (`results/gate-20261112T2242*`); bar recorded from it | yes |
| `delivery-ci-red-not-done` | new 2026-11-12 (0.14.5, finding 2, incident 33, answer key L12): the `delivery-ci-red` state, resumed at E.4 with pull request #7's check failing on the pushed commit; the checks read, the failing job read with `gh run view --log-failed`, the failing tests and the platform difference written to `pr-ci-r1.md`, no E line that says clean or green, the report opening with the CI state and "not ready", the handoff briefing one fresh fixer with the platform difference and the not-weakened rule. Bounded before the fixer (the prompt forbids a launch): the fix, the push, the second watch and the three-round cap are not run by any case. First round errored on the graders (an inline `(?m)` flag the eval's regex engine refuses; a `Write` call expected where the runs wrote the file with a shell heredoc); 0.97 in 3/3 after (`results/gate-20261112T2242*`); bar recorded from it | yes |
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
| `problem-framing-doc-payfine` | real, Sonnet: 14/15 over 3 runs; the baseline passed in calibration, a regression guard — the user's own description with "add a pay button" in it: no solution in the doc, Stripe and one-developer as constraints. Known miss 1/3: an unstated "in-person payment must keep working" listed as a constraint beside a related open question | yes |
| `scope-map-self-service` | real, Sonnet: 14/15 over 3 runs; the miss is borderline, not a clear judge error: the map routes privacy to each step's requirements pass, but through one blanket line covering its whole cross-cutting list. The eval's judge failed it 3/3; `tools/rejudge.py` passes it 8/8, which is a hint only. Baseline misses the privacy routing on both calibration passes — a new, larger problem (`planning/self-service/`: fines, holds, contact details) whose privacy constraint is worded around one step. Phase E (2026-10-15): the problem doc's sentence generalising the privacy constraint for the skill is gone; privacy still routed to every step's requirements pass, 15/15 | yes |
| `user-story-writeup-payfine-phase1` | real, Sonnet: 9/9 over 3 runs; baseline fails on both calibration passes (writes the story or fills the security placeholder) — asked to make slice 1 "ready to track", asks whether and where to file before writing. Before the fix the skill never fired: the run filled the slice's security placeholder instead | yes |
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
| `library-app-members-review` | real, Sonnet: 3/3 with plugin vs 2/3 without (table-shaped domain type missed), 1 run — backward-check contamination located in the port file, table-shaped domain type, date-library trap | yes |
| `library-app-fines-review` | real, Sonnet: 4/4 with plugin vs 2/4 without (policy-mixed-with-mechanics and the premature strategy interface missed), 1 run | yes |
| `library-app-notifications-review` | real, Sonnet: 3/3 both arms, 1 run — missing channel abstraction, port on the implementer's side, one-impl-port-over-I/O trap | yes |
| `library-app-reporting-review` | real, Sonnet: 3/3 with plugin vs 2/3 without after one skill fix, 1 run each — SQL-level port and SDK in a report found by both arms; the orchestration-mixed-with-CSV smell was missed by both arms in every Sonnet run until the skill's "inconsistent abstraction level" smell gained a concrete check (a method that calls collaborators and also handles characters/delimiters/encodings is at two levels); re-run `results/20261009-220715-sonnet3-reporting-review` passes with the plugin, the baseline still misses it | yes |
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
| `security-review-http` | real, Sonnet: 3/3 plants + 2/2 traps with plugin, 1 run — refund route outside every auth prefix, internal error text to callers, request headers/bodies to monitoring; traps: prefix-mounted staff auth, public catalog search. Baseline missed the error-text finding | yes |
| `security-review-portal-pr` | real, Sonnet: 5/5 with plugin, 1 run — member-profile IDOR, SQL injection in history search, PR scoping of pre-existing problems; traps: session-scoped routes, prefix-mounted member auth | yes |
| `security-review-config` | real, Sonnet: 5/5 with plugin, 1 run — hardcoded SendGrid fallback key (rotation required), long-lived AWS keys beside an OIDC job, workflow-wide secrets; traps: Stripe publishable key, `id-token: write`. Baseline called the publishable key a leaked secret | yes |
| `security-review-reminders` | real, Sonnet: 3/3 with plugin vs 1/3 without, 1 run — whole member object logged, real-looking PII in test fixtures; trap: identifier-only log line. Phase E (2026-10-15): "Pay attention to how member data is handled" dropped from the prompt; 3/3 runs, both plants found | yes |
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
| `reliability-review-alerts` | real, Sonnet: 3/3 both arms, 1 run (`results/g3-*`; was 3/3 vs 2/3) — page on any error event, non-actionable CPU page; trap: multi-window burn-rate alerts with a runbook. Now a regression guard | yes |
| `reliability-review-portal-pay-pr` | real, Sonnet: 3/3 runs clean, 24/24 (`results/gate-20261018T160908`) — G1 (2026-10-18), the first plant whose defect only shows across files (overlay `code-plants/reliability-review/portal-pay/`, answer key R14, R15, RT10, RT11): a PR adding pay-a-fine to the portal, whose use case charges with an idempotency key the port's comment promises will stop a repeat charge, while the Stripe adapter sends it as a `metadata` label the SDK types say Stripe never reads; the route's "please try again" on a timeout then double-charges. Every run read both sides and the vendor types, found the key ineffective and the charge abandoned at the timeout, and left the bounded wait and the shared 404 alone. No baseline arm | yes |
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
Written by `tools/case_history.py` on 2026-11-14 from 6339 result files under `results/`, `kad-eval-results-archive/`: 3902 plugin-arm runs, 2026-10-31 to 2026-11-14. 675 of them errored before any grader ran (usage limit 665, sign-in 8, results folder over the entry limit 2); 127 grader results threw for a reason outside the run (usage limit 98, interrupted 16, grader pattern does not compile 13).

| Case | Bar since | Completed runs | Since the bar | Failed | Graders that failed (runs) | Last failure | Errored, thrown |
|---|---|---|---|---|---|---|---|
| `acceptance-criteria-payfine` | 2026-10-11 | 11 | 11 | 0 |  |  | 1, 1 |
| `accessibility-review-ac-walk` | 2026-11-09 | 18 | 14 | 1 | `honest-about-what-was-driven` (judge) ×1 | 2026-11-11 | 0, 0 |
| `accessibility-review-neg-readability` | 2026-10-11 | 13 | 13 | 0 |  |  | 0, 0 |
| `accessibility-review-payfine` | 2026-10-11 | 19 | 19 | 5 | `slice-placeholder-filled` (judge) ×4, `criteria-split-now-and-later` (judge) ×1 | 2026-11-11 | 3, 2 |
| `accessibility-review-payfine-subtle` | 2026-10-11 | 19 | 19 | 5 | `slice-placeholder-filled` (judge) ×4, `no-false-alarm-card-number-label` (judge) ×1 | 2026-11-11 | 0, 4 |
| `adr-neg-rename` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `adr-payment-gateway` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `architecture-design-neg-review` | 2026-10-11 | 17 | 17 | 0 |  |  | 0, 0 |
| `architecture-design-owner-sheet` | 2026-11-09 | 27 | 13 | 0 |  |  | 3, 2 |
| `architecture-design-payfine-phase1` | 2026-10-11 | 24 | 24 | 0 |  |  | 0, 2 |
| `architecture-design-payfine-phase2` | 2026-10-11 | 25 | 25 | 20 | `decisions-show-approval` (judge) ×19, `stays-conceptual` (judge) ×2, `builds-on-the-existing-payment-path` (judge) ×1, `notes-the-leaky-payment-port` (judge) ×1, `keeps-the-one-implementation-port` (judge) ×1 | 2026-11-12 | 0, 6 |
| `architecture-design-payfine-via-agent` | 2026-10-11 | 15 | 15 | 0 |  |  | 0, 4 |
| `architecture-design-scope-consequence` | 2026-10-31 | 41 | 34 | 15 | `hands-back-to-the-requirements-owner` (judge) ×12, `does-not-approve-around-it` (judge) ×10 | 2026-11-11 | 0, 4 |
| `architecture-review-neg-security-review` | 2026-10-12 | 12 | 12 | 0 |  |  | 0, 0 |
| `architecture-review-neg-test-quality-review` | 2026-10-12 | 13 | 13 | 0 |  |  | 0, 0 |
| `chunk-runner-gap-handback` | 2026-11-09 | 27 | 23 | 8 | `stops-with-the-decision-on-the-line` (judge) ×8 | 2026-11-13 | 3, 0 |
| `chunk-runner-gate-deviation` | 2026-11-09 | 21 | 17 | 0 |  |  | 3, 0 |
| `chunk-runner-gate-outside` | 2026-11-09 | 19 | 15 | 0 |  |  | 2, 0 |
| `chunk-runner-gate-sources` | 2026-11-09 | 27 | 13 | 1 | `hands-back-pass-after-the-fix-and-stops` ×1 | 2026-11-11 | 8, 0 |
| `chunk-runner-one-fix-round` | 2026-11-09 | 25 | 21 | 5 | `hand-back-is-the-one-line` (judge) ×5 | 2026-11-12 | 2, 0 |
| `chunk-runner-replay-not-the-handback` | 2026-11-13 | 13 | 7 | 0 |  |  | 0, 0 |
| `chunk-runner-replay-unheld-commit` | 2026-11-13 | 13 | 7 | 0 |  |  | 0, 1 |
| `chunk-runner-review-round` | 2026-11-09 | 20 | 16 | 1 | `hand-back-line-carries-the-script-counts` ×1, `round-recorded-by-the-script` ×1, `smoke-report-written` ×1, `review-report-written` ×1, `one-smoke-agent` ×1, `two-launches-never-more` ×1, and 5 more | 2026-11-11 | 2, 0 |
| `chunk-runner-waits-for-handback` | 2026-11-12 | 8 | 5 | 2 | `hand-back-is-the-one-line-for-what-ran` (judge) ×2 | 2026-11-12 | 0, 0 |
| `code-review-catalog` | 2026-10-11 | 19 | 19 | 9 | `nothing-above-low` (judge) ×9 | 2026-11-11 | 4, 2 |
| `code-review-comments-chunk` | 2026-10-31 | 37 | 36 | 17 | `hands-back-counts-and-path` (judge) ×12, `reliability-lens-invoked-for-storage` ×9, `test-quality-lens-invoked` ×8, `why-comment-is-not-flagged` (judge) ×2, `report-written` ×1, `what-comments-are-a-medium` ×1, and 2 more | 2026-11-12 | 8, 8 |
| `code-review-days-left-pr` | 2026-10-11 | 10 | 10 | 0 |  |  | 1, 0 |
| `code-review-fine-notices-pr` | 2026-10-11 | 13 | 13 | 7 | `leaves-mocking-to-test-quality-review` (judge) ×5, `consults-why-comments` ×2, `finds-wrong-name` (judge) ×1 | 2026-11-12 | 1, 0 |
| `code-review-fine-notices-pr-via-agent` | 2026-10-11 | 20 | 20 | 19 | `consults-why-comments` ×18, `leaves-mocking-to-test-quality-review` (judge) ×16 | 2026-11-12 | 1, 7 |
| `code-review-fines-report-pr` | 2026-10-11 | 13 | 13 | 2 | `hands-sdk-to-architecture-review` (judge) ×2, `finds-feature-envy` (judge) ×1 | 2026-11-11 | 4, 0 |
| `code-review-neg-architecture` | 2026-10-11 | 11 | 11 | 0 |  |  | 1, 0 |
| `code-review-structural-high-at-d` | 2026-11-11 | 7 | 5 | 4 | `a-long-single-job-function-stays-a-plain-finding` (judge) ×4 | 2026-11-12 | 1, 0 |
| `delegation-consult-with-file` | 2026-10-31 | 18 | 11 | 4 | `hands-back-the-hash-and-one-sentence` (judge) ×3, `decision-written-in-place-under-the-delegation` (judge) ×1 | 2026-11-09 | 1, 0 |
| `delegation-consult-without-file` | 2026-10-31 | 20 | 19 | 4 | `recommendation-only-named-as-undelegated` (judge) ×4 | 2026-11-12 | 4, 0 |
| `delivery-ci-red-not-done` | 2026-11-12 | 10 | 7 | 2 | `report-leads-with-red-ci-and-not-ready` (judge) ×1, `handoff-briefs-the-fixer` (judge) ×1 | 2026-11-13 | 0, 6 |
| `design-system-payfine-phase1` | 2026-10-11 | 7 | 7 | 0 |  |  | 1, 0 |
| `design-system-payfine-phase2` | 2026-10-11 | 7 | 7 | 0 |  |  | 1, 2 |
| `design-system-payfine-phase3` | 2026-10-11 | 12 | 12 | 5 | `accessibility-by-construction` (judge) ×5 | 2026-11-11 | 5, 0 |
| `design-system-payfine-reference` | 2026-10-17 | 6 | 6 | 1 | `mock-carries-reference-brand` ×1 | 2026-11-11 | 5, 0 |
| `design-system-payfine-review` | 2026-10-17 | 7 | 7 | 0 |  |  | 1, 4 |
| `external-review-triage-cancel-hold` | 2026-10-24 | 6 | 6 | 0 |  |  | 0, 0 |
| `library-app-catalog-review` | 2026-10-11 | 14 | 14 | 3 | `reports-nothing-above-low` (judge) ×3 | 2026-11-09 | 8, 0 |
| `library-app-fines-review` | 2026-10-11 | 9 | 9 | 0 |  |  | 3, 0 |
| `library-app-lending-review` | 2026-10-11 | 15 | 15 | 4 | `finds-orm-inside-checkout-use-case` (judge) ×4 | 2026-11-11 | 6, 0 |
| `library-app-lending-review-via-agent` | 2026-10-11 | 12 | 12 | 1 | `finds-orm-inside-checkout-use-case` (judge) ×1 | 2026-11-09 | 3, 0 |
| `library-app-members-review` | 2026-10-11 | 9 | 9 | 0 |  |  | 3, 0 |
| `library-app-notifications-review` | 2026-10-11 | 9 | 9 | 0 |  |  | 3, 0 |
| `library-app-reporting-pr` | 2026-10-11 | 9 | 9 | 0 |  |  | 3, 0 |
| `library-app-reporting-review` | 2026-10-11 | 9 | 9 | 0 |  |  | 3, 0 |
| `library-app-structure-review` | 2026-10-11 | 9 | 9 | 0 |  |  | 3, 0 |
| `map-query-consults` | 2026-10-11 | 8 | 8 | 0 |  |  | 3, 0 |
| `map-query-no-map` | 2026-10-11 | 2 | 2 | 0 |  |  | 1, 0 |
| `map-update-cancel-hold` | 2026-10-11 | 18 | 18 | 17 | `pre-existing-flags-not-new` (judge) ×13, `no-bash-writes` ×6, `keeps-existing-rows-and-tiers` (judge) ×5 | 2026-11-11 | 3, 0 |
| `operational-readiness-neg-reliability` | 2026-10-11 | 11 | 11 | 0 |  |  | 3, 0 |
| `operational-readiness-neg-security` | 2026-10-11 | 10 | 10 | 0 |  |  | 3, 0 |
| `operational-readiness-ops-phase1` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `operational-readiness-ops-phase2` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `operational-readiness-release-phase1` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `operational-readiness-release-phase2` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `orchestrator-asks-for-target` | 2026-10-11 | 38 | 38 | 0 |  |  | 4, 0 |
| `orchestrator-backward-route` | 2026-10-11 | 49 | 49 | 19 | `routes-back-to-the-owner` (judge) ×14, `log-names-the-hand-back` (judge) ×8, `does-not-go-forward-to-reliability` ×3, `invokes-vertical-slicing` ×3 | 2026-11-12 | 11, 2 |
| `orchestrator-budget-exceeded` | 2026-10-31 | 44 | 40 | 26 | `flow-ends-saying-what-is-built` (judge) ×26 | 2026-11-13 | 6, 1 |
| `orchestrator-chunk-runner-handback` | 2026-11-09 | 22 | 19 | 0 |  |  | 5, 1 |
| `orchestrator-chunk-runner-launch` | 2026-11-09 | 41 | 38 | 14 | `handoff-says-the-runner-is-in-flight` (judge) ×14 | 2026-11-12 | 12, 1 |
| `orchestrator-definition-of-done` | 2026-10-31 | 65 | 58 | 51 | `three-named-fixes-in-one-batch` (judge) ×50, `one-fixer-for-the-batch` ×20, `no-slice-reviewer-yet` ×11, `gate-on-the-fix` ×11, `readme-written` ×3, `readme-skill-invoked-inline` ×3, and 4 more | 2026-11-13 | 19, 0 |
| `orchestrator-delivery-foreground` | 2026-10-31 | 70 | 66 | 26 | `cost-script-run` ×19, `reports-the-delivery-in-the-same-turn` (judge) ×11, `pr-writeup-invoked` ×7, `pull-request-then-issues-then-body-edit` ×6, `one-issue-per-standing-medium-none-for-a-low` (judge) ×5, `e-line-written` ×4 | 2026-11-12 | 6, 0 |
| `orchestrator-delivery-removal` | 2026-11-09 | 34 | 20 | 2 | `record-names-counts-and-files-never-values` (judge) ×2 | 2026-11-10 | 7, 0 |
| `orchestrator-gap-without-delegation` | 2026-10-31 | 59 | 55 | 12 | `round-zero-not-recorded-again` ×9, `stops-for-the-owner-with-the-recommendation` (judge) ×5, `owning-persona-launched-once` ×2, `needs-decision-on-the-c-line` ×2 | 2026-11-12 | 10, 0 |
| `orchestrator-issue-fix-records` | 2026-11-12 | 7 | 4 | 1 | `branch-names-the-slice-and-the-issue` ×1 | 2026-11-12 | 0, 6 |
| `orchestrator-plan-check-seam` | 2026-10-31 | 47 | 43 | 1 | `plan-sent-back-not-edited` (judge) ×1 | 2026-11-11 | 7, 0 |
| `orchestrator-readiness-gate` | 2026-10-31 | 65 | 61 | 15 | `backward-routes-name-the-checks` (judge) ×13, `stops-at-the-routed-skill-or-reports-the-route` (judge) ×5, `readiness-gate-run-by-the-script` ×4, `a-line-carries-session-and-audit` ×4, `first-failed-check-routed-inline` ×4, `gate-before-the-routed-skill` ×4, and 1 more | 2026-11-11 | 8, 0 |
| `orchestrator-readiness-open-item` | 2026-11-09 | 33 | 30 | 6 | `puts-the-blocker-to-the-owner` (judge) ×6 | 2026-11-11 | 5, 0 |
| `orchestrator-readiness-sources` | 2026-11-09 | 30 | 17 | 0 |  |  | 7, 0 |
| `orchestrator-readme-stale-not-done` | 2026-11-11 | 8 | 6 | 5 | `three-named-fixes-in-one-batch` (judge) ×5, `one-fixer-for-the-batch` ×1, `gate-on-the-fix` ×1 | 2026-11-13 | 5, 1 |
| `orchestrator-route-accessibility` | 2026-10-11 | 54 | 54 | 11 | `log-names-row-and-artifact` (judge) ×6, `screen-design-only-after-the-review` ×3, `stops-after-the-routed-step` (judge) ×2, `not-screen-design` ×1 | 2026-11-11 | 12, 2 |
| `orchestrator-route-backward-requirements` | 2026-10-11 | 40 | 40 | 4 | `log-names-row-and-artifact` (judge) ×4, `stops-after-the-routed-step` (judge) ×2, `routes-to-requirements-refinement` ×2 | 2026-11-13 | 8, 0 |
| `orchestrator-route-design` | 2026-10-11 | 38 | 38 | 1 | `stops-after-the-routed-step` (judge) ×1 | 2026-10-31 | 8, 0 |
| `orchestrator-route-design-system` | 2026-10-11 | 36 | 36 | 0 |  |  | 8, 0 |
| `orchestrator-route-implementation` | 2026-10-11 | 42 | 42 | 2 | `stops-after-the-routed-step` (judge) ×2 | 2026-11-01 | 8, 0 |
| `orchestrator-route-implementation-prenamed` | 2026-10-18 | 38 | 38 | 1 | `routes-to-tdd-implementation-lite` (judge) ×1 | 2026-11-09 | 8, 0 |
| `orchestrator-route-open-pr` | 2026-11-09 | 21 | 18 | 0 |  |  | 5, 0 |
| `orchestrator-route-problem-framing` | 2026-10-11 | 37 | 37 | 1 | `stops-after-the-routed-step` (judge) ×1 | 2026-11-11 | 9, 0 |
| `orchestrator-route-reliability` | 2026-10-11 | 45 | 45 | 5 | `log-names-row-and-artifact` (judge) ×5, `stops-after-the-routed-step` (judge) ×2, `routes-to-reliability-requirements` ×2 | 2026-11-11 | 8, 1 |
| `orchestrator-route-scope-decision` | 2026-10-11 | 111 | 111 | 63 | `stops-after-the-routed-step` (judge) ×63, `not-requirements-refinement` ×3 | 2026-11-12 | 17, 6 |
| `orchestrator-route-screen-design` | 2026-10-11 | 51 | 51 | 13 | `stops-after-the-routed-step` (judge) ×6, `log-names-row-and-artifact` (judge) ×6, `not-accessibility-review` ×2, `accessibility-review-only-after-screen-design` ×1 | 2026-11-11 | 11, 0 |
| `orchestrator-route-slicer-accessibility-mistake` | 2026-11-01 | 38 | 35 | 1 | `routes-back-to-the-slicer` ×1, `log-names-the-mismatch` (judge) ×1 | 2026-11-09 | 9, 0 |
| `orchestrator-route-slicing` | 2026-10-11 | 50 | 50 | 6 | `stops-after-the-routed-step` (judge) ×6, `not-user-story-writeup` ×4 | 2026-11-01 | 9, 2 |
| `orchestrator-route-tech-bootstrap` | 2026-10-11 | 39 | 39 | 2 | `log-names-row-and-artifact` (judge) ×2 | 2026-11-11 | 11, 1 |
| `orchestrator-route-user-story` | 2026-10-11 | 41 | 41 | 4 | `stops-after-the-routed-step` (judge) ×3, `routes-to-user-story-writeup` ×3, `log-names-row-and-artifact` ×1, `log-written` ×1, `not-vertical-slicing` ×1 | 2026-11-11 | 10, 2 |
| `orchestrator-runner-handback-unverified` | 2026-11-12 | 7 | 4 | 0 |  |  | 0, 0 |
| `orchestrator-security-stage` | 2026-10-11 | 36 | 36 | 0 |  |  | 11, 0 |
| `orchestrator-session-setup` | 2026-11-01 | 40 | 40 | 8 | `not-problem-framing-doc-yet` ×5, `asks-about-the-session-first` (judge) ×5, `routes-to-problem-framing-doc` ×3, `asks-nothing-about-the-session` (judge) ×3 | 2026-11-09 | 10, 0 |
| `orchestrator-superseded-scope-map` | 2026-10-11 | 36 | 36 | 0 |  |  | 11, 0 |
| `pr-writeup-portal-fines` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `problem-framing-doc-payfine` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `reliability-requirements-neg-review` | 2026-10-11 | 12 | 12 | 0 |  |  | 5, 0 |
| `reliability-requirements-payfine-phase1` | 2026-10-11 | 4 | 4 | 0 |  |  | 0, 0 |
| `reliability-requirements-payfine-phase2` | 2026-10-11 | 3 | 3 | 0 |  |  | 0, 0 |
| `reliability-requirements-payfine-phase2-proceed` | 2026-10-18 | 3 | 3 | 0 |  |  | 0, 0 |
| `reliability-requirements-payfine-phase2-stop` | 2026-10-17 | 3 | 3 | 1 | `does-not-lay-out-scope-options` (judge) ×1 | 2026-11-01 | 0, 0 |
| `reliability-requirements-payfine-phase3` | 2026-10-11 | 3 | 3 | 0 |  |  | 0, 0 |
| `reliability-review-alerts` | 2026-10-11 | 15 | 15 | 1 | `no-false-alarm-burn-rate-alerts` (judge) ×1 | 2026-11-11 | 5, 0 |
| `reliability-review-catalog` | 2026-10-11 | 18 | 18 | 6 | `reports-nothing-above-low` (judge) ×6 | 2026-11-12 | 11, 0 |
| `reliability-review-fine-payment` | 2026-10-11 | 15 | 15 | 1 | `no-false-alarm-settled-fine-guard` (judge) ×1 | 2026-11-12 | 5, 0 |
| `reliability-review-http` | 2026-10-11 | 12 | 12 | 0 |  |  | 5, 0 |
| `reliability-review-neg-architecture` | 2026-10-11 | 12 | 12 | 0 |  |  | 5, 0 |
| `reliability-review-neg-security` | 2026-10-11 | 13 | 13 | 0 |  |  | 5, 0 |
| `reliability-review-nightly` | 2026-10-11 | 21 | 21 | 7 | `no-false-alarm-sms-retry` (judge) ×6, `finds-no-isolation-in-fine-loop` (judge) ×1 | 2026-11-11 | 5, 0 |
| `reliability-review-nightly-via-agent` | 2026-10-11 | 19 | 19 | 6 | `no-false-alarm-sms-retry` (judge) ×6 | 2026-11-11 | 8, 0 |
| `reliability-review-portal-pay-pr` | 2026-10-18 | 12 | 12 | 0 |  |  | 5, 0 |
| `reliability-review-refund-pr` | 2026-11-07 | 16 | 15 | 1 | `no-false-alarm-timeout-is-reported` (judge) ×1 | 2026-11-09 | 5, 0 |
| `requirements-refinement-open-question` | 2026-10-31 | 11 | 10 | 0 |  |  | 2, 0 |
| `requirements-refinement-owner-sheet` | 2026-11-09 | 22 | 9 | 0 |  |  | 2, 0 |
| `requirements-refinement-payfine-phase1` | 2026-10-11 | 12 | 12 | 3 | `does-not-ask-what-the-sources-answer` (judge) ×3 | 2026-11-11 | 5, 0 |
| `requirements-refinement-payfine-phase2` | 2026-10-11 | 9 | 9 | 8 | `finishes-without-reasking` (judge) ×8 | 2026-11-12 | 2, 0 |
| `scope-map-self-service` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `screen-design-owner-sheet` | 2026-11-09 | 19 | 9 | 0 |  |  | 5, 0 |
| `screen-design-payfine` | 2026-10-11 | 8 | 8 | 2 | `copy-rules` (judge) ×2 | 2026-11-11 | 3, 0 |
| `security-requirements-neg-review` | 2026-10-11 | 10 | 10 | 0 |  |  | 3, 0 |
| `security-requirements-payfine-phase1` | 2026-10-11 | 12 | 12 | 0 |  |  | 2, 0 |
| `security-requirements-payfine-phase2` | 2026-10-11 | 14 | 14 | 3 | `does-not-decide-the-fork-itself` (judge) ×3 | 2026-11-12 | 5, 0 |
| `security-requirements-payfine-phase2-proceed` | 2026-10-18 | 9 | 9 | 0 |  |  | 2, 0 |
| `security-requirements-payfine-phase2-stop` | 2026-10-17 | 9 | 9 | 0 |  |  | 2, 0 |
| `security-requirements-payfine-phase3` | 2026-10-11 | 15 | 15 | 13 | `decisions-all-approved` (judge) ×10, `criterion-card-details-never-reach-the-server` (judge) ×4 | 2026-11-12 | 5, 0 |
| `security-requirements-placeholder-pointer` | 2026-10-31 | 11 | 10 | 0 |  |  | 2, 0 |
| `security-requirements-source-criterion` | 2026-11-09 | 19 | 9 | 0 |  |  | 5, 0 |
| `security-review-catalog` | 2026-10-11 | 13 | 13 | 1 | `reports-nothing-above-low` (judge) ×1 | 2026-11-09 | 3, 0 |
| `security-review-config` | 2026-10-11 | 10 | 10 | 0 |  |  | 4, 0 |
| `security-review-http` | 2026-10-11 | 10 | 10 | 0 |  |  | 4, 0 |
| `security-review-neg-architecture` | 2026-10-11 | 10 | 10 | 0 |  |  | 3, 0 |
| `security-review-neg-reliability` | 2026-10-11 | 13 | 13 | 0 |  |  | 5, 0 |
| `security-review-portal-pr` | 2026-10-11 | 16 | 16 | 3 | `pre-existing-issues-not-blocking` (judge) ×3 | 2026-11-11 | 4, 0 |
| `security-review-reminders` | 2026-10-11 | 10 | 10 | 0 |  |  | 4, 0 |
| `security-review-source-value` | 2026-11-09 | 16 | 9 | 0 |  |  | 6, 0 |
| `staleness-audit-docs` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `supply-chain-review-accept-phase1` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `supply-chain-review-accept-phase2` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `supply-chain-review-accepted` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `supply-chain-review-build` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `supply-chain-review-build-via-agent` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `supply-chain-review-neg-reliability` | 2026-10-11 | 11 | 11 | 0 |  |  | 5, 0 |
| `supply-chain-review-neg-security` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `supply-chain-review-workflows` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `tdd-implementation-lite-cancel-hold` | 2026-10-18 | 15 | 15 | 15 | `test-run-after-each-test-edit` ×15, `tests-check-behaviour` (judge) ×1 | 2026-11-12 | 9, 0 |
| `tdd-implementation-lite-cancel-hold-via-agent` | 2026-10-18 | 30 | 30 | 30 | `test-run-after-each-test-edit` ×30, `final-review-runs` ×11, `escalates-queue-question` (judge) ×7, `tests-check-behaviour` (judge) ×4, `break-and-restore-in-trace` ×2, `no-bash-writes` ×1, and 2 more | 2026-11-12 | 6, 0 |
| `tdd-implementation-lite-chunk-plan` | 2026-10-24 | 19 | 19 | 11 | `plan-is-vertical-and-inside-the-slice` (judge) ×8, `plan-has-the-shape` (judge) ×5 | 2026-11-12 | 5, 0 |
| `tdd-implementation-lite-named-fix` | 2026-10-18 | 25 | 25 | 7 | `final-review-runs` ×6, `no-bash-writes` ×1 | 2026-11-11 | 12, 0 |
| `tdd-implementation-lite-one-chunk` | 2026-11-07 | 19 | 19 | 4 | `ends-on-the-hand-back-line` (judge) ×4, `no-bash-writes` ×1 | 2026-11-13 | 3, 0 |
| `tdd-implementation-lite-rename-fix` | 2026-11-02 | 22 | 22 | 3 | `no-shell-writes-into-the-tree` ×3 | 2026-11-09 | 6, 0 |
| `technology-bootstrap-phase1` | 2026-10-11 | 10 | 10 | 1 | `asks-only-what-the-first-test-forces` (judge) ×1 | 2026-11-11 | 7, 0 |
| `technology-bootstrap-phase2` | 2026-10-11 | 19 | 19 | 7 | `asks-only-what-the-first-test-forces` (judge) ×5, `recommends-the-built-in-default-set-once` (judge) ×1, `recommends-ui-framework-and-waits` (judge) ×1 | 2026-11-11 | 4, 0 |
| `technology-bootstrap-phase3` | 2026-10-11 | 16 | 16 | 9 | `records-non-choices-and-open-categories` (judge) ×9, `records-the-built-in-default-set` (judge) ×2, `writes-nothing-else` ×1 | 2026-11-11 | 4, 0 |
| `technology-bootstrap-phase3-reject` | 2026-10-14 | 11 | 11 | 6 | `does-not-relitigate` (judge) ×5, `asks-only-what-the-first-test-forces` (judge) ×1 | 2026-11-11 | 4, 0 |
| `test-quality-review-fines` | 2026-10-11 | 18 | 18 | 9 | `no-false-alarm-fake-ledger` (judge) ×6, `no-false-alarm-exact-tests` (judge) ×5 | 2026-11-12 | 6, 2 |
| `test-quality-review-neg-code-review` | 2026-10-11 | 11 | 11 | 0 |  |  | 3, 0 |
| `test-quality-review-reminders` | 2026-10-11 | 12 | 12 | 0 |  |  | 3, 1 |
| `test-quality-review-seam-fake` | 2026-10-31 | 24 | 20 | 0 |  |  | 6, 4 |
| `user-facing-docs-renewals` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `user-story-writeup-payfine-phase1` | 2026-10-11 | 7 | 7 | 0 |  |  | 3, 0 |
| `user-story-writeup-payfine-phase2` | 2026-10-11 | 0 | 0 | 0 |  |  | 0, 0 |
| `vertical-slicing-handback` | 2026-10-11 | 11 | 11 | 0 |  |  | 4, 0 |
| `vertical-slicing-no-requirements` | 2026-10-11 | 11 | 11 | 0 |  |  | 4, 0 |
| `vertical-slicing-no-screen` | 2026-11-01 | 20 | 17 | 1 | `accessibility-line-matches-the-thin-path` (judge) ×1 | 2026-11-01 | 4, 0 |
| `vertical-slicing-owner-sheet` | 2026-11-09 | 25 | 18 | 2 | `consults-acceptance-criteria` ×2 | 2026-11-11 | 6, 1 |
| `vertical-slicing-payfine-phase1` | 2026-10-11 | 11 | 11 | 0 |  |  | 4, 1 |
| `why-comments-collect-fine` | 2026-10-11 | 4 | 4 | 0 |  |  | 0, 3 |

Of 166 cases, 78 have failed at least once since their bar (however few their runs), 62 never have over 6 or more completed runs, and 26 have not failed but have fewer than 6 runs to go by.

**Never failed since the bar (62):** `acceptance-criteria-payfine`, `accessibility-review-neg-readability`, `architecture-design-neg-review`, `architecture-design-owner-sheet`, `architecture-design-payfine-phase1`, `architecture-design-payfine-via-agent`, `architecture-review-neg-security-review`, `architecture-review-neg-test-quality-review`, `chunk-runner-gate-deviation`, `chunk-runner-gate-outside`, `chunk-runner-replay-not-the-handback`, `chunk-runner-replay-unheld-commit`, `code-review-days-left-pr`, `code-review-neg-architecture`, `design-system-payfine-phase1`, `design-system-payfine-phase2`, `design-system-payfine-review`, `external-review-triage-cancel-hold`, `library-app-fines-review`, `library-app-members-review`, `library-app-notifications-review`, `library-app-reporting-pr`, `library-app-reporting-review`, `library-app-structure-review`, `map-query-consults`, `operational-readiness-neg-reliability`, `operational-readiness-neg-security`, `orchestrator-asks-for-target`, `orchestrator-chunk-runner-handback`, `orchestrator-readiness-sources`, `orchestrator-route-design-system`, `orchestrator-route-open-pr`, `orchestrator-security-stage`, `orchestrator-superseded-scope-map`, `reliability-requirements-neg-review`, `reliability-review-http`, `reliability-review-neg-architecture`, `reliability-review-neg-security`, `reliability-review-portal-pay-pr`, `requirements-refinement-open-question`, `requirements-refinement-owner-sheet`, `screen-design-owner-sheet`, `security-requirements-neg-review`, `security-requirements-payfine-phase1`, `security-requirements-payfine-phase2-proceed`, `security-requirements-payfine-phase2-stop`, `security-requirements-placeholder-pointer`, `security-requirements-source-criterion`, `security-review-config`, `security-review-http`, `security-review-neg-architecture`, `security-review-neg-reliability`, `security-review-reminders`, `security-review-source-value`, `supply-chain-review-neg-reliability`, `test-quality-review-neg-code-review`, `test-quality-review-reminders`, `test-quality-review-seam-fake`, `user-story-writeup-payfine-phase1`, `vertical-slicing-handback`, `vertical-slicing-no-requirements`, `vertical-slicing-payfine-phase1`.

**Too few runs to say (26, no failure in under 6 runs):** `adr-neg-rename`, `adr-payment-gateway`, `map-query-no-map`, `operational-readiness-ops-phase1`, `operational-readiness-ops-phase2`, `operational-readiness-release-phase1`, `operational-readiness-release-phase2`, `orchestrator-runner-handback-unverified`, `pr-writeup-portal-fines`, `problem-framing-doc-payfine`, `reliability-requirements-payfine-phase1`, `reliability-requirements-payfine-phase2`, `reliability-requirements-payfine-phase2-proceed`, `reliability-requirements-payfine-phase3`, `scope-map-self-service`, `staleness-audit-docs`, `supply-chain-review-accept-phase1`, `supply-chain-review-accept-phase2`, `supply-chain-review-accepted`, `supply-chain-review-build`, `supply-chain-review-build-via-agent`, `supply-chain-review-neg-security`, `supply-chain-review-workflows`, `user-facing-docs-renewals`, `user-story-writeup-payfine-phase2`, `why-comments-collect-fine`.

**In the history with no case directory now (10, retired or renamed, not in the table):** `orchestrator-chunk-review-round`, `orchestrator-gate-deviation`, `orchestrator-gate-outside`, `orchestrator-one-fix-round`, `probe-sandbox`, `tdd-implementation-cancel-hold`, `tdd-implementation-cancel-hold-via-agent`, `tdd-implementation-chunk-plan`, `tdd-implementation-named-fix`, `tdd-implementation-one-chunk`.
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
Written by `tools/case_sort.py` on 2026-11-14 from the cases, `tools/case_reading.json` and the results under `results/`, `kad-eval-results-archive/`; cost and time are means over the completed runs since 2026-11-10 (`*`: no run since, every held run).

| Case | Skill | Tool checks | Judges | A tool could decide | Prompt states the rule | Agent $ | Judges $ | Seconds (agent + judges) | Failed since the bar | Deletions that failed it |
|---|---|---|---|---|---|---|---|---|---|---|
| `acceptance-criteria-payfine` | acceptance-criteria | 1 tool call | 2 | 0 of 2 | no | 0.07 | 0.01 | 18 (9 + 9) | 0 of 11 | no pass on the skill |
| `accessibility-review-ac-walk` | accessibility-review | 5 regex, 2 tool call, 1 file | 1 | 0 of 1 | yes: "Start it through the scratch launcher `tools/scratch_run.py` with the scratch folder `scratch/portal-walk` next to the project [...] and `PORTAL_DATA` inside that folder" | 0.44 | 0.01 | 65 | 1 of 14 | no pass on the skill |
| `accessibility-review-neg-readability` | accessibility-review | 1 tool call | 0 |  | no | 0.06 | 0.00 | 9 (8 + 1) | 0 of 13 | no pass on the skill |
| `accessibility-review-payfine` | accessibility-review | 3 regex, 1 tool call, 1 file | 9 | 0 of 9 | partly: "fill in the slice's accessibility placeholder" | 0.23 | 0.40 | 96 (65 + 31) | 7 of 26 | no pass on the skill |
| `accessibility-review-payfine-subtle` | accessibility-review | 3 regex, 1 tool call, 1 file | 9 | 0 of 9 | partly: "fill in the slice's accessibility placeholder" | 0.23 | 0.40 | 99 (68 + 31) | 5 of 26 | no pass on the skill |
| `adr-neg-rename` | adr | 1 regex, 1 tool call | 1 | 0 of 1 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `adr-payment-gateway` | adr | 2 regex, 1 tool call, 1 file | 1 | 0 of 1 | no | 0.08 | 0.01 | 13 (11 + 2) | 0 of 4 (few runs) | no pass on the skill |
| `architecture-design-neg-review` | architecture-design | 1 tool call | 0 |  | no | 0.09 | 0.00 | 15 (15 + 0) | 0 of 17 | no pass on the skill |
| `architecture-design-owner-sheet` | architecture-design | 1 regex, 1 tool call | 1 | 0 of 1 | no | 0.21 | 0.01 | 38 (38 + 4) | 0 of 13 | no pass on the skill |
| `architecture-design-payfine-phase1` | architecture-design | 1 regex, 1 tool call | 2 | 0 of 2 | no | 0.18 | 0.02 | 38 (32 + 9) | 0 of 24 | no pass on the skill |
| `architecture-design-payfine-phase2` | architecture-design | 1 regex | 9 | 0 of 9 | no | 0.26 | 0.32 | 102 (67 + 35) | 20 of 25 | no pass on the skill |
| `architecture-design-payfine-via-agent` | architecture-design | 3 regex, 1 tool call | 1 | 0 of 1 | partly: "its architecture map is at `docs/architecture-map.md`" | 0.22 | 0.02 | 45 | 0 of 19 | no pass on the skill |
| `architecture-design-scope-consequence` | architecture-design | 1 regex, 1 tool call | 2 | 0 of 2 | no | 0.18 | 0.01 | 44 (39 + 9) | 15 of 34 | no pass on the skill |
| `architecture-review-neg-security-review` | architecture-review | 1 tool call | 0 |  | no | 0.08 | 0.00 | 18 (17 + 1) | 0 of 12 | no pass on the skill |
| `architecture-review-neg-test-quality-review` | architecture-review | 1 tool call | 0 |  | no | 0.08 | 0.00 | 12 (11 + 1) | 0 of 13 | no pass on the skill |
| `chunk-runner-gap-handback` | chunk-runner | 5 regex, 4 tool call | 0 |  | no | 0.28 | 0.01 | 34 (26 + 7) | 8 of 27 | 0 of 7 |
| `chunk-runner-gate-deviation` | chunk-runner | 6 regex, 4 tool call, 1 file | 0 |  | partly: "Stop once the gate has run and its result is known, before any launch" | 0.30 | 0.00 | 34 (30 + 3) | 0 of 21 | 1 of 14: `gate-design-modules` |
| `chunk-runner-gate-outside` | chunk-runner | 5 regex, 5 tool call | 0 |  | partly: "Stop once the gate has passed, before any reviewer is launched" | 0.55 | 0.00 | 85 | 0 of 19 | 0 of 10 |
| `chunk-runner-gate-sources` | chunk-runner | 6 regex, 4 tool call | 0 |  | partly: "Stop once the gate has passed, before any reviewer is launched" | 0.53 | 0.00 | 75 | 1 of 17 | 2 of 8: `gate-planning-sources`, `handback-template` |
| `chunk-runner-one-fix-round` | chunk-runner | 5 regex, 6 tool call | 0 |  | partly: "the sandbox checks in this round are information and never end it" | 0.55 | 0.00 | 84 | 6 of 31 | 2 of 15: `handback-one-line`, `regressions-to-a-fixer` |
| `chunk-runner-replay-not-the-handback` | chunk-runner | 3 regex, 2 tool call | 1 | 0 of 1 | no | 0.46 | 0.01 | 66 | 0 of 7 | 0 of 4 |
| `chunk-runner-replay-unheld-commit` | chunk-runner | 3 regex, 3 tool call | 1 | 0 of 1 | no | 0.39 | 0.00 | 55 | 0 of 7 | 0 of 5 |
| `chunk-runner-review-round` | chunk-runner | 6 regex, 8 tool call, 2 file | 0 |  | partly: "Stop once round 0 is recorded [...] don't start the fix round" | 1.22 | 0.02 | 152 | 1 of 20 | 1 of 19: `smoke-agent-kind` |
| `chunk-runner-waits-for-handback` | chunk-runner | 4 regex, 8 tool call | 0 |  | yes: "end after step 2, the gate on the builder's commit (and its one fixer, if the gate fails). Launch no reviewer and no smoke agent" | 0.59 | 0.00 | 85 | 6 of 15 | 2 of 19: `handback-one-line`, `hash-is-real` |
| `code-review-catalog` | code-review | 1 regex, 2 tool call, 1 file | 2 | 0 of 2 | no | 0.12 | 0.02 | 28 (22 + 7) | 9 of 19 | no pass on the skill |
| `code-review-comments-chunk` | code-review | 3 regex, 3 tool call, 1 file | 3 | 0 of 3 | partly: "Write one report in the shared finding format [...] and hand back the counts and the path" | 0.24 | 0.06 | 48 (37 + 13) | 20 of 43 | no pass on the skill |
| `code-review-days-left-pr` | code-review | 1 regex, 1 tool call, 1 file | 7 | 0 of 7 | no | 0.15 | 0.12 | 57 (33 + 24) | 0 of 10 | no pass on the skill |
| `code-review-fine-notices-pr` | code-review | 1 regex, 2 tool call, 1 file | 8 | 0 of 8 | no | 0.15 | 0.20 | 56 (31 + 24) | 7 of 13 | no pass on the skill |
| `code-review-fine-notices-pr-via-agent` | code-review | 2 regex, 1 tool call, 1 file | 8 | 0 of 8 | no | 0.21 | 0.12 | 73 | 19 of 20 | no pass on the skill |
| `code-review-fines-report-pr` | code-review | 1 regex, 1 tool call, 1 file | 5 | 0 of 5 | no | 0.16 | 0.11 | 58 (42 + 16) | 2 of 13 | no pass on the skill |
| `code-review-neg-architecture` | code-review | 1 tool call | 0 |  | no | 0.17 | 0.00 | 35 (35 + 0) | 0 of 11 | no pass on the skill |
| `code-review-structural-high-at-d` | code-review | 1 regex, 1 tool call, 1 file | 2 | 0 of 2 | no | 0.21 | 0.06 | 69 (53 + 16) | 4 of 5 (few runs) | no pass on the skill |
| `delegation-consult-with-file` | reliability-requirements | 4 regex, 2 tool call | 1 | 0 of 1 | yes: "Decide it, revise your document in place, commit it by name as `Decision <n>: <title>`, and hand back the commit hash and one sentence" | 0.15 | 0.03 | 29 (20 + 10) | 11 of 21 | no pass on the skill |
| `delegation-consult-without-file` | reliability-requirements | 1 regex, 2 tool call | 1 | 0 of 1 | no | 0.12 | 0.02 | 17 (11 + 6) | 4 of 19 | no pass on the skill |
| `delivery-ci-red-not-done` | delivery | 5 regex, 3 tool call, 1 file | 2 | 0 of 2 | partly: "This session may launch no agent: when the next action is a launch, write the handoff file for it (what the agent is to be handed, word for word where the skill gives words) and stop there" | 0.39 | 0.03 | 53 (42 + 12) | 2 of 7 | no pass on the skill |
| `design-system-payfine-phase1` | design-system | 1 regex, 1 tool call | 1 | 0 of 1 | no | 0.10 | 0.00 | 14 (11 + 3) | 0 of 7 | no pass on the skill |
| `design-system-payfine-phase2` | design-system | 2 regex, 2 file | 4 | 0 of 4 | no | 0.18 | 0.04 | 59 (46 + 12) | 0 of 7 | no pass on the skill |
| `design-system-payfine-phase3` | design-system | 3 regex, 1 file | 5 | 0 of 5 | no | 0.31 | 0.26 | 132 (91 + 39) | 7 of 16 | no pass on the skill |
| `design-system-payfine-reference` | design-system | 3 regex, 1 tool call | 2 | 0 of 2 | no | 0.22 | 0.01 | 75 (68 + 7) | 1 of 6 | no pass on the skill |
| `design-system-payfine-review` | design-system | 1 regex, 1 tool call, 1 file | 4 | 0 of 4 | no | 0.18 | 0.06 | 60 (49 + 12) | 0 of 7 | no pass on the skill |
| `external-review-triage-cancel-hold` | external-review-triage | 2 regex, 1 tool call, 1 file | 3 | 0 of 3 | partly: "Write your report to [...] and hand back the counts and the path" | 0.35 | 0.07 | 54 (47 + 8) | 0 of 10 | no pass on the skill |
| `library-app-catalog-review` | architecture-review | 1 regex, 1 tool call, 1 file | 2 | 0 of 2 | no | 0.19 | 0.04 | 50 (42 + 8) | 3 of 14 | no pass on the skill |
| `library-app-fines-review` | architecture-review | 1 regex, 1 tool call, 1 file | 4 | 0 of 4 | no | 0.27 | 0.13 | 84 (71 + 12) | 0 of 9 | no pass on the skill |
| `library-app-lending-review` | architecture-review | 1 regex, 1 tool call, 1 file | 6 | 0 of 6 | no | 0.25 | 0.32 | 81 (60 + 21) | 4 of 15 | no pass on the skill |
| `library-app-lending-review-via-agent` | architecture-review | 1 regex, 1 tool call, 1 file | 6 | 0 of 6 | partly: "return its findings report verbatim [...] (including its opening section on the importance ordering it assumed)" | 0.38 | 0.20 | 132 | 1 of 12 | no pass on the skill |
| `library-app-members-review` | architecture-review | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.21 | 0.09 | 60 (51 + 9) | 0 of 9 | no pass on the skill |
| `library-app-notifications-review` | architecture-review | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.22 | 0.08 | 63 (54 + 9) | 0 of 9 | no pass on the skill |
| `library-app-reporting-pr` | architecture-review | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.21 | 0.06 | 57 (48 + 9) | 0 of 9 | no pass on the skill |
| `library-app-reporting-review` | architecture-review | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.22 | 0.08 | 63 (54 + 9) | 0 of 9 | no pass on the skill |
| `library-app-structure-review` | architecture-review | 1 regex, 1 tool call, 1 file | 4 | 0 of 4 | no | 0.30 | 0.18 | 84 (72 + 12) | 0 of 9 | no pass on the skill |
| `map-query-consults` | map-query | 1 regex, 1 tool call | 4 | 0 of 4 | no | 0.10 | 0.03 | 23 (12 + 11) | 0 of 8 | no pass on the skill |
| `map-query-no-map` | map-query | 1 regex, 1 tool call | 1 | 0 of 1 | no | 0.07 | 0.01 | 8 (5 + 3) | 1 of 9 | no pass on the skill |
| `map-update-cancel-hold` | map-update | 5 regex, 1 tool call | 4 | 0 of 4 | no | 0.18 | 0.54 | 47 (23 + 24) | 21 of 22 | no pass on the skill |
| `operational-readiness-neg-reliability` | operational-readiness | 1 tool call | 0 |  | no | 0.10 | 0.00 | 19 (19 + 1) | 0 of 11 | no pass on the skill |
| `operational-readiness-neg-security` | operational-readiness | 1 tool call | 0 |  | no | 0.06 | 0.00 | 12 (12 + 0) | 0 of 10 | no pass on the skill |
| `operational-readiness-ops-phase1` | operational-readiness | 1 tool call | 1 | 0 of 1 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `operational-readiness-ops-phase2` | operational-readiness | 0 | 5 | 0 of 5 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `operational-readiness-release-phase1` | operational-readiness | 1 tool call | 2 | 0 of 2 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `operational-readiness-release-phase2` | operational-readiness | 0 | 5 | 0 of 5 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `orchestrator-asks-for-target` | orchestrator | 3 tool call | 1 | 0 of 1 | no | 0.18 | 0.00 | 13 (8 + 4) | 0 of 38 | no pass on the skill |
| `orchestrator-backward-route` | orchestrator | 4 tool call, 1 file | 2 | 0 of 2 | no | 0.32 | 0.02 | 59 (48 + 11) | 19 of 49 | no pass on the skill |
| `orchestrator-budget-exceeded` | orchestrator | 2 regex, 2 tool call | 1 | 0 of 1 | no | 0.25 | 0.01 | 30 (22 + 8) | 26 of 40 | no pass on the skill |
| `orchestrator-chunk-runner-handback` | orchestrator | 6 regex, 2 tool call | 1 | 0 of 1 | partly: "hand off once chunk 1's C line is written and its records committed, before chunk 2's runner is launched" | 0.29 | 0.01 | 38 (32 + 7) | 0 of 19 | no pass on the skill |
| `orchestrator-chunk-runner-launch` | orchestrator | 6 tool call, 1 tool order | 1 | 0 of 1 | partly: "hand off as soon as chunk 1's runner has been launched: don't wait for it to return; write the handoff file saying the runner is in flight and stop" | 1.75 | 0.01 | 279 | 14 of 38 | no pass on the skill |
| `orchestrator-definition-of-done` | orchestrator | 8 tool call, 1 tool order, 1 file | 1 | 0 of 1 | partly: "hand off before the slice reviewers are launched (after the Definition of Done has been acted on and checked again)" | 1.09 | 0.01 | 203 | 51 of 58 | no pass on the skill |
| `orchestrator-delivery-foreground` | orchestrator | 4 regex, 4 tool call | 1 | 0 of 1 | no | 0.45 | 0.01 | 72 (59 + 13) | 27 of 73 | no pass on the skill |
| `orchestrator-delivery-removal` | orchestrator | 6 regex, 5 tool call, 1 tool order | 1 | 0 of 1 | partly: "If the scan finds anything of that file in this branch's commits, replace it and rewrite the branch before it is pushed. You have my word for that rewrite" | 0.46 | 0.01 | 102 | 2 of 20 | no pass on the skill |
| `orchestrator-gap-without-delegation` | orchestrator | 2 regex, 5 tool call | 1 | 0 of 1 | no | 0.52 | 0.01 | 74 | 12 of 55 | no pass on the skill |
| `orchestrator-issue-fix-records` | orchestrator | 6 regex, 4 tool call | 1 | 0 of 1 | partly: "Hand off as soon as the chunk loop's A line is written (write the handoff file and stop; don't start B in this session)" | 0.34 | 0.01 | 43 (39 + 4) | 1 of 4 (few runs) | no pass on the skill |
| `orchestrator-plan-check-seam` | orchestrator | 2 regex, 4 tool call | 1 | 0 of 1 | partly: "hand off once the B line is written, before chunk 1's build" | 0.47 | 0.01 | 74 | 2 of 47 | no pass on the skill |
| `orchestrator-readiness-gate` | orchestrator | 2 regex, 4 tool call, 1 tool order | 2 | 0 of 2 | partly: "Hand off as soon as the chunk loop's A line is written (write the handoff file and stop; don't start B in this session)" | 0.62 | 0.03 | 141 (121 + 15) | 15 of 61 | no pass on the skill |
| `orchestrator-readiness-open-item` | orchestrator | 2 regex, 3 tool call | 1 | 0 of 1 | no | 0.31 | 0.01 | 45 (40 + 6) | 6 of 30 | no pass on the skill |
| `orchestrator-readiness-sources` | orchestrator | 4 regex, 4 tool call | 1 | 0 of 1 | no | 0.32 | 0.01 | 47 (42 + 5) | 0 of 17 | no pass on the skill |
| `orchestrator-readme-stale-not-done` | orchestrator | 2 regex, 8 tool call, 1 tool order | 1 | 0 of 1 | partly: "hand off before the slice reviewers are launched (after the Definition of Done has been acted on and checked again)" | 1.11 | 0.01 | 218 | 5 of 6 | no pass on the skill |
| `orchestrator-route-accessibility` | orchestrator | 1 regex, 4 tool call, 1 file | 2 | 0 of 2 | no | 0.48 | 0.01 | 115 (103 + 11) | 11 of 54 | no pass on the skill |
| `orchestrator-route-backward-requirements` | orchestrator | 5 tool call, 1 file | 2 | 0 of 2 | no | 0.26 | 0.01 | 34 (26 + 9) | 4 of 40 | no pass on the skill |
| `orchestrator-route-design` | orchestrator | 4 tool call, 1 file | 2 | 0 of 2 | no | 0.35 | 0.01 | 52 (43 + 10) | 1 of 38 | no pass on the skill |
| `orchestrator-route-design-system` | orchestrator | 5 tool call, 1 file | 2 | 0 of 2 | no | 0.26 | 0.01 | 36 (25 + 11) | 0 of 36 | no pass on the skill |
| `orchestrator-route-implementation` | orchestrator | 3 tool call, 1 file | 2 | 0 of 2 | no | 0.23 | 0.01 | 31 (22 + 9) | 2 of 42 | no pass on the skill |
| `orchestrator-route-implementation-prenamed` | orchestrator | 2 tool call, 1 file | 2 | 0 of 2 | no | 0.23 | 0.01 | 30 (20 + 9) | 1 of 38 | no pass on the skill |
| `orchestrator-route-open-pr` | orchestrator | 1 regex, 6 tool call | 1 | 0 of 1 | partly: "Report what is open and stop after your first question to me; don't run the triage or any fix in this session" | 0.24 | 0.01 | 26 (21 + 5) | 0 of 18 | no pass on the skill |
| `orchestrator-route-problem-framing` | orchestrator | 4 tool call, 1 file | 2 | 0 of 2 | no | 0.21 | 0.01 | 24 (14 + 10) | 1 of 37 | no pass on the skill |
| `orchestrator-route-reliability` | orchestrator | 5 tool call, 1 file | 2 | 0 of 2 | no | 0.27 | 0.01 | 36 (28 + 8) | 5 of 45 | no pass on the skill |
| `orchestrator-route-scope-decision` | orchestrator | 3 tool call, 1 file | 2 | 0 of 2 | no | 0.28 | 0.02 | 42 (32 + 9) | 63 of 111 | no pass on the skill |
| `orchestrator-route-screen-design` | orchestrator | 1 regex, 3 tool call, 1 file | 2 | 0 of 2 | no | 0.42 | 0.01 | 92 (83 + 9) | 13 of 51 | no pass on the skill |
| `orchestrator-route-slicer-accessibility-mistake` | orchestrator | 4 tool call | 1 | 0 of 1 | no | 0.30 | 0.00 | 37 (32 + 6) | 1 of 35 | no pass on the skill |
| `orchestrator-route-slicing` | orchestrator | 4 tool call, 1 file | 2 | 0 of 2 | no | 0.31 | 0.01 | 48 (40 + 8) | 6 of 50 | no pass on the skill |
| `orchestrator-route-tech-bootstrap` | orchestrator | 4 tool call, 1 file | 2 | 0 of 2 | no | 0.26 | 0.01 | 34 (26 + 8) | 2 of 39 | no pass on the skill |
| `orchestrator-route-user-story` | orchestrator | 4 tool call, 1 file | 2 | 0 of 2 | no | 0.23 | 0.01 | 34 (25 + 9) | 4 of 41 | no pass on the skill |
| `orchestrator-runner-handback-unverified` | orchestrator | 2 regex, 3 tool call | 2 | 0 of 2 | partly: "This session may launch no agent: when the next action is a launch, write the handoff file for it and stop there" | 0.29 | 0.02 | 35 (28 + 7) | 0 of 4 (few runs) | no pass on the skill |
| `orchestrator-security-stage` | orchestrator | 3 tool call, 1 file | 2 | 0 of 2 | no | 0.31 | 0.01 | 44 (37 + 7) | 0 of 36 | no pass on the skill |
| `orchestrator-session-setup` | orchestrator | 4 tool call | 1 | 0 of 1 | no | 0.23 | 0.01 | 22 (17 + 5) | 8 of 40 | no pass on the skill |
| `orchestrator-superseded-scope-map` | orchestrator | 4 tool call, 1 file | 1 | 0 of 1 | no | 0.27 | 0.01 | 35 (31 + 4) | 0 of 36 | no pass on the skill |
| `pr-writeup-portal-fines` | pr-writeup | 1 tool call | 3 | 0 of 3 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `problem-framing-doc-payfine` | problem-framing-doc | 1 tool call, 1 file | 3 | 0 of 3 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `reliability-requirements-neg-review` | reliability-requirements | 1 tool call | 0 |  | no | 0.10 | 0.00 | 23 (23 + 0) | 0 of 12 | no pass on the skill |
| `reliability-requirements-payfine-phase1` | reliability-requirements | 1 tool call | 2 | 0 of 2 | no | 0.12* | 0.03 | 25 (19 + 7) | 0 of 4 (few runs) | no pass on the skill |
| `reliability-requirements-payfine-phase2` | reliability-requirements | 1 regex | 3 | 0 of 3 | no | 0.13 | 0.06 | 38 (32 + 7) | 0 of 10 | no pass on the skill |
| `reliability-requirements-payfine-phase2-proceed` | reliability-requirements | 1 regex | 3 | 0 of 3 | no | 0.14 | 0.06 | 41 (34 + 7) | 0 of 10 | no pass on the skill |
| `reliability-requirements-payfine-phase2-stop` | reliability-requirements | 1 regex | 3 | 0 of 3 | no | 0.11 | 0.05 | 23 (14 + 9) | 3 of 10 | no pass on the skill |
| `reliability-requirements-payfine-phase3` | reliability-requirements | 1 regex, 1 file | 7 | 0 of 7 | no | 0.21* | 0.38 | 83 (52 + 31) | 0 of 3 (few runs) | no pass on the skill |
| `reliability-review-alerts` | reliability-review | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.28 | 0.12 | 104 (85 + 19) | 1 of 15 | no pass on the skill |
| `reliability-review-catalog` | reliability-review | 1 regex, 1 tool call, 1 file | 2 | 0 of 2 | no | 0.24 | 0.07 | 71 (62 + 8) | 6 of 18 | no pass on the skill |
| `reliability-review-fine-payment` | reliability-review | 1 regex, 1 tool call, 1 file | 4 | 0 of 4 | no | 0.24 | 0.14 | 76 (62 + 14) | 1 of 15 | no pass on the skill |
| `reliability-review-http` | reliability-review | 1 regex, 1 tool call, 1 file | 5 | 0 of 5 | no | 0.33 | 0.19 | 112 (93 + 18) | 0 of 12 | no pass on the skill |
| `reliability-review-neg-architecture` | reliability-review | 1 tool call | 0 |  | no | 0.10 | 0.00 | 20 (20 + 1) | 0 of 12 | no pass on the skill |
| `reliability-review-neg-security` | reliability-review | 1 tool call | 0 |  | no | 0.08 | 0.00 | 18 (18 + 0) | 0 of 13 | no pass on the skill |
| `reliability-review-nightly` | reliability-review | 1 regex, 1 tool call, 1 file | 8 | 0 of 8 | no | 0.32 | 0.48 | 118 (91 + 27) | 7 of 21 | no pass on the skill |
| `reliability-review-nightly-via-agent` | reliability-review | 1 regex, 1 tool call, 1 file | 8 | 0 of 8 | no | 0.50 | 0.38 | 186 | 6 of 19 | no pass on the skill |
| `reliability-review-portal-pay-pr` | reliability-review | 1 regex, 1 tool call, 1 file | 4 | 0 of 4 | no | 0.25 | 0.11 | 74 (62 + 12) | 0 of 12 | no pass on the skill |
| `reliability-review-refund-pr` | reliability-review | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.23 | 0.08 | 68 (53 + 15) | 1 of 15 | no pass on the skill |
| `requirements-refinement-open-question` | requirements-refinement | 1 regex, 1 tool call | 3 | 0 of 3 | no | 0.11 | 0.02 | 26 (16 + 10) | 0 of 10 | no pass on the skill |
| `requirements-refinement-owner-sheet` | requirements-refinement | 2 regex, 1 tool call, 1 file | 1 | 0 of 1 | no | 0.13 | 0.01 | 31 (27 + 4) | 0 of 9 | no pass on the skill |
| `requirements-refinement-payfine-phase1` | requirements-refinement | 1 tool call | 4 | 0 of 4 | no | 0.11 | 0.03 | 30 (15 + 15) | 3 of 12 | no pass on the skill |
| `requirements-refinement-payfine-phase2` | requirements-refinement | 1 regex, 1 file | 7 | 0 of 7 | no | 0.13 | 0.12 | 55 (24 + 31) | 11 of 13 | no pass on the skill |
| `scope-map-self-service` | scope-map | 1 tool call, 1 file | 3 | 0 of 3 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `screen-design-owner-sheet` | screen-design | 1 regex, 1 tool call, 1 file | 1 | 0 of 1 | no | 0.31 | 0.01 | 89 (85 + 4) | 0 of 9 | no pass on the skill |
| `screen-design-payfine` | screen-design | 3 regex, 2 tool call, 1 file | 7 | 0 of 7 | no | 0.30 | 0.10 | 110 (83 + 27) | 2 of 8 | no pass on the skill |
| `security-requirements-neg-review` | security-requirements | 1 tool call | 0 |  | no | 0.06 | 0.00 | 13 (13 + 0) | 0 of 10 | no pass on the skill |
| `security-requirements-payfine-phase1` | security-requirements | 1 tool call | 2 | 0 of 2 | no | 0.14 | 0.02 | 33 (24 + 9) | 0 of 12 | no pass on the skill |
| `security-requirements-payfine-phase2` | security-requirements | 1 regex | 3 | 0 of 3 | no | 0.15 | 0.08 | 43 (31 + 12) | 4 of 21 | no pass on the skill |
| `security-requirements-payfine-phase2-proceed` | security-requirements | 1 regex | 3 | 0 of 3 | no | 0.16 | 0.06 | 49 (39 + 10) | 0 of 16 | no pass on the skill |
| `security-requirements-payfine-phase2-stop` | security-requirements | 1 regex | 3 | 0 of 3 | no | 0.12 | 0.04 | 21 (12 + 10) | 0 of 16 | no pass on the skill |
| `security-requirements-payfine-phase3` | security-requirements | 1 regex, 1 file | 7 | 0 of 7 | no | 0.21 | 0.17 | 69 (46 + 23) | 13 of 15 | no pass on the skill |
| `security-requirements-placeholder-pointer` | security-requirements | 5 regex, 1 tool call, 1 file | 1 | 0 of 1 | no | 0.31 | 0.03 | 103 (100 + 4) | 0 of 10 | no pass on the skill |
| `security-requirements-source-criterion` | security-requirements | 3 regex, 2 tool call, 1 file | 1 | 0 of 1 | partly: "nothing from that file may end up in the repository" | 0.29 | 0.03 | 95 (90 + 5) | 0 of 9 | no pass on the skill |
| `security-review-catalog` | security-review | 1 regex, 1 tool call, 1 file | 2 | 0 of 2 | no | 0.20 | 0.04 | 57 (47 + 10) | 1 of 13 | no pass on the skill |
| `security-review-config` | security-review | 1 regex, 1 tool call, 1 file | 5 | 0 of 5 | no | 0.32 | 0.23 | 113 (94 + 19) | 0 of 10 | no pass on the skill |
| `security-review-http` | security-review | 1 regex, 1 tool call, 1 file | 5 | 0 of 5 | no | 0.28 | 0.15 | 89 (73 + 16) | 0 of 10 | no pass on the skill |
| `security-review-neg-architecture` | security-review | 1 tool call | 0 |  | no | 0.10 | 0.00 | 20 (20 + 0) | 0 of 10 | no pass on the skill |
| `security-review-neg-reliability` | security-review | 1 tool call | 0 |  | no | 0.11 | 0.00 | 28 (28 + 1) | 0 of 13 | no pass on the skill |
| `security-review-portal-pr` | security-review | 1 regex, 1 tool call, 1 file | 5 | 0 of 5 | no | 0.19 | 0.15 | 61 (43 + 18) | 3 of 16 | no pass on the skill |
| `security-review-reminders` | security-review | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.22 | 0.07 | 66 (54 + 12) | 0 of 10 | no pass on the skill |
| `security-review-source-value` | security-review | 3 regex, 2 tool call, 1 file | 1 | 0 of 1 | no | 0.15 | 0.01 | 30 (25 + 4) | 0 of 9 | no pass on the skill |
| `staleness-audit-docs` | staleness-audit | 1 tool call | 5 | 0 of 5 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `supply-chain-review-accept-phase1` | supply-chain-review | 1 tool call | 2 | 0 of 2 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `supply-chain-review-accept-phase2` | supply-chain-review | 0 | 3 | 0 of 3 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `supply-chain-review-accepted` | supply-chain-review | 1 regex, 1 tool call, 1 file | 5 | 0 of 5 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `supply-chain-review-build` | supply-chain-review | 1 regex, 1 tool call, 1 file | 5 | 0 of 5 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `supply-chain-review-build-via-agent` | supply-chain-review | 1 regex, 1 tool call, 1 file | 5 | 0 of 5 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `supply-chain-review-neg-reliability` | supply-chain-review | 1 tool call | 0 |  | no | 0.10 | 0.00 | 20 (20 + 0) | 0 of 11 | no pass on the skill |
| `supply-chain-review-neg-security` | supply-chain-review | 1 tool call | 0 |  | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `supply-chain-review-workflows` | supply-chain-review | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `tdd-implementation-lite-cancel-hold` | tdd-implementation-lite | 13 regex, 2 tool call, 4 tool order, 1 file | 6 | 0 of 6 | no | 0.41 | 0.08 | 92 (65 + 27) | 19 of 19 | no pass on the skill |
| `tdd-implementation-lite-cancel-hold-via-agent` | tdd-implementation-lite | 14 regex, 2 tool call, 2 tool order, 1 file | 6 | 0 of 6 | no | 0.39 | 0.09 | 106 | 34 of 34 | no pass on the skill |
| `tdd-implementation-lite-chunk-plan` | tdd-implementation-lite | 3 regex, 2 tool call, 1 file | 2 | 0 of 2 | partly: "Write the chunk plan [...] and build nothing" | 0.19 | 0.06 | 53 (32 + 21) | 14 of 29 | no pass on the skill |
| `tdd-implementation-lite-named-fix` | tdd-implementation-lite | 8 regex, 2 tool call, 1 file | 3 | 0 of 3 | no | 0.36 | 0.04 | 73 (56 + 17) | 7 of 29 | no pass on the skill |
| `tdd-implementation-lite-one-chunk` | tdd-implementation-lite | 8 regex, 3 tool call, 1 tool order | 4 | 0 of 4 | partly: "Chunks are committed." | 0.30 | 0.05 | 59 (46 + 13) | 6 of 29 | no pass on the skill |
| `tdd-implementation-lite-rename-fix` | tdd-implementation-lite | 10 regex, 3 tool call, 1 file | 0 |  | no | 0.29 | 0.00 | 38 (38 + 1) | 3 of 22 | no pass on the skill |
| `technology-bootstrap-phase1` | technology-bootstrap | 1 tool call | 2 | 0 of 2 | no | 0.09 | 0.02 | 26 (15 + 10) | 1 of 10 | no pass on the skill |
| `technology-bootstrap-phase2` | technology-bootstrap | 3 regex | 4 | 0 of 4 | partly: "pick the one where that's the default [...] Give me your recommendations for the whole set in one message rather than one at a time" | 0.15 | 0.07 | 78 (55 + 23) | 7 of 19 | no pass on the skill |
| `technology-bootstrap-phase3` | technology-bootstrap | 1 regex, 1 file | 4 | 0 of 4 | no | 0.14 | 0.08 | 38 (19 + 19) | 9 of 16 | no pass on the skill |
| `technology-bootstrap-phase3-reject` | technology-bootstrap | 1 regex, 1 file | 5 | 0 of 5 | no | 0.15 | 0.08 | 43 (29 + 14) | 6 of 11 | no pass on the skill |
| `test-quality-review-fines` | test-quality-review | 1 regex, 1 tool call, 1 file | 7 | 0 of 7 | no | 0.19 | 0.29 | 76 (49 + 27) | 9 of 18 | no pass on the skill |
| `test-quality-review-neg-code-review` | test-quality-review | 1 tool call | 0 |  | no | 0.10 | 0.00 | 22 (22 + 1) | 0 of 11 | no pass on the skill |
| `test-quality-review-reminders` | test-quality-review | 1 regex, 1 tool call, 1 file | 3 | 0 of 3 | no | 0.15 | 0.05 | 42 (32 + 9) | 0 of 12 | no pass on the skill |
| `test-quality-review-seam-fake` | test-quality-review | 3 regex, 1 tool call, 1 file | 3 | 0 of 3 | partly: "Write your report in the shared finding format [...] and hand back the counts and the path" | 0.19 | 0.06 | 44 (32 + 12) | 0 of 24 | no pass on the skill |
| `user-facing-docs-renewals` | user-facing-docs | 1 tool call, 1 file | 2 | 0 of 2 | no |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `user-story-writeup-payfine-phase1` | user-story-writeup | 1 tool call | 2 | 0 of 2 | no | 0.06 | 0.01 | 13 (6 + 7) | 0 of 7 | no pass on the skill |
| `user-story-writeup-payfine-phase2` | user-story-writeup | 1 regex, 1 file | 3 | 0 of 3 | partly: "Don't create the issue yourself" |  |  |  | 0 of 0 (few runs) | no pass on the skill |
| `vertical-slicing-handback` | vertical-slicing | 1 tool call | 4 | 0 of 4 | no | 0.17 | 0.02 | 45 (32 + 13) | 0 of 11 | no pass on the skill |
| `vertical-slicing-no-requirements` | vertical-slicing | 1 regex, 1 tool call | 2 | 0 of 2 | no | 0.09 | 0.01 | 12 (6 + 6) | 0 of 11 | no pass on the skill |
| `vertical-slicing-no-screen` | vertical-slicing | 1 regex, 1 tool call, 1 file | 1 | 0 of 1 | no | 0.17 | 0.02 | 41 (35 + 7) | 1 of 17 | no pass on the skill |
| `vertical-slicing-owner-sheet` | vertical-slicing | 2 regex, 2 tool call, 1 file | 2 | 0 of 2 | no | 0.15 | 0.01 | 41 (32 + 9) | 2 of 18 | no pass on the skill |
| `vertical-slicing-payfine-phase1` | vertical-slicing | 1 regex, 2 tool call, 1 file | 5 | 0 of 5 | no | 0.14 | 0.04 | 44 (27 + 17) | 0 of 11 | no pass on the skill |
| `why-comments-collect-fine` | why-comments | 1 regex, 1 tool call, 1 file | 4 | 0 of 4 | no | 0.07* | 0.02 | 35 (14 + 21) | 0 of 4 (few runs) | no pass on the skill |

**One run of every case:** $48.13 over the 148 cases with a completed run held (agent $38.88, judges $9.26, 19% judges); $47.30 over the 145 with a run since 2026-11-10. 18 cases have no completed run held and are not priced.

**Graders:** 435 judges and 684 tool checks over 166 cases; 24 cases have no judge.

**Judges a tool could decide:** 0 of 435, in 0 cases; 0 cases would be left with no judge. Their share of the judge cost, split evenly within each case (an estimate): $0.00 per run of every case.

**Runs that failed only on a judge:** of 2985 completed runs since the bars, 668 failed; 437 of those failed on judges alone, and 0 on judges a tool could decide alone ($0.00 of runs at today's cost per run): none.

**Prompt states the rule it grades:** yes 3, partly 28, no 135.

**Never failed since the bar (6 or more runs):** 64 cases, $14.68 of one run of every case. **Never failed and $0.40 or more a run (8, $3.82):** `chunk-runner-gate-outside` $0.55, `security-review-config` $0.55, `reliability-review-http` $0.51, `library-app-structure-review` $0.48, `chunk-runner-replay-not-the-handback` $0.47, `security-review-http` $0.43, `external-review-triage-cancel-hold` $0.42, `library-app-fines-review` $0.41.

By skill (one run of each of its cases; the judges a tool could decide and their estimated share):

| Skill | Cases (priced) | Agent $ | Judges $ | Judges | A tool could decide | Their share $ | Prompts stating the rule (yes, partly) | Never failed |
|---|---|---|---|---|---|---|---|---|
| orchestrator | 34 (34) | 13.92 | 0.38 | 51 | 0 | 0.00 | 0, 10 | 7 |
| chunk-runner | 9 (9) | 4.87 | 0.05 | 2 | 0 | 0.00 | 1, 5 | 4 |
| reliability-review | 10 (10) | 2.57 | 1.56 | 37 | 0 | 0.00 | 0, 0 | 4 |
| architecture-review | 11 (11) | 2.42 | 1.17 | 34 | 0 | 0.00 | 0, 1 | 8 |
| tdd-implementation-lite | 6 (6) | 1.94 | 0.33 | 21 | 0 | 0.00 | 0, 2 | 0 |
| security-review | 8 (8) | 1.56 | 0.66 | 21 | 0 | 0.00 | 0, 0 | 6 |
| code-review | 8 (8) | 1.40 | 0.70 | 35 | 0 | 0.00 | 0, 1 | 2 |
| security-requirements | 8 (8) | 1.45 | 0.43 | 20 | 0 | 0.00 | 0, 1 | 6 |
| accessibility-review | 4 (4) | 0.96 | 0.82 | 19 | 0 | 0.00 | 1, 2 | 1 |
| reliability-requirements | 8 (8) | 1.08 | 0.64 | 20 | 0 | 0.00 | 1, 0 | 3 |
| architecture-design | 6 (6) | 1.14 | 0.38 | 15 | 0 | 0.00 | 0, 1 | 4 |
| design-system | 5 (5) | 0.98 | 0.37 | 16 | 0 | 0.00 | 0, 0 | 3 |
| test-quality-review | 4 (4) | 0.64 | 0.39 | 13 | 0 | 0.00 | 0, 1 | 3 |
| vertical-slicing | 5 (5) | 0.72 | 0.10 | 14 | 0 | 0.00 | 0, 0 | 3 |
| technology-bootstrap | 4 (4) | 0.53 | 0.25 | 15 | 0 | 0.00 | 0, 1 | 0 |
| map-update | 1 (1) | 0.18 | 0.54 | 4 | 0 | 0.00 | 0, 0 | 0 |
| screen-design | 2 (2) | 0.61 | 0.12 | 8 | 0 | 0.00 | 0, 0 | 1 |
| requirements-refinement | 4 (4) | 0.47 | 0.18 | 15 | 0 | 0.00 | 0, 0 | 2 |
| delivery | 1 (1) | 0.39 | 0.03 | 2 | 0 | 0.00 | 0, 1 | 0 |
| external-review-triage | 1 (1) | 0.35 | 0.07 | 3 | 0 | 0.00 | 0, 1 | 1 |
| map-query | 2 (2) | 0.17 | 0.04 | 5 | 0 | 0.00 | 0, 0 | 1 |
| operational-readiness | 6 (2) | 0.16 | 0.00 | 13 | 0 | 0.00 | 0, 0 | 2 |
| supply-chain-review | 8 (1) | 0.10 | 0.00 | 23 | 0 | 0.00 | 0, 0 | 1 |
| why-comments | 1 (1) | 0.07 | 0.02 | 4 | 0 | 0.00 | 0, 0 | 0 |
| adr | 2 (1) | 0.08 | 0.01 | 2 | 0 | 0.00 | 0, 0 | 0 |
| acceptance-criteria | 1 (1) | 0.07 | 0.01 | 2 | 0 | 0.00 | 0, 0 | 1 |
| user-story-writeup | 2 (1) | 0.06 | 0.01 | 5 | 0 | 0.00 | 0, 1 | 1 |
| pr-writeup | 1 (0) |  |  | 3 | 0 | 0.00 | 0, 0 | 0 |
| problem-framing-doc | 1 (0) |  |  | 3 | 0 | 0.00 | 0, 0 | 0 |
| scope-map | 1 (0) |  |  | 3 | 0 | 0.00 | 0, 0 | 0 |
| staleness-audit | 1 (0) |  |  | 5 | 0 | 0.00 | 0, 0 | 0 |
| user-facing-docs | 1 (0) |  |  | 2 | 0 | 0.00 | 0, 0 | 0 |

**Judges a tool could decide, with the reason** (the judges that take reading have theirs in `tools/case_reading.json`):

| Case | Judge | What a tool would read | Share of a run $ |
|---|---|---|---|

**Prompts that state the rule they grade:**

| Case | The prompt's words | What they give away |
|---|---|---|
| `accessibility-review-ac-walk` | yes: "Start it through the scratch launcher `tools/scratch_run.py` with the scratch folder `scratch/portal-walk` next to the project [...] and `PORTAL_DATA` inside that folder" | the launcher, the scratch folder and the data directory are what `app-started-through-the-launcher` and `app-never-started-bare` grade; "in its criteria-walk mode" and "Hand back the counts and the path" are the orchestrator's launch text |
| `accessibility-review-payfine` | partly: "fill in the slice's accessibility placeholder" | tells the run the slice file has to change, which `slice-placeholder-filled` grades; how (a one-line pointer, nothing else touched) is left to the skill |
| `accessibility-review-payfine-subtle` | partly: "fill in the slice's accessibility placeholder" | as `accessibility-review-payfine` |
| `architecture-design-payfine-via-agent` | partly: "its architecture map is at `docs/architecture-map.md`" | points the run at the map, and `consults-map-query` grades that the map was consulted; the agent named is the path the case exists to run |
| `chunk-runner-gate-deviation` | partly: "Stop once the gate has run and its result is known, before any launch" | reworded in E5: the resume line names the state ("no gate has run on that commit"). The stopping point is left: it bounds the run's cost, and it is what `no-fixer-no-reviewer` grades; the module directories and deviation zone are handed-over facts, not the rule. |
| `chunk-runner-gate-outside` | partly: "Stop once the gate has passed, before any reviewer is launched" | reworded in E5: the resume line names the state. The stopping point is left (it bounds the run's cost): it says to go on until the gate passes and to launch no reviewer, `gate-run-twice` and `no-reviewer-before-the-pass` |
| `chunk-runner-gate-sources` | partly: "Stop once the gate has passed, before any reviewer is launched" | as `chunk-runner-gate-outside`; the prompt also says the target directory holds `sources.md`, which points at `--planning` |
| `chunk-runner-one-fix-round` | partly: "the sandbox checks in this round are information and never end it" | reworded in E5: the resume line names the state ("round 1 is not recorded yet") and no longer the action `round-one-recorded-with-the-range` grades. What is left is a handed-over fact the E2 pass found the run follows instead of the skill's sentence. Naming the skill to invoke is the launch, not a leak. |
| `chunk-runner-review-round` | partly: "Stop once round 0 is recorded [...] don't start the fix round" | reworded in E5: the resume line names the state ("no reviewer and no smoke agent has been launched") and no longer the two launches. The stopping point is left (it bounds the run's cost) and still names the recording `round-recorded-by-the-script` grades; the hand-over names `scratch_run.py`, which `smoke-agent-handed-the-launcher` grades |
| `chunk-runner-waits-for-handback` | yes: "end after step 2, the gate on the builder's commit (and its one fixer, if the gate fails). Launch no reviewer and no smoke agent" | `no-reviewer-launched` and `gate-on-the-builders-commit` grade what the stopping point says. The case starts at the build and has no resume line, so E5 reworded nothing here: the stopping point is the run's bound. |
| `code-review-comments-chunk` | partly: "Write one report in the shared finding format [...] and hand back the counts and the path" | the reply's content is what `hands-back-counts-and-path` grades; the rest is the orchestrator's launch text for a chunk reviewer, and "Touches: storage" is the state that should bring the reliability lens |
| `delegation-consult-with-file` | yes: "Decide it, revise your document in place, commit it by name as `Decision <n>: <title>`, and hand back the commit hash and one sentence" | every tool check and the hand-back judge grade what this sentence says; it is the orchestrator's task text, and the same words in `delegation-consult-without-file` are what must be refused, so here the case shows only that the file's presence does not stop the run |
| `delivery-ci-red-not-done` | partly: "This session may launch no agent: when the next action is a launch, write the handoff file for it (what the agent is to be handed, word for word where the skill gives words) and stop there" | `nothing-launched` grades what the prompt forbids, and the handoff the judge reads is asked for; that red checks are read and are not "done" is left to the skill |
| `external-review-triage-cancel-hold` | partly: "Write your report to [...] and hand back the counts and the path" | the reply's content is what `hands-back-counts-and-path` grades; it is the orchestrator's launch text |
| `library-app-lending-review-via-agent` | partly: "return its findings report verbatim [...] (including its opening section on the importance ordering it assumed)" | tells the run the report has an importance-ordering section, which `states-assumed-importance-ordering` grades; the agent named is the path the case exists to run |
| `orchestrator-chunk-runner-handback` | partly: "hand off once chunk 1's C line is written and its records committed, before chunk 2's runner is launched" | names the two actions `c-line-written-from-the-hand-back` and `records-committed-by-name` grade, and the stop `nothing-launched` grades; what goes on the line is left to the skill |
| `orchestrator-chunk-runner-launch` | partly: "hand off as soon as chunk 1's runner has been launched: don't wait for it to return; write the handoff file saying the runner is in flight and stop" | says a runner is what gets launched (`one-chunk-runner-launched`) and dictates the handoff's content, which is all the judge reads |
| `orchestrator-definition-of-done` | partly: "hand off before the slice reviewers are launched (after the Definition of Done has been acted on and checked again)" | "checked again" is `definition-of-done-checked-twice`; the stop is `no-slice-reviewer-yet` |
| `orchestrator-delivery-removal` | partly: "If the scan finds anything of that file in this branch's commits, replace it and rewrite the branch before it is pushed. You have my word for that rewrite" | the owner's word is an input the procedure requires, but "scan", "rewrite" and "before it is pushed" are also what `every-commit-scanned-before-and-after`, `branch-rewritten-by-the-script` and `rewrite-before-the-push` grade |
| `orchestrator-issue-fix-records` | partly: "Hand off as soon as the chunk loop's A line is written (write the handoff file and stop; don't start B in this session)" | the stop is `nothing-launched`, the handoff file is `handoff-carries-the-issue-prefix`; "Issue #14 is the one I told you to fix first on its own branch" is the owner's earlier answer, an input |
| `orchestrator-plan-check-seam` | partly: "hand off once the B line is written, before chunk 1's build" | the stop is `no-builder-launched` and the B line is `b-line-written`; that a failed plan goes back to a planner is left to the skill |
| `orchestrator-readiness-gate` | partly: "Hand off as soon as the chunk loop's A line is written (write the handoff file and stop; don't start B in this session)" | the stop is `no-builder-while-the-gate-fails`; the delegation and sandbox sentences are the owner's answers, inputs |
| `orchestrator-readme-stale-not-done` | partly: "hand off before the slice reviewers are launched (after the Definition of Done has been acted on and checked again)" | as `orchestrator-definition-of-done` |
| `orchestrator-route-open-pr` | partly: "Report what is open and stop after your first question to me; don't run the triage or any fix in this session" | "what is open" points at the tracker (`asks-the-tracker-for-open-pull-requests`, `-issues`), and the stop is `nothing-launched` and `no-planning-skill-invoked` |
| `orchestrator-runner-handback-unverified` | partly: "This session may launch no agent: when the next action is a launch, write the handoff file for it and stop there" | `nothing-launched` grades what the prompt forbids; that the line's hash is checked is left to the skill |
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
- `code-review-structural-high-at-d`: `a-long-single-job-function-stays-a-plain-finding` (judge) failed 6 of 7 runs.
- `delivery-ci-red-not-done`: `failing-tests-written-to-the-records` matches the test's name within 6,000 characters after any Write or Bash call that names `pr-ci-r1.md`, so the failed job's log printed by a later command passes a run that wrote the file without the test names.
- `map-update-cancel-hold`: `pre-existing-flags-not-new` (judge) failed 13 of 18 runs.
- `orchestrator-budget-exceeded`: `flow-ends-saying-what-is-built` (judge) failed 30 of 43 runs; whether the reply or the criterion is short was not read here.
- `orchestrator-definition-of-done`: `three-named-fixes-in-one-batch` (judge) failed 57 of 65 completed runs held; the coverage table says it fails replies that report exactly the three fixes. A grader that fails nearly every run tells a broken run from a good one no better than one that never fails.
- `orchestrator-issue-fix-records`: `branch-names-the-slice-and-the-issue` allows a quote before the branch name (`['"]?`), but a double quote is `\"` in the trace's JSON, so `git switch -c "slice-001-issue14-..."` would not match and a correct run would fail. Read from the pattern; the one failure held (2026-11-12) was a run that created no branch.
- `orchestrator-issue-fix-records`: `handoff-carries-the-issue-prefix` matches the file name within 1,500 characters after the start of any Write or Bash call, so a later call or a tool result that names it passes a run that never wrote it.
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
