# kad-dev-team

A personal Claude Code plugin. It bundles a roster of narrow-focus developer
personas (agents), each backed by one or more skills, encoding the essential principles for clean, robust, option-enabling, maintainable,
well-tested, expandable software.

The personas span the roles a well-rounded engineering team needs to cover —
architecture, TDD, code review, security, reliability/infra, visual and
interaction design, accessibility, and more — each grounded in established
engineering practice. See
[PERSONAS.md](./PERSONAS.md) for the full roster and build status.

One skill, `orchestrator`, isn't tied to any single persona — it routes a
problem to whichever persona/skill applies next by inspecting what already
exists, instead of you having to name the right one each time.

## Start

From the project's root, in a terminal:

```bash
kad                 # alias kad=<plugin root>/bin/kad once; or run bin/kad by its path
```

That is the whole setup. The first run on a project prints the permission
set the session runs with (what it may write, what it may never read, which
hosts it reaches, the one credential it holds, local ports, Chrome, audit
mode) and asks one yes; every later run prints one line and starts, inside
the sandbox runtime, with audit mode on and Claude in Chrome ready. Then
say "what's next". A plain `claude` session cannot run the flow: its
orchestrator prints this one command and stops. The details are under
"Starting a session: `bin/kad`".

## Structure

```
.claude-plugin/
  plugin.json        # plugin manifest
  marketplace.json    # self-hosting marketplace entry, for local install/testing
agents/
  <persona>/AGENT.md  # persona definition: frontmatter + system prompt
skills/
  <skill>/SKILL.md    # backing knowledge a persona (or you, directly) can invoke
  orchestrator/scripts/validation_gate.py  # the chunk loop's mechanical gate: suite green, typecheck and
                       # lint from the manifest, scope (the chunk's files plus the design's module
                       # directories; an in-module file off the list is a reported deviation, an
                       # out-of-module file a failure), protected files, coverage; report-only comment
                       # density and size figures; run on every chunk commit and every fix commit before
                       # any reviewer; --accept-protected takes in a protected document the user amended
                       # while the loop was running
  orchestrator/scripts/ts_runtime_lines.mjs # which lines of a TypeScript file keep runtime code, for the
                       # gate's coverage check (type-only modules exempt, erased type lines discounted)
  orchestrator/scripts/sandbox_check.py    # the loop's first step: the launcher's fence probed from inside,
                       # secrets unreadable, no direct network, writes only where the approved set allows
                       # (the launcher's own folders named); a FAIL under the launcher stops the flow with
                       # no question, since the cause is outside the session (see below)
  orchestrator/scripts/readiness_check.py  # the design-readiness gate before the first builder: ten
                       # mechanical checks over the planning documents, each failure routed to the
                       # persona that owns the document (a slice's blocking open item, and a value of a
                       # file the owner provided, to the owner)
  orchestrator/scripts/source_scan.py      # the planning-data rule's mechanical half: reads each file the
                       # owner provided (listed by location in the target directory's sources.md) where it
                       # is and finds its text and numeric cells in the planning documents, the code or
                       # every commit of a branch, printing files, lines and cells and never a value;
                       # `describe` gives a planning stage a file's shape without a cell; `map`, `rewrite`
                       # and `scan --map` are delivery's removal of a value from history
  orchestrator/scripts/scratch_run.py      # the data rule: every agent that starts the app starts it through
                       # this, HOME and every data path inside a scratch folder outside the project,
                       # a path that resolves outside refused; --hash digests the owner's real data
                       # directory for the before-and-after check around a launch
  orchestrator/scripts/rounds_record.py    # a review or smoke report in the shared finding format into the
                       # fix-round sidecar, classified regression or pre-existing against the fix's
                       # diff, and the counts for the log line; the criteria walk's per-criterion
                       # table into the sidecar too; --standing lists what is carried
  test-quality-review/scripts/test_measures.py # at the slice review: helpers copied across test files and
                       # the share of assertions on markup, CSS, regexes or prose, with a bar
  orchestrator/scripts/done_check.py       # the Definition of Done at the slice review: README, lint and
                       # formatter, typecheck, no code in strings, no planning references, comment
                       # density, persisted names, env defaults, test padding
  orchestrator/scripts/audit_sync.py       # after every records commit of the loop when KAD_AUDIT_REPO is set: a
                       # slice's planning documents, log, report, map, reviewer reports, fix-round
                       # sidecar and every session's transcripts (found by session id, scanned
                       # for listed sources' values first and withheld on a hit) copied into
                       # the audit repository's clone ($KAD_AUDIT_DIR/repo/) under a lock,
                       # refused on a credential-shaped string, committed under the project's
                       # identity and pushed; --check reports the clone's state for the A line
  map-update/scripts/extract_map.py        # the architecture map extractor (TypeScript, JavaScript, Python):
                       # modules, import edges, externals, exports, tiers carried from the prior map,
                       # the diff and the two candidate flags; a language without one is listed with
                       # no edges and said so, never hand-parsed
hooks/
  hooks.json, audit.sh # audit mode: off unless KAD_AUDIT=1 (see below); with KAD_AUDIT_REPO set, the
                       # SessionStart hook finds the audit repository's clone at $KAD_AUDIT_DIR/repo/
                       # (the launcher made it) or clones it there, and records the outcome;
                       # `audit.sh --snapshot` copies the session's transcript on demand
evals/
  <case>/case.yaml     # a `claude plugin eval` case (negative trigger cases use prompt.md + graders/)
  fixtures/library-app # shared fixture app with an answer key; personas plant defects in overlays
  thresholds.json      # each case's bar for the eval gate
  tools/               # eval_gate.py, affected_cases.py, record_thresholds.py, rejudge.py,
                       # freeze-history.sh, audit_report.py, orchestrator_log_check.py (a real
                       # project's log against the orchestrator's rules), cold_read.md and
                       # mutation_pass.py (a slice review's two probes: the stranger's assessment
                       # with execution probes, and scripted exact-string mutants against the
                       # suite), implementation_judge.py (the
                       # blind pairwise judge of two implementations, kept for the evals), pairwise_judge.py
                       # (with/without arms, over that judge), new-case.sh,
                       # summarize_results.py and report_evidence.py (read a results dir or CI artifact),
                       # eval_evidence.py (the PR check: a passing gate run recorded against these exact files),
                       # wsl-setup.sh and wsl-gate.sh (set up, then run the gate under WSL2 in one command)
  HANDOFF-2026-10-13.md # where the eval audit stands and how to continue it; TODO.md is the work list
  example/             # one running problem, worked end to end by the real roster
.github/workflows/
  eval-gate.yml        # PR check: every affected eval case has a passing local gate run in evals/evidence.json
.synthesis/
  <persona>.md          # internal only — source synthesis notes, deleted once roster is complete
```

`claude plugin eval` runs every case as a genuine child process, with a
no-plugin baseline arm for comparison. A pull request that changes a skill,
an agent or an eval must carry, in `evals/evidence.json`, a passing local
gate run of every case it can affect against exactly those files; the PR
check verifies that without calling a model (`evals/README.md`, "Eval
gate"). `evals/README.md` also has
the playbook for building a suite for another skill, and
`evals/fixtures/library-app/README.md` explains the shared fixture app.

`evals/example/` is the dogfooding record, not a test case: one real problem
carried from framing through requirements, slicing, design, runtime-safety
criteria, stack selection, and screen design by the actual personas. Most
changes to this plugin came from watching that run break, so its
`summary.md` is usually the best explanation of why a rule exists.

## Starting a session: `bin/kad`

One command, run from the project's root (alias `kad=<plugin root>/bin/kad`
once, or run the script by its path; a marketplace install's is under
`~/.claude/plugins/cache/kad-dev-team-marketplace/kad-dev-team/<version>/bin/kad`,
and changes with the version):

```bash
kad                              # start the fenced session
kad --check                      # print the set it would start with; write and start nothing
kad --reset                      # show the permission set again, the stored answers open to change
kad --no-chrome                  # a slice that touches no screen; a UI slice then owes every screen check
kad -- --resume                  # arguments after -- go to claude
```

**The first run on a project** prints the permission set in plain words
and asks one yes: what the session may write (the project, the audit
directory, Claude Code's own files, the temp directory, npm's cache and
kad's `gh` directory; never Claude Code's user settings, hooks, commands,
agents, skills or plugins, so nothing an agent writes outlives the
session); what it may never read (`~/.ssh`, `~/.aws`, `~/.gnupg`,
`~/.kube`, `~/.config/gcloud`, `~/.azure`, `~/.config/gh`, `~/.npmrc`,
`~/.netrc`, `~/.git-credentials`, `~/.pypirc`, `~/.docker/config.json`,
`~/.terraform.d/credentials.tfrc.json`, the Claude credentials file);
which hosts it reaches (the API and sign-in, GitHub, Chrome's bridge, the
registries the project's manifests call for, `registry.npmjs.org` for a
`package.json` and `pypi.org` for a `pyproject.toml`, and any extra
domain you add); the one credential it holds (the GitHub token from your
`gh` login, as `GH_TOKEN`, so the loop can push, open the pull request
and file issues inside the fence; `--gh-token-env NAME` takes a
fine-grained token instead; every other credential-shaped variable is
dropped from the environment); local ports (allowed, for a dev server and
the smoke runs; `--no-local` denies them); Chrome (on; on Linux the set
says that this opens every unix socket to the session, the SSH agent's
and Docker's included, since the runtime cannot allow the extension's
socket alone); audit mode (on, with the repository the material is synced
to at the end of each slice, or local only). Answer `n` to change the
three answers behind it (audit mode, the audit repository, the extra
domains; `none` clears one) and the set is shown again. The answers and
the approval are stored per project, owner-readable only, in
`~/.config/kad-dev-team/launcher.json` (a project without answers of its
own starts from the file's root-level ones, where 0.13.x kept them),
which the launcher only ever rewrites whole, under a lock, through a
temporary file, and never deletes: a declined or interrupted run leaves it
as it was (0.13.1's `--reset` deleted it before asking, and an interrupted
reset lost every answer). **Every later run prints one line and starts.**
A run whose set is wider than the approved one (a manifest that now calls
for a registry, a `--domain`, Chrome or local ports back on after an
opt-out, another audit repository) is shown again for one yes; a narrower
run (`--no-chrome`, `--no-local`, `--no-audit`) starts without a question.
`--audit`, `--no-audit`, `--audit-repo URL` and `--domain D` set the
answers on the first run and change one run afterwards (`--audit-repo
none` is local-only for that run).

What it does every time: checks the platform (macOS, Linux and WSL2 have
the runtime's backend; native Windows is told to run it from WSL2) and
that `claude`, `python3` and the sandbox runtime `srt` are on PATH
(offering to install the runtime); makes sure Claude in Chrome can reach
Claude Code, writing the extension's native-messaging manifest into each
installed Chromium-family browser's profile and the native host wrapper
under `~/.claude/chrome/` when they are missing (Claude Code writes them
the first time Chrome is enabled in a plain session; the fence denies both
paths, so the launcher writes them outside it, with the same content, once
the set is approved); writes the runtime's settings for this run under
`~/.config/kad-dev-team/srt/`, one file per launch so two overlapping
launches of one project never read each other's (with `allowPty` on macOS, without which
the runtime's profile denies the terminal's raw mode and every arrow key
lands in the session as text; the bridge hosts tunnelled past the
runtime's TLS termination, which refuses the WebSocket upgrade the bridge
needs, the reason run 3 never reached a browser; the extension's unix
socket allowed, which on Linux means every unix socket, since the runtime
cannot allow one path there, and the set says so); drops the credential-shaped variables and
another Claude Code session's variables (`CLAUDE_CODE_CHILD_SESSION` and
its kin, which would turn transcript saving off for the session started
here); clones the audit repository into `$KAD_AUDIT_DIR/repo/` before the
fence starts (inside it git cannot write a `.git/config`), with the
project's git identity; creates the plugin's hook data directory under
`~/.claude/plugins/data/` for a `--plugin-dir` run (the fence denies its
creation, and every hook then fails before it runs); and starts `srt
--settings <file> claude --chrome --plugin-dir <this plugin>` in the
project, so the Read tool, hooks and every agent are inside the fence.
The session gets `KAD_SRT_SETTINGS`, `KAD_GH_DIR`, `KAD_AUDIT_DIR`,
`KAD_AUDIT=1`, `KAD_AUDIT_REPO` and `KAD_CHROME=1`, which the
orchestrator's sandbox check reads before anything is launched: it names
the launcher's own folders as allowed and whatever else is missing.

**Nothing restarts.** The fence has to exist before Claude Code starts, so
there is no `--relaunch`, no `--prepare` and no terminal window (0.13.1's
window inherited the session's variables and lost two runs' transcripts).
A plain `claude` session asked "what's next" runs the orchestrator's step
0, which finds the session is not fenced, prints this one command with the
launcher's full path, and stops; it asks nothing. A session fenced by
something other than the launcher (`srt claude` by hand) goes on without a
question, with audit mode as its environment says.

The orchestrator's A step asks nothing the launcher guarantees: no
settings, sandbox or transcript question. On a slice that touches UI it
asks the Chrome tools whether a browser answers; none answering is an
error with the fix on the line (the browser not open, the extension not
installed or not connected, `--no-chrome` given) and one question: restart
with Chrome, or continue with every screen check owed. Delegation is asked
once per project and kept in `planning/delegation.md`.
`bash evals/tools/kad_test.sh` tests the launcher with stub tools.

## Local development

Load this plugin directly from disk without installing it, so changes take
effect on the next restart:

```bash
claude --plugin-dir <plugin root>
```

You can combine this with other `--plugin-dir` flags to load alongside other
plugins you're iterating on.

## Audit mode

To check how the personas behave in real work, turn audit mode on for the
sessions you want recorded:

```bash
export KAD_AUDIT=1                   # or "env": {"KAD_AUDIT": "1"} in settings.json
export KAD_AUDIT_DIR=~/kad-audit     # optional; defaults to ~/.claude/kad-audit
export KAD_AUDIT_REPO=https://github.com/<you>/audit-docs  # optional; see below
```

The plugin's hooks then log each prompt and every `kad-dev-team` skill and
agent call, and keep the full transcript of any session that used the
plugin. Nothing leaves your machine, and sessions that never used the
plugin aren't kept.

With `KAD_AUDIT_REPO` set as well, the audit material gets a home you
choose: a separate repository, cloned into `$KAD_AUDIT_DIR/repo/` (by
`kad` before the fence starts, or by the SessionStart hook in a session
`kad` did not start; never inside the project). The orchestrator's chunk
loop reports the clone's state, and whether this session's transcript is
being written (`transcript — kept | MISSING: <why>`, from an `audit.sh
--snapshot` run there and then), on its A line and, after every records
commit (each chunk's, the slice review's, the delivery's), snapshots the
session's transcript and runs `audit_sync.py`, which copies that slice's
planning documents, orchestrator log, implementation report, architecture
map, reviewer reports, fix-round sidecar and every session's transcripts
into `<clone>/<project>-slice-<n>/`, refuses if anything it would copy
looks like a credential, and commits (under the project's git identity)
and pushes in the clone, under a lock so two sessions cannot interleave;
its result goes on the log line as printed, a failure included, never as
a skip. A session's transcript is found by its id (the live file Claude
Code writes, or the hook's snapshot, whichever is larger; a copy that
grew is refreshed on the next sync), a session counts as complete only
once its SessionEnd is in the log, and with a `sources.md` in the
planning directory every transcript is read by the source scan first: a
session holding a listed source's value is *withheld* (`withheld:
<session>` on the line; the transcript stays on disk and the owner
decides), and one the scan cannot read is never copied as clean. Run it
by hand with `python3 -I skills/orchestrator/scripts/audit_sync.py
--project <root> --slice <n>` (add `--snapshot` to copy this session's
transcript first, `--transcripts` to include the sessions' transcripts,
`--no-push` to only commit, `--clone <dir>` for a clone elsewhere,
`--sources <file>` to scan against another `sources.md`). In this repo, ask Claude to "review the audit logs"
(the `audit-review` skill): it reads the flagged sessions against the
skills' own rules and proposes fixes and eval cases.
`evals/tools/audit_report.py` gives the raw overview (where each
session's transcript is: kept, on disk and not copied, withheld, or
none), `evals/tools/orchestrator_log_check.py <project dir>` checks a
project's `orchestrator-log.md` against the orchestrator's rules and the
kept transcripts, and a slice review's two probes are
`evals/tools/cold_read.md` (the stranger's assessment, launched as an
Opus agent against a clone) and `evals/tools/mutation_pass.py` (scripted
exact-string mutants against the suite).

## The implementation skill

Every chunk is built by `tdd-implementation-lite`: the contract (what the
implementer owns, where things go, how a gap is escalated, what the
report holds) as test-first with verification rather than TDD: the tests
before the code, seen failing on their own assertions against a stub,
then shown to catch a deliberate break, with the loop between left to the
model. Until 0.13.0 the orchestrator asked once per slice whether to
build with this or with `tdd-implementation`, TDD proper with a Test List
and a `test-quality-review` call every cycle; two real slices showed lite
matching its design quality at about a quarter of the cost, and the
heavier skill was retired on 2026-11-06. `tdd-implementation-lite` is
never chosen from a plain "build it": it runs only when the chunk loop
names it.

## The chunk loop

The orchestrator's `tdd-coach:tdd-implementation-lite` row builds a slice as a
series of small commits on a slice branch, each checked before the next
starts, and delivers the branch as a pull request. This is the v4 shape
(`.synthesis/implementation-flow-v4.md`), redesigned after the second real
run cost $346 and 14.5 hours for a slice that was not production-grade:
the money moves upstream into design completeness and to the seam and the
finish, and the review loop keeps only what the data said earned its
place. In order:

- **Before A, the open work:** the orchestrator asks the tracker (`gh`)
  what is open before it reads a planning document. A pull request from a
  slice branch routes to the external-review triage on every unresolved
  comment, whoever wrote it (the flow's own posts carry the footer line
  `— kad-dev-team` and are the only ones skipped), and nothing newer
  starts until it is merged; each open Critical or High issue is one
  question to the owner (fix it in the open slice's round, fix it first
  on its own branch, accept it as known; a Critical never the third).
- **A. Start:** a repository and an `origin` must exist (otherwise
  `release-engineer:repo-bootstrap`, decided with the owner); the sandbox
  check (below); the browser check on a UI slice; then at most two
  questions, **one per `AskUserQuestion` call**: browser, delegation. On
  "yes" to the delegation question the orchestrator writes
  `planning/delegation.md` and the per-slice file (the owner's words, what
  it covers, what it never covers), which is what lets a persona settle a
  mid-build decision without the owner. The cadence (`loop`, or `light`
  when the owner's message names it) and the **budget line** are written:
  8 h of loop time for a UI-touching slice and 5 h otherwise, 2 reviewer
  launches per chunk, 1 fixer per scope plus 1 for regressions; consults
  counted, never capped; counted at every chunk boundary, and the flow
  ends at the boundary that exceeds one. A `slice-<nnn>-<slug>` branch
  (uncommitted planning documents are committed on it first), the base
  commit recorded. Then the **design-readiness gate**
  (`readiness_check.py`): every criterion homed in the design, every
  failure path homed, a number on every retry, wait and give-up, security
  and reliability agreeing, a mockup for every named state, no question
  routed to "the implementer", a "Kept for later slices" line, every open
  or deferred item of the slice triaged (`Usable without it: <how>` or a
  blocker, which goes to the owner before any build), a row for an
  external provider's unusable reply. Each failure is a backward route to
  the persona that owns the document before any builder launches; after
  the last route a new chunk-loop entry carries the A line.
- **B. Plan:** one implementer (Sonnet) reads the slice, consults the map
  and writes a **chunk plan** into the implementation report: two to
  eight vertical chunks, each with a title, the criteria it delivers, its
  files, its done check (which names a **seam test**: through the real
  composition root, the real adapters and the real local store, only the
  external service faked at its wire boundary) and the territories it
  touches. The orchestrator checks the plan mechanically and commits it.
- **C. Chunks:** for each chunk the orchestrator launches one **chunk
  runner** (`agents/chunk-runner`, Opus, `skills/chunk-runner`), which
  carries the chunk's whole round on a context of its own and hands back
  one line (0.14.1, the v4 design's D9 phase 2: slice 2's orchestrator
  thread averaged about 427k cache-read tokens per call and was 44% of
  the cost). Inside the runner: a fresh implementer (Sonnet, short
  context, `maxTurns` 120) builds the chunk test-first, the seam test
  first, comments only where `why-comments` would keep one, and commits
  it with the chunk's title. The gate runs on the commit range: suite,
  typecheck, lint, scope (the chunk's files plus the design's module
  directories; a file inside a module but off the list is a recorded
  deviation, not a failure), protected documents, coverage, report-only
  comment density and size figures, and the builder's transcript replayed
  (`--agent`): the shell edits counted beside the number the builder
  reported, and a commit chained to its test run named. Then **two
  launches, never more**: one combined reviewer (`code-reviewer`, Opus:
  `code-review`, `test-quality-review` and, when the chunk touches HTTP,
  storage or error handling, `reliability-review`, one report, at most
  eight findings, Critical/High/Medium only) and one **smoke run** (the
  app started through `scratch_run.py`, every data path inside a scratch
  folder, never the owner's data; the chunk's done check driven through
  the real interface: `accessibility-engineer` in the real browser with a
  screenshot per state when the chunk touches UI, else `tdd-coach` over
  HTTP). Then **one fix round**: a fresh fixer (Sonnet) for every
  finding, the gate, a regressions-only re-review on the fix's diff, a
  second and last fixer for the regressions, the gate, done. Pre-existing
  findings the re-review raises stand: a standing Critical or High stops
  the loop for the owner, a standing Medium goes to the pull request
  body. A finding no planning document can settle is `needs-decision
  (<persona>)`: the runner hands it back; with the delegation file the
  orchestrator launches the owning persona once, which writes its own
  document and commits `Decision <n>`, then relaunches the runner for the
  fix round; without it the flow stops for the owner. A gate failure on
  a test that passed on the same range before is `flaky: <test>`: one
  re-run, then one fixer at the cause. `rounds_record.py` is the only
  thing that parses a report; it writes the sidecar and prints the C
  line's counts. No Lows per chunk. The orchestrator keeps the records
  commit, the audit sync, the C line (the hand-back's fields plus
  `builder`, `data unchanged|CHANGED` from the hash of the owner's data
  directory around the launch, `records`, `audit`) and the budget check.
  Under the `light` cadence (one measured arm, named in the owner's
  message for the slice: `cadence — light` on the A line) the runner does
  the build, the gate and the smoke run only, and every finding waits
  for D.
- **D. Slice review:** the map is regenerated with the shipped extractor
  (the suite's shared helpers listed under a `test-support` tier, so a
  builder's `map-query` finds an existing helper); the **Definition of
  Done** runs (`done_check.py`: README, linter and formatter clean,
  typecheck, no code in strings, no planning reference in code, comment
  density at or under 5%, the next slice's names persisted, env defaults
  not production, tests not padding), with `docs-writer:readme` for the
  README and one Sonnet fixer for the batch; then the six reviewers once
  on the whole slice diff (Lows allowed here; each criteria reviewer
  restates the slice's accepted deferrals as findings so they reach the
  pull request; `test-quality-review` measures duplicated helpers and
  brittle assertions with `test_measures.py`) and, for a UI slice, the
  **criteria walk**: `accessibility-engineer` opens the built app in the
  real browser, drives every acceptance criterion a browser can reach and
  writes a table (PASS / FAIL / NOT REACHABLE, how, a screenshot), the
  screen-reader announcements the owner's only manual item; a FAIL is a
  finding for the fix round, a NOT REACHABLE row goes to the owner's
  checklist issue. One fix round as in C (under `light`, each chunk's
  findings go back to that chunk's own builder by message, an Opus fixer
  for what it cannot clear), and the **stranger test**: the smoke agent
  follows the README on a fresh clone in the last round, the app again
  through `scratch_run.py`.
- **E. Delivery, all in the foreground:** the log and the records are
  committed first (`Records: slice <nnn> delivery`, the handoff file
  removed), since `delivery` refuses a dirty tree; CI is written if the
  repository has none (`release-engineer:ci-pipeline`), the branch is pushed and a
  pull request opened without asking (`release-engineer:delivery`, body
  by `pr-writeup`: what was built, the decisions, the Definition of Done
  table, the standing Mediums, the Known Lows grouped by theme), **only
  standing Mediums are filed as issues** (Lows stay in the body), the
  external reviewer's comments are triaged
  (`code-reviewer:external-review-triage`: fix, decline with a reply, or
  defer to an issue) for up to five rounds, the cost is computed from the
  transcripts of every session the sidecar names (`cost_by_role.py`; a
  session with no transcript on disk means `cost not measured`, never a
  partial total) and written on the E line, and the audit material is
  synced to the audit repository once more when one is configured, in the
  same turn as the last issue.

Every launch passes `model` and `maxTurns` explicitly (an agent
definition's lines are not applied in practice); every reviewer writes
its report to a file in the records directory (`planning/implementation/`,
committed as `Records: slice <nnn> chunk <k>` after each chunk) and hands
back counts, so no report is carried in the orchestrator's context. The
log entry for the row has one bold line per step and per chunk, with
commit hashes and per-round counts, and indented plain bullets for
decisions and corrections; the detail lives in the reviewer files and the
sidecar. A context clear or a session end mid-loop writes a handoff file
the next invocation resumes from.

## Running the chunk loop: the sandbox

The loop launches code-writing instances and reviewers that run unattended
with Bash in hand. A plugin cannot ship the settings that fence them (a
plugin's settings carry no `sandbox` or `permissions` keys, and a
plugin-shipped agent's `permissionMode` and `hooks` are ignored), so the
fence is the launcher's: `bin/kad` writes the sandbox runtime's settings
from the approved set and starts the whole session inside it, and the
orchestrator checks that fence before the flow starts and before every
launch, with `skills/orchestrator/scripts/sandbox_check.py --project
<root>`. Because the script runs inside the fence, it probes it instead of
trusting the file: a write to the home directory must fail with the
sandbox's own error; a direct TCP connection to each of two public
addresses must fail with "network unreachable" (a timeout or a refusal is a
firewall, not a sandbox); no credential-shaped environment variable may
reach the shell (the one the launcher kept, `GH_TOKEN`, is reported as
kept); each credential path must be unreadable from the shell if it exists
and named in the runtime's `denyRead` whether or not it exists (a login can
create one later); the runtime's `allowWrite` may open nothing beyond the
project, Claude Code's own paths, temp, npm's cache and the launcher's own
folders (its `gh` config directory, the audit directory and the settings
directory, named on the line; before 0.14.0 the check failed every
launcher session on them and the owner clicked through); and the project's
`.worktreeinclude`, which copies gitignored files into every worktree, may
match no credential-shaped file. `--secret <path>` adds a path to the
list, with a trailing `/` for a directory that may not exist yet. The last
line is `sandbox check: PASS` or `FAIL`; the exit code is 0, 1 for a
failing check, 2 when the platform has no sandbox. Under the launcher a
`FAIL` is reported and the flow stops with no question: the cause is
outside the session. `python3 -I evals/tools/sandbox_check_test.py`
covers the write check against the launcher's folders, `python3 -I
evals/tools/source_scan_test.py` the source scan, its two gates and the
planning rule's wording in the five skills that carry it, `python3 -I
evals/tools/audit_sync_test.py` the audit sync's transcript rules, and
`python3 -I evals/tools/mutation_pass_test.py` the mutation runner.

The runtime (`npm install -g @anthropic-ai/sandbox-runtime`) wraps the
whole Claude Code process in the platform's boundary, Seatbelt on macOS
and bubblewrap on Linux and WSL2, so the Read tool, hooks and MCP servers
are inside it too. Native Windows has no backend: run `kad` from WSL2
(`wsl -d Ubuntu-22.04`, from the project's path there). What the launcher
writes for a project, every key required (the runtime refuses a file
missing one rather than run on defaults that would drop its rules):

```json
{
  "filesystem": {
    "allowWrite": ["<project>", "~/.claude", "~/.claude.json", "/private/tmp", "~/.npm",
                   "~/.config/kad-dev-team/gh", "~/.claude/kad-audit"],
    "denyWrite": ["~/.claude/settings.json", "~/.claude/settings.local.json", "~/.claude/hooks",
                  "~/.claude/commands", "~/.claude/agents", "~/.claude/skills", "~/.claude/plugins"],
    "denyRead": ["~/.ssh", "~/.aws", "~/.gnupg", "~/.kube", "~/.config/gcloud", "~/.azure",
                 "~/.config/gh", "~/.npmrc", "~/.netrc", "~/.git-credentials", "~/.pypirc",
                 "~/.docker/config.json", "~/.terraform.d/credentials.tfrc.json",
                 "~/.claude/.credentials.json"],
    "allowRead": []
  },
  "network": {
    "allowedDomains": ["api.anthropic.com", "claude.ai", "platform.claude.com", "github.com", "*.github.com",
                       "registry.npmjs.org", "bridge.claudeusercontent.com", "mcp-proxy.anthropic.com"],
    "deniedDomains": [],
    "allowLocalBinding": true,
    "tlsTerminate": { "excludeDomains": ["bridge.claudeusercontent.com", "mcp-proxy.anthropic.com"] },
    "allowUnixSockets": ["/tmp/claude-mcp-browser-bridge-<user>"]
  },
  "allowPty": true
}
```

`allowPty` is macOS-only: without it the runtime's profile denies the
terminal devices, Claude Code's `setRawMode` fails with `EPERM`, and every
arrow key and mouse report lands in the session as text (`^[[A`,
`^[[<35;…M`). The grant the runtime emits for it is every `/dev/ttys*`,
not only the session's own terminal, so a command inside the fence can
reach another terminal the same user has open; the runtime offers no
narrower rule, and an interactive session cannot run without one. It is
the one place the fence is as wide as the user's own terminals. On Linux
the temp path is `/tmp` and Chrome's socket is `allowAllUnixSockets`
(seccomp cannot filter by path). `tlsTerminate` is the runtime's own
local proxy terminating TLS with a trust bundle, without which `gh` (Go)
cannot verify a certificate on macOS; the two bridge hosts are excluded
because the proxy refuses the WebSocket upgrade the extension needs.
Nothing inside the session can change the file, which is the point. The
runtime is a beta research preview; its keys may move.

## Installing for real (once pushed to a repo)

```bash
/plugin marketplace add <your-repo-url>
/plugin
```
Then browse to `kad-dev-team-marketplace` → `kad-dev-team` and install at
user scope.

## Adding a new persona

1. Pick the next row from the roster table in [PERSONAS.md](./PERSONAS.md).
2. Synthesize from all three reference sources (see PERSONAS.md's
   Attribution philosophy) into `.synthesis/<slug>.md`.
3. Write its backing skill(s), one per distinct trigger the persona handles:
   `skills/<trigger-slug>/SKILL.md`.
4. Write the persona: `agents/<persona-slug>/AGENT.md`, referencing each
   skill it uses in its frontmatter `skills:` list.
5. Test with `--plugin-dir` (above).
6. Build its eval suite per the playbook in `evals/README.md`: plant its
   violations and traps in `evals/fixtures/library-app/app/`, scaffold
   cases with `evals/tools/new-case.sh`, calibrate with
   `--ablation with-without --scaffold`.
7. Flip its Status to Done in PERSONAS.md.
