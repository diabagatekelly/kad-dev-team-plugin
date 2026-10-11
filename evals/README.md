# Evals

`claude plugin eval` is out of early access and confirmed working. This
directory holds two kinds of case, and it matters which kind you're looking
at:

- **Emulated cases** — the original set, one `prompt.md` bundling several
  `graders/*.md` per skill trigger, run via the homegrown
  `.claude/skills/agent-eval` stand-in (a fresh general-purpose agent
  role-plays the persona; see each case's `eval-score/summary.md`). Built
  before the real CLI was available; never run against it. Case names
  follow `agent:skill` for persona-backed triggers, or just `skill` for a
  skill with no owning persona (e.g. `orchestrator`).
- **Real cases** — `case.yaml` per case, executed by `claude plugin eval`
  as a genuine child `claude` process per run, with a no-plugin baseline
  arm (`--ablation with-without`). Today that is the `library-app-*` suite
  for `software-architect:architecture-review` plus two
  `architecture-review-neg-*` trigger cases, and the `security-review-*`
  suite for `devsecops-engineer:security-review` (five cases on the same
  fixture plus two negative trigger cases), followed by the
  `reliability-review-*`, `supply-chain-review-*`,
  `operational-readiness-*`, `security-requirements-*` and
  `reliability-requirements-*` suites on the same fixture, and the code
  personas' `tdd-implementation-*`, `test-quality-review-*`,
  `code-review-*` and `map-*` cases (their plants are case-only overlays in
  `fixtures/library-app/code-plants/`), and the UI personas'
  `design-system-*`, `screen-design-*` and `accessibility-review-*` cases
  (overlays in `fixtures/library-app/ui-plants/`). Results land in
  `evals/results/<timestamp>/` (gitignored) each time the suite runs;
  nothing is hand-copied into case directories.

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
reasons).

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
included) is ignored, see "Interactive skills" below. A full pass costs about $7.50 at
`--runs 1` plus about $2 for the pairwise judge; the suite's `runs: 3`
default triples the first number.

Each case tests one skill trigger: does the right skill get invoked
(`tool_used` grader), and is the output actually correct (`llm` grader).

**Two-phase cases.** If a persona's correct behavior is to ask a clarifying
question, `agent-eval` runs a second phase: it supplies a scripted answer
(from the case's `## Scripted answers` section) and re-invokes the persona
to get the actual finished artifact — a real invocation would ask via
`AskUserQuestion` and keep going in the same turn; a single-phase run can't
model that; grading only the question would validate "did it ask" and never
"did it finish the job." `eval-result/phase1-question.md` holds the
question, `eval-result/output.md` holds the final artifact. Graders default
to grading the final artifact; a grader with `target: phase1` in its
frontmatter grades the question instead (used for the "did it ask" checks).

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
5. **Fix the skill only for a failure that survives step 4**, re-run the
   affected cases, and record the finding in this README's findings list
   and the persona's `PERSONAS.md` row.
6. **Keep run output out of git.** `results/` is ignored; the coverage
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
2. **Freeze it.** Run phase 1 with `--keep-temp --json <file>`, take the
   kept directory (the parent of `out/` in the run's `tracePath`) from a run
   whose question is a good one, and run
   `tools/freeze-history.sh <kept-dir> evals/<phase-2-case>/history.jsonl`.
   A resumed phase (2 onward) writes its transcript next to its own
   `history.jsonl` instead, one branch per run; freeze it with
   `tools/freeze-history.sh evals/<case>/<session>.jsonl <next>/history.jsonl
   "<text from the chosen run's final message>"`.
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
   until the earlier phase is re-run and re-frozen.

Answers arrive as a user message rather than an `AskUserQuestion` result,
which is the one fidelity gap. This replaces the `.claude/skills/agent-eval`
stand-in for the two-phase and approval-loop cases below; the emulated
cases in the table are the backlog, and each one's `prompt.md` already names
the plants a `library-app` case would need.

## Coverage

Case names follow `agent:skill` for persona-backed triggers, or just
`skill` for a skill with no owning persona (e.g. `orchestrator`).

**Last result** is the most recent score. **Current** says whether that score
still describes the code: a case goes stale the moment its `AGENT.md` or
`SKILL.md` changes, or its own fixtures/graders are edited. A stale case's
score is history, not a claim about today.

| Case | Last result | Current? |
|---|---|---|
| `docs-writer:problem-framing-doc` | 3/3 PASS | stale — persona rules moved into the skill; not re-run, the real case below covers phase 1 |
| `docs-writer:scope-map` | 5/5 PASS, inline | stale — persona rules moved into the skill; not re-run, the real case below covers phase 1 |
| `docs-writer:adr` | — | superseded by the real case below |
| `docs-writer:why-comments` | — | superseded by the real case below |
| `docs-writer:user-story-writeup` | 3/3 PASS, two-phase | stale — persona rules moved into the skill; not re-run, the real case below covers phase 1 |
| `docs-writer:pr-writeup` | — | superseded by the real case below |
| `docs-writer:user-facing-docs` | — | superseded by the real case below |
| `docs-writer:staleness-audit` | — | superseded by the real case below |
| `product-manager:requirements-refinement` | 6/6 PASS, two-phase | stale — persona rules moved into the skill; not re-run, the real case below covers phase 1 |
| `product-slicer:vertical-slicing` | 6/6 PASS, two-phase | stale — persona rules moved into the skill; not re-run, the real case below covers phase 1 |
| `product-slicer:acceptance-criteria` | 2/2 PASS, inline | stale — persona rules moved into the skill; not re-run, the real case below covers phase 1 |
| `orchestrator` | 15/15 PASS, skill-only | yes — kept as the broad check on the routing table (13 described directories, dry run); the real cases below cover what it can't |
| `orchestrator-security-stage` | real, Sonnet: 2/2 runs all pass (`results/20261011-orch-cal2`); baseline fails routing and writes no log — "what's next?" on a real planning folder fires the orchestrator, which routes to `security-requirements` by invoking the skill, passes the save location, writes the log at routing time, and the persona asks its questions | yes |
| `orchestrator-superseded-scope-map` | real, Sonnet: 2/2 runs all pass — real inspection: reads `## Status` and routes to requirements for the Active map's step 1, not to slicing from the superseded map's requirements doc. The baseline also routes correctly here, so this is a regression guard on inspection, with the skill-invocation graders as the plugin-fired check | yes |
| `orchestrator-backward-route` | real, Sonnet: 2/2 runs all pass — a "Handed back to product-slicer — blocking" section routes to `product-slicer`, not forward to reliability criteria; the log records why | yes |
| `orchestrator-asks-for-target` | real, Sonnet: 2/2 runs all pass; baseline 0/1 — no folder given, it asks where the artifacts are before anything else and doesn't search the project | yes |
| `architecture-design-payfine-phase1` | real, Sonnet: 1/1 with plugin on both passes (`results/20261011-sa-p1f-architecture-design-payfine-phase1`); the baseline writes the design straight away — the pay-a-fine slice before design, with the engineer's generic `PaymentGateway` registry proposal: presents it as a decision, recommends against it (one provider; `FinePayments` already isolates Stripe), and waits | yes |
| `architecture-design-payfine-phase2` | real, Sonnet: 27/27 over 3 runs (`results/20261011-sa-final-architecture-design-payfine-phase2`) — the user overrules (a second provider is signed), approves the rest; the saved design states its importance ordering, stays conceptual, records each decision's approval, names what crosses its boundaries, builds the approved gateway on the existing `CollectFine` path, notes the leaky payment port (V7) and doesn't call the one-implementation port premature. Graded on the saved file. No baseline arm | yes |
| `architecture-design-neg-review` | real, Sonnet: never invokes `architecture-design` in either arm (a review of live code) | yes |
| `technology-bootstrap-phase1` | real, Sonnet: 1/1 with plugin on three passes; the baseline also asks first, so this phase is a regression guard — an empty repo with slice 1's artifacts in `docs/` (`fixtures/bootstrap-empty/`): asks who maintains it and what kind of app before recommending anything | yes |
| `technology-bootstrap-phase2` | real, Sonnet: 2/3 runs clean (`results/20261011-sa-p2g-technology-bootstrap-phase2`) — the answer delegates the test runner and package manager but never mentions a UI framework; recommends one with alternatives and waits instead of settling it | yes |
| `technology-bootstrap-phase3` | real, Sonnet: 15/15 over 3 runs (`results/20261011-sa-final3-boot3`) — the user approves React with Vite; the saved bootstrap decides only what the first test forces, defers persistence with the in-memory reason, treats pinning as a choice, records rejected alternatives and open categories, and shows each choice as approved or delegated. Graded on the saved file. No baseline arm | yes |
| `requirements-refinement-payfine-phase1` | real, Sonnet: 12/12 over 3 runs (`results/20261011-np-final-*`); baseline 2/3 in calibration (writes technical design into the answer) — the pay-a-fine problem doc only, asked to "work out exactly what we want built": asks what to build before writing, doesn't ask what the problem doc or code answers | yes |
| `vertical-slicing-payfine-phase1` | real, Sonnet: 18/18 over 3 runs; baseline 4/5 in calibration (no separate security and accessibility placeholders) — problem plus Active requirements, saves `slice-001.md`: stays inside "confirmed in scope", both placeholders, slice set named, doesn't re-ask the WHAT | yes |
| `acceptance-criteria-payfine` | real, Sonnet: 9/9 over 3 runs; the baseline passed in calibration, so this is a regression guard — the engineer's "handles errors gracefully": rejected as untestable, and the undecided non-decline failures are flagged or routed to the reliability placeholder, not settled in the rewrite | yes |
| `problem-framing-doc-payfine` | real, Sonnet: 14/15 over 3 runs; the baseline passed in calibration, a regression guard — the user's own description with "add a pay button" in it: no solution in the doc, Stripe and one-developer as constraints. Known miss 1/3: an unstated "in-person payment must keep working" listed as a constraint beside a related open question | yes |
| `scope-map-self-service` | real, Sonnet: 14/15 over 3 runs, the miss a judge error (the map routes privacy to each step's requirements pass; re-asked, the judge passes it); baseline misses the privacy routing on both calibration passes — a new, larger problem (`planning/self-service/`: fines, holds, contact details) whose privacy constraint is worded around one step | yes |
| `user-story-writeup-payfine-phase1` | real, Sonnet: 9/9 over 3 runs; baseline fails on both calibration passes (writes the story or fills the security placeholder) — asked to make slice 1 "ready to track", asks whether and where to file before writing. Before the fix the skill never fired: the run filled the slice's security placeholder instead | yes |
| `vertical-slicing-handback` | real, Sonnet: 15/15 over 3 runs (`results/20261011-hb-final`); baseline fails on both calibration passes (edits the Active requirements doc and writes the refund slice in full) — the `pay-fine-handback` folder, where the security pass hands back "members have no refund path": owns the decision, cuts a separate refund slice rather than growing slice 1, sends its WHAT to a requirements pass, and leaves the requirements, design and security documents to their owners. Before the fix the skill grew slice 1, wrote the refund requirement itself and authored security criteria for it. After the fix `vertical-slicing-payfine-phase1` re-ran 18/18 and `orchestrator-backward-route` 2/2 | yes |
| `adr-payment-gateway` | real, Sonnet: 11/12 over 3 runs (`results/20261011-dw-final-*`); baseline fails no-how — a real decision (provider-neutral payments, Adyen at the desk) told with file paths and class names: decision, alternatives with reasons, honest downsides, none of the how. Known miss 1/3: the Context names the `FinePayments` port | yes |
| `adr-neg-rename` | real, Sonnet: 6/6; baseline writes the ADR — a field rename asked for as an ADR: runs the three checks and declines. Before the fix the skill fired and asked how to scope the ADR instead | yes |
| `why-comments-collect-fine` | real, Sonnet: 15/15; the baseline passed in calibration, a regression guard — four planted comments in `fines/collect-fine.ts` (D1, D2, DT1, case-only overlay): deletes the WHAT comments, flags the one that contradicts the retry loop, keeps the WHY, stays off the code | yes |
| `pr-writeup-portal-fines` | real, Sonnet: 12/12; baseline misses the ticket question and the AI role — a finished `/portal/fines` diff written by Claude Code: accurate plain-language description, asks about a ticket instead of assuming, names the tool and its role | yes |
| `user-facing-docs-renewals` | real, Sonnet: 12/12; the baseline passed in calibration, a regression guard — members' help page for portal renewals: two renewals, 21 days from the renewal day, nothing the code doesn't do. Before the fix it invented a "My Loans → Renew" click path and "no late fines"; one run didn't fire until the description said "help page". The no-click-path grader was dropped after failing plain pages twice | yes |
| `staleness-audit-docs` | real, Sonnet: 17/18; baseline misses restated code and ceremony — a planted `docs/` (D3–D6, DT2, DT3): stale lending rules, a code-narrating page, a sign-off log, an ADR the code overturned; keeps the waiver doc and the still-true Stripe ADR. Known miss 1/3: proposes a required-reviewers gate after deleting the sign-off log | yes |
| `tdd-implementation-cancel-hold` | real, Sonnet: 50/54 over 3 runs (`results/20261011-final2-*`); baseline fails every process check in calibration (no Test List, no RED, no review, writes the code first) — the approved cancel-a-hold design built test-first, graded mechanically on the full trace (`regex`/`tool_order`) and on the written files: tests before code, RED runs seen, a `test-quality-review` call every cycle, last run green, design doc ends unchanged, nothing outside the slice touched; the reason wording decided and named, notification left to its owner. Known misses: the main agent edits the design doc before invoking the skill (2/3; the skill then reverts it), one report without its Test List, one multi-scenario test | yes |
| `tdd-implementation-named-fix` | real, Sonnet: 3/3 runs clean (`results/20261011-final-*`); baseline makes the edit and writes no tests in calibration — V15 handed back as a review finding: `LoanStore` through the constructor, `main/server.ts` updated, behaviour unchanged and pinned by new tests that run green, nothing else touched, honest about tests coming after the structural change. Before the trigger fix the skill fired in 1 of 4 runs | yes |
| `tdd-implementation-cancel-hold-via-agent` | real, Sonnet: 25/32 over 2 runs, delegation to `tdd-coach` confirmed — the agent's own TDD process passes; the misses come from the parent, which writes answers into the design doc before delegating, where the subagent can't see that the doc changed (no git in the sandbox) | yes |
| `test-quality-review-fines` | real, Sonnet: 3/3 runs clean; baseline misses the call-order test (calls it "correct") and the untested `percentOf` — the planted `test/fines.test.ts` (Q1–Q5): subject's own method mocked, unwired mock, weak cap assertion, call-order assertion, untested export; traps: a designated fake stubbed per test, exact assertions. The skill didn't fire until its description named "are these tests actually testing anything?" | yes |
| `test-quality-review-reminders` | real, Sonnet: 2/3 runs clean, the third a last-message artifact (the review was complete; the final message is a postscript about a stopped background task); the baseline passed in calibration, a regression guard — the app's own reminder tests: the untested email channel, no false alarm on constructor-injected fakes, "sound but incomplete" | yes |
| `test-quality-review-neg-code-review` | real, Sonnet: never invokes `test-quality-review` (a readability request) | yes |
| `code-review-fine-notices-pr` | real, Sonnet: 2/3 runs clean, the third the same postscript artifact; baseline grades the over-mocked test as its own finding — triplicated notice logic without flagging the guard clause, a false "whole dollars" comment, a name that says count but sums ranked above a vague one, a WHAT comment, duplicate test names; keeps the WHY comment; `why-comments` consulted via `Skill` | yes |
| `code-review-fines-report-pr` | real, Sonnet: 13/15 over 3 runs, 1/3 clean (`results/20261011-final-*`) — a `run()` doing several jobs, member rules in a report class (feature envy), a year/month data clump, the month format with no owner; the Stripe SDK named for `architecture-review`. Feature envy was missed in every run (both arms) until the skill gained a sweep-every-function step and the plant changed from a formatter (which reviews rightly passed) to misplaced business rules. Known misses: the month format (2/3), feature envy (2/3) | yes |
| `code-review-catalog` | real, Sonnet: 3/3; the baseline passed in calibration, a regression guard — the clean module, nothing above Low | yes |
| `code-review-neg-architecture` | real, Sonnet: never invokes `code-review` (a dependency-direction question) | yes |
| `code-review-fine-notices-pr-via-agent` | real, Sonnet: 2/2 runs clean, delegation to `code-reviewer` confirmed | yes |
| `map-update-cancel-hold` | real, Sonnet: 27/27 over 3 runs (one run's scratch script in the sandbox's temp dir was counted against it until the grader limited itself to project files); baseline attaches severity in calibration — after the cancel-hold slice lands, regenerates `docs/architecture-map.md` with no path given: new rows faithful, tiers carried forward, `utils/` untiered, the new tier-1 → tier-3 edge and the untiered edge flagged without verdicts, the shared `roundHalfUpCents` flagged, pre-existing candidates not reported as new, no app code touched. Before the template fix one run called the duplicate "fresh rather than intentional" | yes |
| `map-query-consults` | real, Sonnet: 3/3 runs clean; baseline misses the structural candidate and the shape match and greps the source — three does-it-exist questions answered from the map at its fixed home: `MemberDirectory`, `daysBetween` for `diffInDays`, nothing for a PDF, the stale map caveated | yes |
| `map-query-no-map` | real, Sonnet: 2/3 runs clean; baseline answers by grepping — no map exists: says so and points to `map-update`. Known miss 1/3: mentions a file it noticed while locating the app root | yes |
| `library-app-lending-review` | real, Sonnet: 6/6 with plugin vs 4/6 without (runtime cycle missed, ordering not stated), 1 run — ORM in a use case, runtime import cycle, framework request crossing in, use case reaching into the composition root, type-only-cycle trap | yes |
| `library-app-lending-review-via-agent` | real, Sonnet: 6/6 with plugin, delegation to `software-architect` confirmed via `Agent`; an earlier run scored 5/6 because the top-level agent summarised the report and dropped the ordering line, so the prompt now asks for the report verbatim (`results/20261009-220948-sonnet3-lending-review-via-agent`); the no-plugin arm is vacuous (the agent doesn't exist without the plugin) | yes |
| `library-app-members-review` | real, Sonnet: 3/3 with plugin vs 2/3 without (table-shaped domain type missed), 1 run — backward-check contamination located in the port file, table-shaped domain type, date-library trap | yes |
| `library-app-fines-review` | real, Sonnet: 4/4 with plugin vs 2/4 without (policy-mixed-with-mechanics and the premature strategy interface missed), 1 run | yes |
| `library-app-notifications-review` | real, Sonnet: 3/3 both arms, 1 run — missing channel abstraction, port on the implementer's side, one-impl-port-over-I/O trap | yes |
| `library-app-reporting-review` | real, Sonnet: 3/3 with plugin vs 2/3 without after one skill fix, 1 run each — SQL-level port and SDK in a report found by both arms; the orchestration-mixed-with-CSV smell was missed by both arms in every Sonnet run until the skill's "inconsistent abstraction level" smell gained a concrete check (a method that calls collaborators and also handles characters/delimiters/encodings is at two levels); re-run `results/20261009-220715-sonnet3-reporting-review` passes with the plugin, the baseline still misses it | yes |
| `library-app-reporting-pr` | real, Sonnet: 3/3 with plugin vs 1/3 without after one skill fix, 1 run each — first Sonnet run had the "Pre-existing, not blocking" section listing only items inside the diff; the skill gained "skim the rest of the module before you finish", and the re-run (`results/20261009-215755-sonnet2b`) named the SQL-level port and the Stripe import as pre-existing and non-blocking, with the PR's own smell flagged and the new port not called premature | yes |
| `library-app-structure-review` | real, Sonnet: 4/4 with plugin vs 3/4 without (`services/` and `utils/` described, not flagged), 1 run — technical-role directories, SDK outside its adapter, bootstrap/near-miss/date-library traps | yes |
| `library-app-catalog-review` | real, Sonnet: 1/1 with plugin vs 0/1 without, 1 run — the clean module; with the skill the review reports nothing above Low, without it a Medium is raised (earlier runs flagged two things the fixture itself had introduced, a cross-module read and a dead search route; both fixed) | yes |
| `architecture-review-neg-security-review` | real, Sonnet and Fable: never invokes `architecture-review` in either arm | yes |
| `architecture-review-neg-test-quality-review` | real, Sonnet and Fable: never invokes `architecture-review` in either arm | yes |
| `security-requirements-payfine-phase1` | real, Sonnet: 3/3 runs with plugin (`results/20261011-req-cal7`), 0/1 without on both passes that ran a baseline — given the pay-a-fine slice and the engineer's "let members onto `/fines`" proposal, asks about obligations and who may see whose data, and does not ask how members sign in or which provider handles payment (the code says) | yes |
| `security-requirements-payfine-phase2` | real, Sonnet: 9/9 over 3 runs (`results/20261011-req-sec-p2c`) — presents the shared-route proposal as a pending decision (it would expose staff-only waiving and skip the ownership check), decides nothing for the user, no false alarm on the publishable key. No baseline arm: the history is a with-plugin transcript | yes |
| `security-requirements-payfine-phase3` | real, Sonnet: 18/18 over 3 runs (`results/20261011-req-sec-p3a`) — the user keeps the shared route; finished criteria written for it and made safe (members pay only their own fines, cannot waive), card data never received, error and monitoring exits covered, decision recorded without re-arguing | yes |
| `security-requirements-neg-review` | real, Sonnet: never invokes `security-requirements` in either arm (a review of live code) | yes |
| `security-review-http` | real, Sonnet: 3/3 plants + 2/2 traps with plugin, 1 run — refund route outside every auth prefix, internal error text to callers, request headers/bodies to monitoring; traps: prefix-mounted staff auth, public catalog search. Baseline missed the error-text finding | yes |
| `security-review-portal-pr` | real, Sonnet: 5/5 with plugin, 1 run — member-profile IDOR, SQL injection in history search, PR scoping of pre-existing problems; traps: session-scoped routes, prefix-mounted member auth | yes |
| `security-review-config` | real, Sonnet: 5/5 with plugin, 1 run — hardcoded SendGrid fallback key (rotation required), long-lived AWS keys beside an OIDC job, workflow-wide secrets; traps: Stripe publishable key, `id-token: write`. Baseline called the publishable key a leaked secret | yes |
| `security-review-reminders` | real, Sonnet: 3/3 with plugin vs 1/3 without, 1 run — whole member object logged, real-looking PII in test fixtures; trap: identifier-only log line | yes |
| `security-review-catalog` | real, Sonnet: 1/1 with plugin vs 0/1 without, 1 run — the clean module; baseline rated a rate-limit/scan note Medium | yes |
| `security-review-neg-architecture` | real, Sonnet: never invokes a `security-review` skill in either arm | yes |
| `security-review-neg-reliability` | real, Sonnet: never invokes a `security-review` skill in either arm | yes |
| `supply-chain-review-build` | real, Sonnet: 4/5 with plugin vs 4/5 without in the final pass (`results/20261010-sc-final`); 5/5 vs 3/5 the pass before — tag-pinned base image, an image build that installs without the lockfile, install scripts enabled with a transitive install script; traps: manifest caret ranges under a committed lockfile and `npm ci`, Dependabot. The base-image tag is the flaky one: missed in 2 of 4 direct runs even after the skill gained an enumerate-every-reference check, while the agent path caught it every time | yes |
| `supply-chain-review-build-via-agent` | real, Sonnet: 5/5 with plugin, delegation to `devsecops-engineer` confirmed via `Agent`; the no-plugin arm (2/5) is not a comparison | yes |
| `supply-chain-review-workflows` | real, Sonnet: 3/3 both arms, 1 run — a regression guard: a tag-pinned third-party action in the deploy job, an `@main` reference in a write-scoped workflow; trap: SHA-pinned actions | yes |
| `supply-chain-review-accepted` | real, Sonnet: 5/5 with plugin vs 4/5 without, 1 run — a bare allowlist entry, a "temporary" acceptance nothing enforces (the baseline missed this), an AGPL transitive dependency; traps: a properly recorded acceptance, a dev-only advisory | yes |
| `supply-chain-review-accept-phase1` | real, Sonnet: 3/3 with plugin across passes vs 1/3 without — asked to record an allowlisted advisory, the skill asks which classification applies and for the reason instead of choosing; the baseline picks or offers a dated "temporary" acceptance. The skill did not fire at all until its description named accepting/recording a finding | yes |
| `supply-chain-review-accept-phase2` | real, Sonnet: 3/3 on 2 runs plus the final pass (`results/20261010-sc-p2b`) — the first case built on `context.history_file`: resumes a frozen phase-1 question, answers "accepted risk" with a reason, and checks the write-up keeps the user's classification and reason, adds no unenforced expiry, and flags the acceptance as ADR-worthy without drafting it. No baseline arm: the history is a with-plugin transcript. The ADR flag failed until it became an explicit recording step, and that fix only reached phase 2 after phase 1 was re-run and re-frozen | yes |
| `supply-chain-review-neg-security` | real, Sonnet: never invokes `supply-chain-review` in either arm | yes |
| `supply-chain-review-neg-reliability` | real, Sonnet: never invokes `supply-chain-review` in either arm | yes |
| `reliability-requirements-payfine-phase1` | real, Sonnet: 2/2 runs with plugin (`results/20261011-req-rel-p1e`), 0/1 without on both passes that ran a baseline — same slice with the engineer's "show 'failed, try again' after 10 s" proposal; asks what an hour down costs, the target and who notices, not what the code says | yes |
| `reliability-requirements-payfine-phase2` | real, Sonnet: 8/9 over 3 runs, 2/3 clean (`results/20261011-req-rel-p2e`) — names the duplicate charge a timed-out retry can cause and leaves its handling as a pending decision (the miss settles it), no retry of declines | yes |
| `reliability-requirements-payfine-phase3` | real, Sonnet: 18/18 over 3 runs (`results/20261011-req-rel-p3c`) — the user keeps "show failed" and refunds duplicates by hand; finished criteria for that, duplicates made findable for the refund, charge-without-settle caught, double submit covered, declines vs faults, no retry of declines | yes |
| `reliability-requirements-neg-review` | real, Sonnet: never invokes `reliability-requirements` in either arm (a review of live code) | yes |
| `reliability-review-nightly` | real, Sonnet: 8/8 with plugin vs 5/8 without, 1 run (`results/20261010-final-reliability-review`) — unhandled rejection from the timer-driven job, no per-loan isolation, a database pool leaked per run, a mailer with no timeout, a postal adapter that swallows failures; traps: the reminder loop's catch, re-run idempotency, a correct transient-only SMS retry. The pool leak was missed in two of six calibration runs | yes |
| `reliability-review-nightly-via-agent` | real, Sonnet: 8/8 with plugin, delegation to `devsecops-engineer` confirmed via `Agent`; the no-plugin arm (3/8) is not a comparison, the agent doesn't exist without the plugin | yes |
| `reliability-review-http` | real, Sonnet: 5/5 with plugin vs 3/5 without, 1 run — expected and unexpected failures conflated in `respond.ts`, unbounded loan history, holds kept only in memory; traps: the catalog route's 503 handling, the capped search. Unbounded history and in-memory holds each missed once across calibration | yes |
| `reliability-review-alerts` | real, Sonnet: 3/3 with plugin vs 2/3 without, 1 run — page on any error event, non-actionable CPU page; trap: multi-window burn-rate alerts with a runbook | yes |
| `reliability-review-fine-payment` | real, Sonnet: 4/4 both arms, 1 run — a regression guard, not evidence of uplift: charge-then-settle with no idempotency, retrying declines in the use case, a pay route that hides unexpected failures; trap: the settled-fine guard | yes |
| `reliability-review-catalog` | real, Sonnet: 1/2 with plugin vs 1/2 without (`results/20261010-recheck3-catalog`) — the clean module, a borderline restraint case with no uplift. Its original prompt asked how catalog behaves "when the database is slow or down and as the catalog grows"; that leading question produced a Medium/High capacity concern in every run of both arms (four calibration passes plus two rechecks). With the neutral prompt the capacity speculation stopped; the remaining failing runs rate a missing read retry Medium. Known gap: the skill does not reliably hold a clean module to Low | yes |
| `reliability-review-neg-security` | real, Sonnet: never invokes `reliability-review` in either arm | yes |
| `reliability-review-neg-architecture` | real, Sonnet: never invokes `reliability-review` in either arm | yes |
| `operational-readiness-release-phase1` | real, Sonnet: 1/1 with plugin on six passes (`results/20261011-or-p1h`), 0/1 without on both passes that ran a baseline — asked "is it ready to ship?", the skill asks who uses the service, what breaks, who finds out and whether a rollback has ever run, and holds its verdict; the baseline reviews straight away. In the first calibration pass the skill fired but reviewed straight away too, until it said its first response is questions | yes |
| `operational-readiness-release-phase2` | real, Sonnet: 14/15 over 3 runs, 2/3 runs clean (`results/20261011-or-p2h`) — resumes the frozen questions with the one-developer answer; unverified deploy, migration 0012 coupled to the release, never-rehearsed rollback and no team-scale ceremony 3/3; no false "no rollback" claim 2/3 (the miss reads `release.sh` as unable to target a previous image). No baseline arm: the history is a with-plugin transcript | yes |
| `operational-readiness-ops-phase1` | real, Sonnet: 1/1 with plugin on six passes (`results/20261011-or-p1h`), 0/1 without on both passes that ran a baseline — same as the release phase 1, asked about running the service rather than one release | yes |
| `operational-readiness-ops-phase2` | real, Sonnet: 15/15 over 3 runs (`results/20261011-or-p2h`) — nightly job with no missing-run signal, config that starts silently without `MONITOR_DSN`/Stripe/Twilio, nothing written for 2am, no ceremony, no false "no backups" claim | yes |
| `operational-readiness-neg-security` | real, Sonnet: never invokes `operational-readiness` in either arm | yes |
| `operational-readiness-neg-reliability` | real, Sonnet: never invokes `operational-readiness` in either arm | yes |
| `design-system-payfine-phase1` | real, Sonnet: 9/9 over 3 runs (`results/ui5-*`); baseline 0/2 in calibration (writes a design system straight away) — first screen in the project, no design system: asks whether there's a reference to match or candidates to generate, and asks or states the platform, writing nothing | yes |
| `design-system-payfine-phase2` | real, Sonnet: 12/12 over 3 runs (`results/ui5-*`) — told to generate for phones: three candidate HTML files beside `visual-ux/`, not in it, says it couldn't view them, asks which to keep without leaning. Known minor miss 1/3: promises "the winner's mockup and screenshot" when no screenshot is possible. No baseline arm: the history is a with-plugin transcript | yes |
| `design-system-payfine-phase3` | real, Sonnet: 19/21 over 3 runs (`results/ui5-*`) — the user picks the second candidate; the system goes to `visual-ux/` with every token category, phone-first platform with its source, a ratio for every text colour, only the winner's mockup, no screenshot claimed. Misses: one run declares `--success` without its ratio (it is 4.70:1); one `chosen-direction-committed` FAIL is judge noise (re-asked twice: PASS) | yes |
| `screen-design-payfine` | real, Sonnet: 33/33 over 3 runs (`results/ui3-*`); baseline wrote no mockups in calibration (8/10) — against the planted design system: one HTML mockup per state, the system's patterns reused, no pay-several or saved cards, copy rules, accessibility placeholder carried forward, no screenshot claimed, nothing asked that the docs answer, `design-system` not fired | yes |
| `accessibility-review-payfine` | real, Sonnet: 36/36 over 3 runs (`results/ui3-*`); baseline 10/11 in calibration, a regression guard, not evidence of uplift: its only miss is not saying the check was a markup read — the declined-state mockup (A1–A4, AT1–AT3): unreachable fine choice ranked top, missing live region, 4.48:1 meta text, placeholder-only name field; no false alarm on the focus rule, the hidden icon or the `aria-labelledby` field; Given/When/Then split now vs needs real code; mockup untouched | yes |
| `accessibility-review-neg-readability` | real, Sonnet: never invokes `accessibility-review` in either arm (a plain-language pass on a planning doc) | yes |

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

Eight cases currently need a run. Nothing here is green — every score in
the table above either predates a change to the code it covers, or predates
an edit to the case itself. Ordered by what's worth doing first, not by
what's cheapest.

| # | Case | Why it's first |
|---|---|---|
| 1 | ~~`orchestrator`~~ | **Run, fixed, re-run: 15/15 PASS.** First pass was 14/15 — `single-step-not-chained` caught backward routes L and M narrating the post-resolution forward resumption. Fixed in `skills/orchestrator/SKILL.md`'s backward-routing section and confirmed clean on re-run. Details in `orchestrator/eval-score/summary.md`. |
| 2 | ~~`software-architect:technology-bootstrap`~~ | **Run: 6/6 PASS.** The negative grader (never solicit CI/CD, hosting, a database, observability, or auth) passed clean against its own fixture for the first time. One interpretive call worth watching in future runs: UI framework was judged not-forced by the first test — defensible, but not mechanical. Details in `software-architect:technology-bootstrap/eval-score/summary.md`. |
| 3 | ~~`docs-writer:scope-map`~~ | **Run, fixed, re-run: 5/5 PASS.** First pass was 4/5 — the "AI categorization must be free" constraint got absorbed into its step's one-liner instead of being flagged cross-cutting like security. Fixed in `skills/scope-map/SKILL.md`: identify a cross-cutting constraint by its underlying concern, not by which step's sentence names it. Confirmed clean on re-run. Details in `docs-writer:scope-map/eval-score/summary.md`. |
| 4 | ~~`product-manager:requirements-refinement`~~ | **Run: 6/6 PASS.** The constraints-in-force grader — added after a real run dropped the hosting and single-user constraints for a step that didn't look like it owned them — passed clean: both non-obvious consequences (network access-control gate, present-tense single-user modeling) were drawn correctly. |
| 5 | ~~`product-slicer:vertical-slicing`~~ | **Run: 6/6 PASS.** Scenario C's grader — encoding the real failure where a menu of options got handed to the user, who picked "grow the slice" — passed clean: ranked order worked through explicitly, narrowing rejected with a concrete reason, new slice ahead chosen, both invalidations named. |
| 6 | ~~`product-slicer:acceptance-criteria`~~ | **Run: 2/2 PASS.** Regression confirmation, no news, as expected. |
| 7 | ~~`software-architect:architecture-review`~~ | **Run: 4/4 PASS.** Regression confirmation, no news. Case since retired in favour of the `library-app-*` suite. |
| 8 | ~~`software-architect:architecture-design`~~ | **Reworked, then run: 8/8 PASS.** Graders split into four `portable-*` (hold for any design doc) and three `fixture-*` (this case's own sync/async and premature-abstraction content) per `NOTES.md`'s plan. First-ever gradable result for this case, and the first real test of the "Technology at a boundary" section added since it was last run. |

All eight cases in this backlog have now been run at least once.

Run with the `agent-eval` skill, one case per invocation.

### Known coverage gaps

- **Persona rules the orchestrator can't reach.** The orchestrator now
  invokes a routed skill and never reads the persona's `AGENT.md`, so any
  rule a routed step needs must be in the skill. `devsecops-engineer`,
  `software-architect`, `product-manager`, `product-slicer` and
  `docs-writer`, `tdd-coach`, `code-reviewer`,
  `architecture-cartographer`, `ux-designer` and `accessibility-engineer`
  have had that pass, so every persona has. Keep it that way: a new
  persona rule goes in the skill, not only the `AGENT.md`.
- **The `tdd-implementation` quarantine flow is uncovered.** The real cases
  invoke the skill directly and through the `tdd-coach` agent; the
  orchestrator's quarantine/grade/combine/finalize flow (two worktree
  candidates, parallel reviewers) has no case. Worktree isolation inside
  the eval sandbox is unproven.
- **The main agent acts before `tdd-implementation` loads.** Asked to build
  a design, Sonnet reads around and often writes its own answers to the
  design's open questions into the design doc before invoking the skill
  (2/3 runs even after the description says "invoke it first"). The skill
  now reverts such an edit and treats the question as open; through the
  agent path the parent's edit is invisible to the subagent, so
  `tdd-implementation-cancel-hold-via-agent` stays weak for that reason.
- **software-architect has no `Skill` tool.** `architecture-design`
  consults `map-query` and the devsecops skills through the `Skill` tool,
  which the agent path can't use. tdd-coach and code-reviewer were given
  it this session; software-architect wasn't changed.

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
- **`agent-eval`'s "Read/Grep/Glob only" dry-run grant isn't actually
  enforceable on a `general-purpose` subagent in this environment.**
  Surfaced running `accessibility-engineer:accessibility-review`: the
  spawned emulation agent had full tool access regardless of the
  procedure's instructions, and used it — opening a real Chrome tab and
  driving the fixture mockup live (keyboard events, computed-style
  contrast math, real `getBoundingClientRect` measurements) rather than
  reasoning over the HTML text alone. No repo file was written or edited,
  so the side-effect-free half of the dry run held, but this is not the
  purely-textual emulation the procedure describes, and it's likely the
  reason that same run also forgot the mandated "Skills consulted:"
  self-report line (see `eval-score/summary.md`) — busy actually
  executing checks instead of following a literal formatting
  instruction. Any future case for a persona whose skill instructs real
  tool use (browser automation, code execution) should expect the same
  gap until this harness gains a real tool-restriction mechanism.
- ~~**`tdd-coach:tdd-implementation` couldn't be checked running for real.**~~
  **Closed.** The real cases run Node's test runner in the sandbox (the
  `code-plants/tdd/` overlay's `test/ts-resolve.mjs` lets
  `node --experimental-transform-types --test` load the app's TypeScript
  with no install) and grade the trace mechanically.
- **`technology-bootstrap`'s advisor-consult path is only softly graded.**
  Consulting `devsecops-engineer` inline is treated as expected-but-not-
  required, because the emulation harness can't distinguish an inline
  consult from a spawn — the distinction the rule actually exists to
  enforce.
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
