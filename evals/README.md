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
these tools and the heavy-against-lite comparison still use it); this tool
imports it and adds the review rubric and the results-dir plumbing.
`tools/compare_arms.py` does the same between two arms of one tdd case:
the slice built by `tdd-implementation` against the same slice built by
`tdd-implementation-lite` (G2's measurement, since G1 left the bars at the
ceiling). It takes two gate results whose runs were kept with
`--keep-scaffold`, renders each run's change set against the case's
pristine scaffold with nothing that names the arm, judges every pair of
runs in both orders with the plugin's implementation rubric, and writes
every reason to a `*.pairwise.json` next to the first result.

Run it:

```
bash evals/fixtures/library-app/verify.sh
claude plugin eval . --case 'library-app-*' --ablation with-without --scaffold \
  --judge-model sonnet --max-cost-usd 14 --no-publish --trust-plugin
claude plugin eval . --case 'security-review-*' --ablation with-without --scaffold \
  --judge-model sonnet --max-cost-usd 10 --no-publish --trust-plugin
python3 -I evals/tools/pairwise_judge.py evals/results/<timestamp>
# heavy against lite, from two kept gate runs of the same slice:
python3 -I evals/tools/compare_arms.py evals/results/gate-<ts>-tdd-implementation-cancel-hold.json \
  evals/results/gate-<ts>-tdd-implementation-lite-cancel-hold.json --task docs/cancel-hold/design.md
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
is to commit. Inside Linux or macOS run `python3 -I
evals/tools/eval_gate.py` directly. Windows itself cannot run it (below).
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

**Last result** is the most recent score. **Current** says whether that score
still describes the code: a case goes stale the moment its `AGENT.md` or
`SKILL.md` changes, or its own fixtures/graders are edited. A stale case's
score is history, not a claim about today.

| Case | Last result | Current? |
|---|---|---|
| `orchestrator-security-stage` | real, Sonnet: 2/2 runs all pass (`results/20261011-orch-cal2`); baseline fails routing and writes no log — "what's next?" on a real planning folder fires the orchestrator, which routes to `security-requirements` by invoking the skill, passes the save location, writes the log at routing time, and the persona asks its questions. Phase E (2026-10-15): the design doc's "Open for devsecops-engineer" section is gone; routed from the slice placeholders alone, 3/3 runs | yes |
| `orchestrator-superseded-scope-map` | real, Sonnet: 2/2 runs all pass — real inspection: reads `## Status` and routes to requirements for the Active map's step 1, not to slicing from the superseded map's requirements doc. The baseline also routes correctly here, so this is a regression guard on inspection, with the skill-invocation graders as the plugin-fired check | yes |
| `orchestrator-backward-route` | real, Sonnet: 2/2 runs all pass, again after `vertical-slicing` gained its stop-first rule (`results/rrf-*`) — a "Handed back to product-slicer — blocking" section routes to `product-slicer`, not forward to reliability criteria; the log records why. Phase E (2026-10-15): receipt hand-back; its grader had kept the refund wording and failed one run that routed correctly and chose growth with reasons; reworded, 3/3 twice | yes |
| `orchestrator-asks-for-target` | real, Sonnet: 2/2 runs all pass; baseline 0/1 — no folder given, it asks where the artifacts are before anything else and doesn't search the project | yes |
| `orchestrator-route-problem-framing` | real, Sonnet: 10/10 over 2 runs (`results/g8-*`) — a new, empty planning folder: routes to `problem-framing-doc`. The first version left the folder empty on disk; an empty directory doesn't reach the sandbox, so the orchestrator searched for it and stopped. The prompt now says the folder is new | yes |
| `orchestrator-route-scope-decision` | real, Sonnet: 9/10 over 2 runs (`results/g8-*`) — a problem doc and nothing else: routes to `scope-map` to decide whether a map is needed. Known miss 1/2: once `scope-map` decided no map, the orchestrator went straight on to `requirements-refinement` without asking, against step 5's never-chain-silently rule. Four attempted fixes each caused a worse regression elsewhere and were reverted (see findings) | yes |
| `orchestrator-route-slicing` | real, Sonnet: 10/10 over 2 runs (`results/g8-*`) — problem plus an Active requirements doc: routes to `vertical-slicing` | yes |
| `orchestrator-route-user-story` | real, Sonnet: 10/10 over 2 runs (`results/g8-*`) — a slice not yet written up: routes to `user-story-writeup` | yes |
| `orchestrator-route-design` | real, Sonnet: 9/10 over 2 runs (`results/g8-*`) — a user story and no design: routes to `architecture-design`. The miss was the grader: it forbade any `security-requirements` call, and `architecture-design` legitimately consults it inline; that check is now `not-tdd-implementation`, which both runs pass | yes |
| `orchestrator-route-reliability` | real, Sonnet: 12/12 over 2 runs (`results/g8-*`) — a non-UI cancel-hold slice with security filled and reliability a placeholder (`route-plants/cancel-hold-reliability-open/`): routes to `reliability-requirements` | yes |
| `orchestrator-route-design-system` | real, Sonnet: 16/18 over 3 runs (`results/gate-20261014T200227`; 12/12 over 2 runs in `results/g8-*`) — a UI slice with both runtime-safety criteria filled and no design system: routes to `design-system`. Since 2026-10-14 one run in three routes to `reliability-requirements` instead: the shared slice fixture lists its security and reliability criteria unlabeled among the functional ones, so "filled" is a judgment call (F1 in `TODO.md`); the bar is recorded as it scores | yes |
| `orchestrator-route-screen-design` | real, Sonnet: 12/12 over 2 runs (`results/g8-*`) — a design system but no screen design: routes to `screen-design` | yes |
| `orchestrator-route-accessibility` | real, Sonnet: 12/12 over 2 runs (`results/g8-*`) — a screen design with the accessibility criteria a placeholder: routes to `accessibility-review`. Phase E (2026-10-15): the screen design no longer names `accessibility-engineer`; 3/3 runs | yes |
| `orchestrator-route-tech-bootstrap` | real, Sonnet: 10/10 over 2 runs (`results/g8-*`) — the fully specified cancel-hold slice in a repo with no stack: routes to `technology-bootstrap` | yes |
| `orchestrator-route-implementation` | real, Sonnet: 9/10 over 2 runs (`results/g8-*`) — the same slice in the library app: routes to `tdd-implementation` through the quarantine flow (not exercised). The miss was the grader demanding the log mention the stack, which the skill's own log template doesn't; loosened, both kept logs pass a re-ask (a hint) | yes |
| `orchestrator-route-implementation-prenamed` | real, Sonnet: 0/3 then 3/3 at 1.0 (`results/gate-20261018T160908`, then `gate-20261018T161403`) — G1 (2026-10-18), from H6's second session: the same slice with "if the next step is the implementation and its quarantine flow, go ahead with it". Before the fix every run invoked `tdd-implementation` directly, inline, with no orchestrator, no log and no sandbox check. The orchestrator's and `tdd-implementation`'s descriptions now say a stage guessed at while asking to move forward is not a skill named; after it all three runs route through the orchestrator, write the log, and stop at the sandbox check with nothing built. No baseline arm | yes |
| `orchestrator-route-backward-requirements` | real, Sonnet: 12/12 over 2 runs (`results/g8-*`) — `slice-000` says no requirements pass ran for its step (`route-plants/backward-pm/`): routes back to `requirements-refinement` for that step, not on to its user story. Phase E (2026-10-15): `slice-000` no longer names `requirements-refinement` or `product-manager`, only that nobody confirmed the step's WHAT; 3/3 runs | yes |
| `architecture-design-payfine-phase1` | real, Sonnet: 1/1 with plugin on both passes (`results/20261011-sa-p1f-architecture-design-payfine-phase1`); the baseline writes the design straight away — the pay-a-fine slice before design, with the engineer's generic `PaymentGateway` registry proposal: presents it as a decision, recommends against it (one provider; `FinePayments` already isolates Stripe), and waits | yes |
| `architecture-design-payfine-phase2` | real, Sonnet: 33/36 over 3 runs (`results/gate-20261014T193600`), re-frozen 2026-10-14 from a phase-1 run on the current skill text — the user overrules (a second provider is signed), approves the rest; the saved design states its importance ordering, stays conceptual, records each decision's approval, names what crosses its boundaries, builds the approved gateway on the existing `CollectFine` path, notes the leaky payment port (V7) and doesn't call the one-implementation port premature. Known miss 1/3: `decisions-show-approval`. Graded on the saved file. No baseline arm | yes |
| `architecture-design-neg-review` | real, Sonnet: never invokes `architecture-design` in either arm (a review of live code) | yes |
| `technology-bootstrap-phase1` | real, Sonnet: 1/1 with plugin on three passes; the baseline also asks first, so this phase is a regression guard — an empty repo with slice 1's artifacts in `docs/` (`fixtures/bootstrap-empty/`): asks who maintains it and what kind of app before recommending anything | yes |
| `technology-bootstrap-phase2` | real, Sonnet: 18/18 over 3 runs (`results/gate-20261014T193600`) — the answer delegates the test runner and package manager, never mentions a UI framework, and asks for the whole set in one message (two runs in three had followed the one-at-a-time loop literally, which the graders read as a miss); the package manager is picked on its pinning posture after an inline `supply-chain-review` consult (no `Agent`/`Task` spawn, no reflexive `security-requirements` consult), and every run argues the UI framework is not forced by a domain-level first test and leaves it open | yes |
| `technology-bootstrap-phase3` | real, Sonnet: 15/15 over 3 runs (`results/gate-20261014T195625`), re-frozen 2026-10-14 — the user approves the set, deferring the UI framework included; the saved bootstrap decides only what the first test forces, records how each choice was settled with its rejected alternatives (the template's own section), leaves persistence and the UI framework open with reasons and owners, and writes nothing else (no scaffolding). Graded on the saved file; what phase 2 already said is not re-graded. No baseline arm | yes |
| `technology-bootstrap-phase3-reject` | real, Sonnet: 18/18 over 3 runs (`results/gate-20261014T200227`) — the chain's rejecting answer: "npm and Jest, I know them"; the saved bootstrap records both as the user's choices with their reason and the recommendations as declined, restates the pinning posture for npm (`npm ci` as a habit, `.npmrc` to recover the rest) instead of dropping it, and proceeds without re-arguing. Same frozen phase 2 as phase 3. No baseline arm | yes |
| `requirements-refinement-payfine-phase1` | real, Sonnet: 13/15 over 3 runs (`results/gate-20261014T201609`; 14/15 and 15/15 on earlier batches the same day); baseline 2/3 in calibration (writes technical design into the answer) — the pay-a-fine problem doc only, asked to "work out exactly what we want built": asks what to build before writing, asks for the trade-off and the rejected alternatives (3/3 on every batch), doesn't ask what the problem doc or code answers (the misses, one run in three) | yes |
| `vertical-slicing-payfine-phase1` | real, Sonnet: 17/18 over 3 runs after the stop-first rule (`results/rrf-*`), the miss a grader that read "paid or waived fines don't show as outstanding" as adding waivers; reworded, and all three kept slices pass it with the eval's judge model; baseline 4/5 in calibration (no separate security and accessibility placeholders) — problem plus Active requirements, saves `slice-001.md`: stays inside "confirmed in scope", both placeholders, slice set named, doesn't re-ask the WHAT | yes |
| `acceptance-criteria-payfine` | real, Sonnet: 9/9 over 3 runs; the baseline passed in calibration, so this is a regression guard — the engineer's "handles errors gracefully": rejected as untestable, and the undecided non-decline failures are flagged or routed to the reliability placeholder, not settled in the rewrite. Phase E (2026-10-15): the criterion is now "Paying a fine is quick; the member isn't left waiting" (the old one was the skill's own worked example); 9/9 over 3 runs, the time bound flagged or routed to the reliability placeholder every time | yes |
| `problem-framing-doc-payfine` | real, Sonnet: 14/15 over 3 runs; the baseline passed in calibration, a regression guard — the user's own description with "add a pay button" in it: no solution in the doc, Stripe and one-developer as constraints. Known miss 1/3: an unstated "in-person payment must keep working" listed as a constraint beside a related open question | yes |
| `scope-map-self-service` | real, Sonnet: 14/15 over 3 runs; the miss is borderline, not a clear judge error: the map routes privacy to each step's requirements pass, but through one blanket line covering its whole cross-cutting list. The eval's judge failed it 3/3; `tools/rejudge.py` passes it 8/8, which is a hint only. Baseline misses the privacy routing on both calibration passes — a new, larger problem (`planning/self-service/`: fines, holds, contact details) whose privacy constraint is worded around one step. Phase E (2026-10-15): the problem doc's sentence generalising the privacy constraint for the skill is gone; privacy still routed to every step's requirements pass, 15/15 | yes |
| `user-story-writeup-payfine-phase1` | real, Sonnet: 9/9 over 3 runs; baseline fails on both calibration passes (writes the story or fills the security placeholder) — asked to make slice 1 "ready to track", asks whether and where to file before writing. Before the fix the skill never fired: the run filled the slice's security placeholder instead | yes |
| `user-story-writeup-payfine-phase2` | real, Sonnet: 15/15 over 3 runs (`results/rrf-*`) — resumes phase 1 with "GitHub, save it here, I'll paste it in": writes the story to the given path as a user story, carries the three criteria and both placeholders as they are, invents no issue number or assignee, and doesn't file it | yes |
| `requirements-refinement-payfine-phase2` | real, Sonnet: 24/27 over 3 runs (`results/gate-20261014T201657`), re-frozen 2026-10-14 twice (the skill changed under it, see findings) — resumes phase 1 with the user's answers (pay online now, not see-only; payment link rejected; one fine, no saved cards; nothing about staff, whose part phase 1 had asked about): template sections, the user's own trade-off, scope as confirmed, both constraints as consequences, findings that name what is forced without prescribing the change. Every run writes a "Not yet confirmed" section and two of three put the staff view in it; the misses are the final message re-asking a long list of open items, which the judge reads as re-asking (one run clean) | yes |
| `vertical-slicing-no-requirements` | real, Sonnet: 12/12 over 3 runs; baseline fails on both calibration passes (cuts the slice) — problem doc only, and the user says "just decide, we don't need to talk it through": writes nothing and hands back to `requirements-refinement`. Before the fix the skill read its own stop rule and cut the slice anyway, with a note that the scope was its own judgment |
| `vertical-slicing-handback` | real, Sonnet: 15/15 over 3 runs (`results/20261011-hb-final`, and again after the stop-first rule, `results/rrf-*`); baseline fails on both calibration passes (edits the Active requirements doc and writes the refund slice in full) — the `pay-fine-handback` folder, where the security pass hands back "members have no refund path": owns the decision, cuts a separate refund slice rather than growing slice 1, sends its WHAT to a requirements pass, and leaves the requirements, design and security documents to their owners. Before the fix the skill grew slice 1, wrote the refund requirement itself and authored security criteria for it. After the fix `vertical-slicing-payfine-phase1` re-ran 18/18 and `orchestrator-backward-route` 2/2. Phase E (2026-10-15): the hand-back is now a receipt the merchant agreement requires (the refund scenario was the skill's own example, and the fixture no longer lists the options). First run 13/15: one run never invoked the skill and wrote the receipt slice in full, the baseline failure; the skill's description now names a hand-back as a trigger, and the re-run is 15/15 | yes |
| `adr-payment-gateway` | real, Sonnet: 11/12 over 3 runs (`results/20261011-dw-final-*`); baseline fails no-how — a real decision (provider-neutral payments, Adyen at the desk) told with file paths and class names: decision, alternatives with reasons, honest downsides, none of the how. Known miss 1/3: the Context names the `FinePayments` port | yes |
| `adr-neg-rename` | real, Sonnet: 6/6; baseline writes the ADR — a field rename asked for as an ADR: runs the three checks and declines. Before the fix the skill fired and asked how to scope the ADR instead | yes |
| `why-comments-collect-fine` | real, Sonnet: 15/15; the baseline passed in calibration, a regression guard — four planted comments in `fines/collect-fine.ts` (D1, D2, DT1, case-only overlay): deletes the WHAT comments, flags the one that contradicts the retry loop, keeps the WHY, stays off the code | yes |
| `pr-writeup-portal-fines` | real, Sonnet: 12/12; baseline misses the ticket question and the AI role — a finished `/portal/fines` diff written by Claude Code: accurate plain-language description, asks about a ticket instead of assuming, names the tool and its role | yes |
| `user-facing-docs-renewals` | real, Sonnet: 12/12; the baseline passed in calibration, a regression guard — members' help page for portal renewals: two renewals, 21 days from the renewal day, nothing the code doesn't do. Before the fix it invented a "My Loans → Renew" click path and "no late fines"; one run didn't fire until the description said "help page". The no-click-path grader was dropped after failing plain pages twice | yes |
| `staleness-audit-docs` | real, Sonnet: 17/18; baseline misses restated code and ceremony — a planted `docs/` (D3–D6, DT2, DT3): stale lending rules, a code-narrating page, a sign-off log, an ADR the code overturned; keeps the waiver doc and the still-true Stripe ADR. Known miss 1/3: proposes a required-reviewers gate after deleting the sign-off log | yes |
| `tdd-implementation-cancel-hold` | real, Sonnet: 53/54 over 3 runs (`results/g4-*`); baseline fails every process check in calibration (no Test List, no RED, no review, writes the code first) — the approved cancel-a-hold design built test-first, graded mechanically on the full trace (`regex`/`tool_order`) and on the written files: tests before code, RED runs seen, a `test-quality-review` call every cycle, last run green, design doc ends unchanged, nothing outside the slice touched; the reason wording decided and named, notification left to its owner. The main agent no longer edits the design doc before invoking the skill (0/3, was 2/3) since the description says to leave its open questions to the skill. Known miss: one report without its Test List | yes |
| `tdd-implementation-named-fix` | real, Sonnet: 3/3 runs clean (`results/g4-*`); baseline makes the edit and writes no tests in calibration — V15 handed back as a review finding: `LoanStore` through the constructor, `main/server.ts` updated, behaviour unchanged and pinned by new tests that run green, nothing else touched, honest about tests coming after the structural change. Before the trigger fix the skill fired in 1 of 4 runs | yes |
| `tdd-implementation-cancel-hold-via-agent` | real, Sonnet: 48/60 over 4 runs (`results/k1-*`, after `tdd-coach`'s `AGENT.md` was cut to the persona and a pointer to its skills; 23/30 before, so no measurable change), delegation to `tdd-coach` confirmed. The parent no longer touches the design doc before delegating. `red-runs-seen` fails every agent run, but it counts failing runs (four or more), not tests: the agent saw 4–6 distinct tests fail before passing, the same as the direct path, and runs fewer repeat runs while red. The real agent-path miss is judgment: in 3/4 runs the subagent settles the notification question itself ("no notification is sent", reasoned from the code) instead of leaving it to the design's owner, which the direct path does 3/3. Also once each: a skipped review in a cycle, open questions written into the design doc | yes |
| `tdd-implementation-lite-cancel-hold` | real, Sonnet, G2 (2026-10-18/19): the same slice built with `tdd-implementation-lite`, test-first with verification rather than TDD. Graders marked floor (what lite tells the model) or measurement (what only heavy prescribes). First lite, nothing said about verification: 0.92, every floor grader 3/3, every RED a missing-module import, the can-fail check 0/6; the blind judge (`tools/compare_arms.py`) preferred it over heavy 9/9 for broader tests. Augmented lite (tests, then stubs so the RED fails on assertions, implement, green, deliberate break caught and restored): 0.95–0.96 over three runs of three, `red-on-assertions`, `break-and-restore-in-trace`, `tests-before-any-code` and `map-query-before-any-code` 6/6 under Node's regex engine, six or seven tests per run; preferred over heavy 9/9 again. The only grader lost in any run is the per-test cycle lite does not ask for | no (bars below 1.0 by design: the measurement graders) |
| `tdd-implementation-lite-named-fix` | real, Sonnet, G2: the V15 fix with `tdd-implementation-lite`; 15/15 in every run of every pass (the fix, behaviour pinned by tests that run for real, honest about the order, nothing else touched, the final reviewers, and the break-and-restore once lite asked for it); against heavy the blind judge called it a wash (identical code, one extra assertion deciding the non-ties either way) | yes |
| `tdd-implementation-lite-cancel-hold-via-agent` | real, Sonnet, G2: the lite build delegated to `tdd-coach`, told to build with the lite skill; same graders as the direct case with the skill checked in the delegated agent's trace. The agent path is where the contract misses showed: reviewers skipped as "small change, self-checked" in two runs and the consult skipped in one, fixed in the lite text (and the agent's workflow summary, which prescribed the TDD loop to every build, now describes heavy and lite separately); 0.96 after, the four exact graders 6/6; preferred over heavy 9/9 by the blind judge | no (as above) |
| `test-quality-review-fines` | real, Sonnet: 3/3 runs clean; baseline misses the call-order test (calls it "correct") and the untested `percentOf` — the planted `test/fines.test.ts` (Q1–Q5): subject's own method mocked, unwired mock, weak cap assertion, call-order assertion, untested export; traps: a designated fake stubbed per test, exact assertions. The skill didn't fire until its description named "are these tests actually testing anything?". Phase E (2026-10-15): the prompt no longer quotes the description ("I'm not confident it would catch a real bug"); the skill fired in 6/6 runs. `no-false-alarm-exact-tests` then lost 3/3 to reviews that called the sound tests thin and suggested boundary cases; the criterion now fails only a genuine false alarm, 29/30 after | yes |
| `test-quality-review-reminders` | real, Sonnet: 2/3 runs clean, the third a last-message artifact (the review was complete; the final message is a postscript about a stopped background task); the baseline passed in calibration, a regression guard — the app's own reminder tests: the untested email channel, no false alarm on constructor-injected fakes, "sound but incomplete" | yes |
| `test-quality-review-neg-code-review` | real, Sonnet: never invokes `test-quality-review` (a readability request) | yes |
| `code-review-fine-notices-pr` | real, Sonnet: 2/3 runs clean, the third the same postscript artifact; baseline grades the over-mocked test as its own finding — triplicated notice logic without flagging the guard clause, a false "whole dollars" comment, a name that says count but sums ranked above a vague one, a WHAT comment, duplicate test names; keeps the WHY comment; `why-comments` consulted via `Skill` | yes |
| `code-review-fines-report-pr` | real, Sonnet: 13/15 over 3 runs, 1/3 clean (`results/20261011-final-*`) — a `run()` doing several jobs, member rules in a report class (feature envy), a year/month data clump, the month format with no owner; the Stripe SDK named for `architecture-review`. Feature envy was missed in every run (both arms) until the skill gained a sweep-every-function step and the plant changed from a formatter (which reviews rightly passed) to misplaced business rules. Known misses: the month format (2/3), feature envy (2/3) | yes |
| `code-review-days-left-pr` | real, Sonnet: 27/30 over 3 runs (`results/m5-*`); in calibration the baseline missed two or three of the four plants on each pass — a days-left PR reviewed with no hint about size: an options parameter nothing passes or reads, a flag nothing sets, a null check the type rules out, a catch that only rethrows (answer key `CB1`–`CB4`); traps: two branches the tests pin and reuse of `daysBetween` (`CBT1`–`CBT3`). Before the description put "invoke first" and the general-review trigger at its start, `code-review` never fired on "review it before I merge"; it now fires 2/3. Misses: the impossible-null check in two runs | yes |
| `code-review-catalog` | real, Sonnet: 3/3; the baseline passed in calibration, a regression guard — the clean module, nothing above Low | yes |
| `code-review-neg-architecture` | real, Sonnet: never invokes `code-review` (a dependency-direction question) | yes |
| `code-review-fine-notices-pr-via-agent` | real, Sonnet: 2/2 runs clean, delegation to `code-reviewer` confirmed | yes |
| `map-update-cancel-hold` | real, Sonnet: 27/27 over 3 runs (one run's scratch script in the sandbox's temp dir was counted against it until the grader limited itself to project files); baseline attaches severity in calibration — after the cancel-hold slice lands, regenerates `docs/architecture-map.md` with no path given: new rows faithful, tiers carried forward, `utils/` untiered, the new tier-1 → tier-3 edge and the untiered edge flagged without verdicts, the shared `roundHalfUpCents` flagged, pre-existing candidates not reported as new, no app code touched. Before the template fix one run called the duplicate "fresh rather than intentional" | yes |
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
| `security-requirements-payfine-phase1` | real, Sonnet: 7/9 over 3 runs (`results/gate-20261014T193255`; 9/9 on the batch before it the same day), 0/1 without on both calibration passes — given the pay-a-fine slice and the engineer's "let members onto `/fines`" proposal, asks about obligations and who may see whose data, and does not ask how members sign in or which provider handles payment (the misses: asking whether the browser tokenises with Stripe.js, which the code implies) | yes |
| `security-requirements-payfine-phase2` | real, Sonnet: 11/12 over 3 runs (`results/gate-20261014T195625`), re-frozen 2026-10-14 — every run stops at the forks: the shared-route proposal presented as a decision (it would expose staff-only waiving and skip the ownership check), nothing marked approved, no criteria written before approval, no false alarm on the publishable key. Before the skill said approval comes before the document, every run wrote the whole document with its decisions pending and the judge failed two in three on a three-thousand-word message. No baseline arm: the history is a with-plugin transcript | yes |
| `security-requirements-payfine-phase2-proceed` | real, Sonnet: 12/12 over 3 runs (`results/gate-20261018T160908`) — G1 (2026-10-18): the stop rule tested against its own restraint. Same frozen phase 1 as phase 2 and the stop case; the answer carries an obligation (any online charge matchable to the fine it paid; disputes answered within 14 days, by finance, by hand from Stripe's dashboard) that reads like the stop case's but is not one: the ledger already records the charge id on settlement, and disputes are finance's process. All three runs presented the forks, placed matching in the criteria and disputes out of scope, and handed nothing back. No baseline arm | yes |
| `security-requirements-payfine-phase3` | real, Sonnet: 27/27 over 3 runs (`results/gate-20261014T194332`), re-frozen 2026-10-14 — the user keeps the shared route; the saved document writes the criteria for it and makes it safe (members pay only their own fines, cannot waive), records the overrule with its risk once and every other decision as approved, card data never received, error and monitoring exits covered. Graded on the saved file | yes |
| `security-requirements-neg-review` | real, Sonnet: never invokes `security-requirements` in either arm (a review of live code) | yes |
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
| `reliability-requirements-payfine-phase1` | real, Sonnet: 8/9 over 3 runs (`results/gate-20261014T193255`), 0/1 without on both calibration passes — same slice with the engineer's "show 'failed, try again' after 10 s" proposal; asks what an hour down costs, the target and who notices, not what the code says (the 1/3 miss asks whether staff can see Stripe's dashboard) | yes |
| `reliability-requirements-payfine-phase2` | real, Sonnet: 11/12 over 3 runs (`results/gate-20261014T195625`), re-frozen 2026-10-14 with the case's own tools (the old history held an `Agent` call the case forbids) — every run stops at the forks: names the duplicate charge a timed-out retry can cause and leaves its handling pending, writes no criteria yet, no retry of declines. No baseline arm | yes |
| `reliability-requirements-payfine-phase2-proceed` | real, Sonnet: 12/12 over 3 runs (`results/gate-20261018T162629`; 9/12 under the first wording) — G1 (2026-10-18): same frozen phase 1 as phase 2 and the stop case; the answer names the day-long outages but says the desk takes payment by phone for a member who can't wait, so there is no gap. All three runs presented the forks and handed nothing back. The first wording of the outage grader failed every run for not naming the outage as a failure mode; the forks turn need not list every failure mode (the document does), so the grader now fails only an invented scope gap: 9/9 on the recorded outputs, 3/3 on the re-run. No baseline arm | yes |
| `reliability-requirements-payfine-phase3` | real, Sonnet: 27/27 over 3 runs (`results/gate-20261014T194332`), re-frozen 2026-10-14 — the user keeps "show failed" and refunds duplicates by hand, against a phase 2 that recommended preventing them; the saved document records the overrule and every other decision as approved, writes the criteria for the user's choice, makes duplicates findable for the refund, catches charge-without-settle, covers double submit, separates declines from faults, no retry of declines. Graded on the saved file | yes |
| `reliability-requirements-neg-review` | real, Sonnet: never invokes `reliability-requirements` in either arm (a review of live code) | yes |
| `reliability-review-nightly` | real, Sonnet: 7/8 with plugin vs 5/8 without, 1 run (`results/g3-*`, after the missing-retry rule) — unhandled rejection from the timer-driven job, no per-loan isolation, a database pool leaked per run, a mailer with no timeout, a postal adapter that swallows failures; traps: the reminder loop's catch, re-run idempotency, a correct transient-only SMS retry. The miss folds per-loan isolation into its crash finding (a re-ask passes it, a hint only). The pool leak was missed in two of six earlier calibration runs | yes |
| `reliability-review-nightly-via-agent` | real, Sonnet: 7/8 with plugin (`results/g3-*`), delegation to `devsecops-engineer` confirmed via `Agent`; the miss is the re-run trap, failed on a correctly scoped overlapping-runs race (the probe case in the findings showed the eval's judge failing this text as a last message and passing it as a file); the no-plugin arm (0/5 finds) is not a comparison, the agent doesn't exist without the plugin | yes |
| `reliability-review-http` | real, Sonnet: 5/5 with plugin vs 2/5 without, 1 run (`results/g3-*`) — expected and unexpected failures conflated in `respond.ts`, unbounded loan history, holds kept only in memory; traps: the catalog route's 503 handling, the capped search. Unbounded history and in-memory holds each missed once across calibration. Phase E (2026-10-15): the dependency-failure and data-growth hint dropped from the prompt; 3/3 runs, all three plants found | yes |
| `reliability-review-alerts` | real, Sonnet: 3/3 both arms, 1 run (`results/g3-*`; was 3/3 vs 2/3) — page on any error event, non-actionable CPU page; trap: multi-window burn-rate alerts with a runbook. Now a regression guard | yes |
| `reliability-review-portal-pay-pr` | real, Sonnet: 3/3 runs clean, 24/24 (`results/gate-20261018T160908`) — G1 (2026-10-18), the first plant whose defect only shows across files (overlay `code-plants/reliability-review/portal-pay/`, answer key R14, R15, RT10, RT11): a PR adding pay-a-fine to the portal, whose use case charges with an idempotency key the port's comment promises will stop a repeat charge, while the Stripe adapter sends it as a `metadata` label the SDK types say Stripe never reads; the route's "please try again" on a timeout then double-charges. Every run read both sides and the vendor types, found the key ineffective and the charge abandoned at the timeout, and left the bounded wait and the shared 404 alone. No baseline arm | yes |
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
| `accessibility-review-payfine` | real, Sonnet: 35/36 over 3 runs (`results/g9-*`, after the state-contrast rule; was 36/36); baseline 10/11 in calibration, a regression guard, not evidence of uplift — the declined-state mockup with the textbook plants (A1–A4, AT1–AT3). The miss: one run's criteria don't separate checkable-now from needs-real-code | yes |
| `accessibility-review-payfine-subtle` | real, Sonnet: 25/27 over 3 runs (`results/g9-*`); in calibration both arms missed only the hover plant on two passes; once the state rule reached the markup-only fallback the plugin found it and the baseline didn't — the card-error mockup built on the design system (A5–A8, AT4–AT6): a component rule that strips the Pay button's focus ring, a link that fails contrast only on `:hover` (3.73:1), an error tied to a misspelled id, a name label hidden with `display: none`; traps: an input focus ring replaced correctly, an `.sr-only` hint, a native radio group. The hover plant is the uplift: found 2/3 with the plugin, 0/2 without. Misses: one run without the hover finding; one disputed false-alarm vote on a review that says the inputs do show focus | yes |
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

### Run backlog

Emptied: the eight emulated cases it listed were all run, then replaced by
real cases and deleted (the table is in git history).

### Known coverage gaps

- **Persona rules the orchestrator can't reach.** The orchestrator now
  invokes a routed skill and never reads the persona's `AGENT.md`, so any
  rule a routed step needs must be in the skill. `devsecops-engineer`,
  `software-architect`, `product-manager`, `product-slicer` and
  `docs-writer`, `tdd-coach`, `code-reviewer`,
  `architecture-cartographer`, `ux-designer` and `accessibility-engineer`
  have had that pass, so every persona has. Keep it that way: a new
  persona rule goes in the skill, not only the `AGENT.md`.
- **The `tdd-implementation` quarantine flow has no case.** The real cases
  invoke the skill directly and through the `tdd-coach` agent; the
  orchestrator's quarantine/grade/combine/finalize flow (two worktree
  candidates, parallel reviewers) needs the `Agent` tool and up to
  eighteen reviewers, which no eval case can run. It is proven by real
  execution instead: twice so far, both in a sandboxed WSL2 session
  (H6, 2026-10-18, heavy; I, 2026-10-19, compare, with the handed-back
  round in E exercised end to end), each read against the hand-off's
  watch list from the stream-json logs and the audit transcripts, each
  producing skill-text and script fixes that the orchestrator cases then
  regression-check. The accounts are under H6 and I in `TODO.md`; the
  recipe for the next run is in the hand-off.
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
