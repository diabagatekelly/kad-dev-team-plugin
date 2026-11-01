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
  orchestrator/scripts/sandbox_check.py    # the loop's first step: the session's Bash sandbox probed from
                       # inside, secrets unreadable, no direct network, escape hatches off; exit 2 when
                       # the platform has no sandbox at all, which the orchestrator turns into a logged
                       # choice, not a stop (see below); --write-settings then writes the deny rules only
  orchestrator/scripts/readiness_check.py  # the design-readiness gate before the first builder: eight
                       # mechanical checks over the planning documents, each failure routed to the
                       # persona that owns the document
  orchestrator/scripts/rounds_record.py    # a review or smoke report in the shared finding format into the
                       # fix-round sidecar, classified regression or pre-existing against the fix's
                       # diff, and the counts for the log line; --standing lists what is carried
  orchestrator/scripts/done_check.py       # the Definition of Done at the slice review: README, lint and
                       # formatter, typecheck, no code in strings, no planning references, comment
                       # density, persisted names, env defaults, test padding
  orchestrator/scripts/audit_sync.py       # the loop's last step when KAD_AUDIT_REPO is set: a slice's planning
                       # documents, log, report, map, reviewer reports and fix-round sidecar copied into
                       # the audit repository's clone, refused on a credential-shaped string, committed
                       # and pushed
  map-update/scripts/extract_map.py        # the architecture map extractor (TypeScript, JavaScript, Python):
                       # modules, import edges, externals, exports, tiers carried from the prior map,
                       # the diff and the two candidate flags; a language without one is listed with
                       # no edges and said so, never hand-parsed
hooks/
  hooks.json, audit.sh # audit mode: off unless KAD_AUDIT=1 (see below); with KAD_AUDIT_REPO set, the
                       # SessionStart hook clones the audit repository into the project's audit-docs/
evals/
  <case>/case.yaml     # a `claude plugin eval` case (negative trigger cases use prompt.md + graders/)
  fixtures/library-app # shared fixture app with an answer key; personas plant defects in overlays
  thresholds.json      # each case's bar for the eval gate
  tools/               # eval_gate.py, affected_cases.py, record_thresholds.py, rejudge.py,
                       # freeze-history.sh, audit_report.py, orchestrator_log_check.py (a real
                       # project's log against the orchestrator's rules), implementation_judge.py (the
                       # blind pairwise judge of two implementations, kept for the evals), pairwise_judge.py
                       # (with/without arms, over that judge), compare_arms.py (heavy against lite tdd
                       # builds from kept runs, the same judge), new-case.sh,
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

Everything a real run needs is one command, run from the project's root:

```bash
<plugin root>/bin/kad            # alias kad=<plugin root>/bin/kad once, then just: kad
kad --check                      # show what it would do, start nothing
kad -- --resume                  # arguments after -- go to claude
```

It checks the platform and the tools (macOS, Linux and WSL2 have the
runtime's backend; native Windows is told to use WSL2; `claude` and
`python3` must be on PATH; the sandbox runtime is offered for install
when missing), writes the runtime's settings for this project under
`~/.config/kad-dev-team/srt/` (writes allowed to the project, Claude
Code's config directory, the temp directory and npm's cache, with the
user settings, hooks, commands, agents, skills and plugins under that
config directory denied so nothing an agent writes outlives the session;
the credential paths denied for reading; the network allowed to the API,
sign-in and GitHub plus the domains you add), drops credential-shaped
variables from the environment the session inherits (`--keep-env NAME`
passes one through, and the orchestrator's check then names it), gives
the session what the loop's commits, pushes, pull requests, issues and
audit sync need inside the fence (the host's GitHub login from `gh auth
token` as `GH_TOKEN`, the one credential the session holds, which the
orchestrator's check reports as kept; `--gh-token-env NAME` takes a
fine-grained token for the one repository instead, narrower than the
login's scope; a session-local `gh` config directory, since its own is
on the deny list; `gh` as git's credential helper in place of the
keychain the fence refuses; and the runtime's TLS termination, without
which `gh` cannot verify a certificate on macOS), turns
audit mode on with the audit repository you named, and starts `srt
claude --plugin-dir <this plugin>` inside that fence, so the Read tool,
hooks and every agent are inside it too. The first run asks three
questions, audit mode (on by default), the audit repository and any
extra domains (`registry.npmjs.org` for npm installs), and stores the
answers, owner-readable only, in `~/.config/kad-dev-team/launcher.json`;
`kad --reset` asks again. On that first run `--audit`, `--no-audit`,
`--audit-repo` and `--domain` answer the questions instead of the
terminal and are stored (how the orchestrator runs it); on every later
run they change that one run and store nothing. `kad --check` shows the
plan and writes nothing; `--install-runtime` installs the sandbox runtime
without asking when it is missing. Local
ports are allowed by default (a dev server, its tests and the loop's
smoke run bind and reach `localhost`; `--no-local` denies them for a
slice that touches no port). `kad --chrome` adds the extension's bridge
domain and starts `claude --chrome`, so Claude in Chrome can open
`localhost:3000` in your real Chrome, which runs outside the fence; enable
the extension once outside the fence first (`claude --chrome`, which
writes Chrome's native-messaging file under `~/Library` or `~/.config`,
paths the fence denies). The
orchestrator's sandbox check reads the same settings file
(`KAD_SRT_SETTINGS`) before it launches anything and names whatever is
missing. The launcher itself writes nothing outside
`~/.config/kad-dev-team/`; the session it starts writes where the
settings allow.

You can also start Claude the usual way and say "what's next": the
orchestrator's step 0, session setup, runs before it asks anything else.
It finds the session is not under the launcher, asks whether you want
audit mode (and, the first time, the audit repository and extra domains),
runs `kad --prepare` itself with your answers, and asks one more
question: restart in the fence, which opens a new terminal window with
the fenced session on the project, the orchestrator already started in
it (`kad --relaunch`; you close the old one), or continue in this
session with the per-command sandbox and no audit. It asks this once per
session, never on a flow resumed from a handoff file, and never in a
session that has no shell to run the launcher with. Nothing needs `kad`
on your PATH: the orchestrator and the relaunch use the script's full
path, which for a marketplace install is under
`~/.claude/plugins/cache/kad-dev-team-marketplace/kad-dev-team/<version>/bin/kad`
(and changes with the version, which is why an alias is a convenience
for your own terminal, not something the plugin relies on). The sections
below say what each piece does by hand.

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
choose: a separate repository, cloned at session start into the project's
`audit-docs/` and listed in the project's `.git/info/exclude`, so the
project's own `.gitignore` and history never mention it. At the end of
each delivered slice the orchestrator runs `audit_sync.py`, which copies
that slice's planning documents, orchestrator log, implementation report,
architecture map, reviewer reports and fix-round sidecar into
`audit-docs/<project>-slice-<n>/`, refuses if anything it would copy looks
like a credential, and commits and pushes in the clone. Run it by hand
with `python3 -I skills/orchestrator/scripts/audit_sync.py --project
<root> --slice <n>` (add `--transcripts` to include the kept session
transcripts, `--no-push` to only commit). In this repo, ask Claude to "review the audit logs"
(the `audit-review` skill): it reads the flagged sessions against the
skills' own rules and proposes fixes and eval cases.
`evals/tools/audit_report.py` gives the raw overview, and
`evals/tools/orchestrator_log_check.py <project dir>` checks a project's
`orchestrator-log.md` against the orchestrator's rules and the kept
transcripts.

## Implementation policy: heavy or lite

Before the chunk loop launches anything, the orchestrator asks once per
slice which skill the implementer builds every chunk with:

- **heavy** (default): `tdd-implementation`, the full prescribed loop (Test
  List, one test at a time, RED seen failing, a `test-quality-review`
  self-check every cycle, the can-it-fail check).
- **lite**: `tdd-implementation-lite`, the same contract (what the
  implementer owns, where things go, how a gap is escalated, what the
  report holds) as test-first with verification rather than TDD: the tests
  before the code, seen failing on their own assertions against a stub,
  then shown to catch a deliberate break, with the loop between left to
  the model. On the first real slice it cost about a quarter of heavy for
  the same design quality.

The policy is recorded on the log's A line. `tdd-implementation-lite` is
never chosen from a plain "build it": it runs only when a task names it.

## The chunk loop

The orchestrator's `tdd-coach:tdd-implementation` row builds a slice as a
series of small commits on a slice branch, each checked before the next
starts, and delivers the branch as a pull request. This is the v4 shape
(`.synthesis/implementation-flow-v4.md`), redesigned after the second real
run cost $346 and 14.5 hours for a slice that was not production-grade:
the money moves upstream into design completeness and to the seam and the
finish, and the review loop keeps only what the data said earned its
place. In order:

- **A. Start:** a repository and an `origin` must exist (otherwise
  `release-engineer:repo-bootstrap`, decided with the owner); the sandbox
  check (below); then up to four questions, **one per `AskUserQuestion`
  call**, in order: settings, sandbox, policy, delegation. On "yes" to the
  delegation question the orchestrator writes
  `planning/delegation-slice-<nnn>.md` (the owner's words, what it covers,
  what it never covers), which is what lets a persona settle a mid-build
  decision without the owner. The **budget line** is written: 5 h of loop
  time, 2 reviewer launches per chunk, 1 fixer per scope plus 1 for
  regressions, 8 consults; counted at every chunk boundary, and the flow
  ends at the boundary that exceeds one. A `slice-<nnn>-<slug>` branch
  (uncommitted planning documents are committed on it first), the base
  commit recorded. Then the **design-readiness gate**
  (`readiness_check.py`): every criterion homed in the design, every
  failure path homed, a number on every retry, wait and give-up, security
  and reliability agreeing, a mockup for every named state, no question
  routed to "the implementer", a "Kept for later slices" line, a row for
  an external provider's unusable reply. Each failure is a backward route
  to the persona that owns the document before any builder launches.
- **B. Plan:** one implementer (Sonnet) reads the slice, consults the map
  and writes a **chunk plan** into the implementation report: two to
  eight vertical chunks, each with a title, the criteria it delivers, its
  files, its done check (which names a **seam test**: through the real
  composition root, the real adapters and the real local store, only the
  external service faked at its wire boundary) and the territories it
  touches. The orchestrator checks the plan mechanically and commits it.
- **C. Chunks:** for each chunk a fresh implementer (Sonnet, short
  context, `maxTurns` 120) builds it test-first, the seam test first,
  comments only where `why-comments` would keep one, and commits it with
  the chunk's title. The gate runs on the commit range: suite, typecheck,
  lint, scope (the chunk's files plus the design's module directories; a
  file inside a module but off the list is a recorded deviation, not a
  failure), protected documents, coverage, and report-only comment
  density and size figures. Then **two launches, never more**: one
  combined reviewer (`code-reviewer`, Opus: `code-review`,
  `test-quality-review` and, when the chunk touches HTTP, storage or
  error handling, `reliability-review`, one report, at most eight
  findings, Critical/High/Medium only) and one **smoke run** (the app
  started as the README says, the chunk's done check driven through the
  real interface; `accessibility-engineer` in the browser when the chunk
  touches UI, else `tdd-coach` over HTTP). Then **one fix round**: a
  fresh fixer (Sonnet) for every finding, the gate, a regressions-only
  re-review on the fix's diff, a second and last fixer for the
  regressions, the gate, done. Pre-existing findings the re-review raises
  stand: a standing Critical or High stops the loop for the owner, a
  standing Medium goes to the pull request body. A finding no planning
  document can settle is `needs-decision (<persona>)`: with the
  delegation file the owning persona is launched once, writes its own
  document, commits `Decision <n>`, and the orchestrator logs one line;
  without it the flow stops for the owner. `rounds_record.py` is the only
  thing that parses a report; it writes the sidecar and prints the C
  line's counts. No Lows per chunk.
- **D. Slice review:** the map is regenerated with the shipped extractor;
  the **Definition of Done** runs (`done_check.py`: README, linter and
  formatter clean, typecheck, no code in strings, no planning reference in
  code, comment density at or under 5%, the next slice's names persisted,
  env defaults not production, tests not padding), with
  `docs-writer:readme` for the README and one Sonnet fixer for the batch;
  then the six reviewers once on the whole slice diff (Lows allowed here),
  one fix round as in C, and the **stranger test**: the smoke agent
  follows the README on a fresh clone in the last round.
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
  transcripts (`cost_by_role.py`) and written on the E line, and the audit
  material is synced to the audit repository when one is configured, in
  the same turn as the last issue.

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
orchestrator checks the session it is about to run in, first thing, before
any question, and again before every launch. You don't have to write the
settings by hand: on a fixable failure the orchestrator asks once whether
to write them into the session's user settings (`settings.json` under
`CLAUDE_CONFIG_DIR`, or `~/.claude`), runs `sandbox_check.py
--write-settings` on a yes, and continues if the re-check passes. When the
session's sandbox is already on but incomplete, Bash cannot write a file
outside the project, so the script prints the intended content and the
orchestrator writes it with its Write tool, which runs outside the
sandbox. What it writes:

```json
{
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "failIfUnavailable": true,
    "excludedCommands": [],
    "autoAllowBashIfSandboxed": true,
    "network": { "allowedDomains": [] },
    "filesystem": {
      "denyRead": ["~/.ssh", "~/.aws", "~/.gnupg", "~/.kube", "~/.config/gcloud", "~/.azure",
                   "~/.config/gh", "~/.npmrc", "~/.netrc", "~/.git-credentials", "~/.pypirc",
                   "~/.docker/config.json", "~/.terraform.d/credentials.tfrc.json",
                   "~/.claude/.credentials.json"]
    }
  },
  "permissions": {
    "deny": ["Read(~/.ssh/**)", "Read(~/.aws/**)", "Read(~/.gnupg/**)", "Read(~/.kube/**)",
             "Read(~/.config/gcloud/**)", "Read(~/.azure/**)", "Read(~/.config/gh/**)",
             "Read(~/.npmrc)", "Read(~/.netrc)", "Read(~/.git-credentials)", "Read(~/.pypirc)",
             "Read(~/.docker/config.json)", "Read(~/.terraform.d/credentials.tfrc.json)",
             "Read(~/.claude/.credentials.json)"]
  }
}
```

What each part is for: the sandbox confines what the Bash tool runs
(writes to the project and the temp directory, network only through its
proxy to `allowedDomains`) but lets a command read the whole machine
unless `denyRead` names the path; the `permissions.deny` rules repeat the
list for the Read tool, which runs outside the sandbox and which every
implementer holds (a directory needs the `/**` form, or the rule covers
the directory and not its files); `allowUnsandboxedCommands: false` makes
a retry with `dangerouslyDisableSandbox` a no-op; `failIfUnavailable:
true` makes a session with no sandbox backend refuse to start instead of
running every command unsandboxed; an empty `excludedCommands` leaves no
command outside the sandbox; `autoAllowBashIfSandboxed` lets sandboxed
commands run without an approval prompt no unattended agent could answer.
Don't deny `~/.claude` wholesale: the plugin's own scripts live under
`~/.claude/plugins/`. `allowedDomains` is the project's call (a test run
that needs a registry names it); the orchestrator records the list in the
log.

Which sandbox a platform has:

| Platform | Sandbox | What the check does |
|---|---|---|
| macOS | Seatbelt | probes it; writes the settings on a yes |
| Linux | bubblewrap and socat | probes it; writes the settings on a yes |
| Windows, WSL2 session | bubblewrap and socat | probes it; writes the settings on a yes |
| Windows, native session | none; Claude Code runs every command unsandboxed | exits 2; the orchestrator asks once whether to continue unsandboxed (the `Read(...)` deny rules and `denyRead` are still written, but never `sandbox.enabled` or `failIfUnavailable`, which with no backend would make the session refuse every command) or to stop and run the session in WSL2, and logs the choice |

The stronger fence, and the one to use for a real slice, is the sandbox
runtime: `npm install -g @anthropic-ai/sandbox-runtime`, then start the
session as `srt claude` from the project. It wraps the whole Claude Code
process in the same Seatbelt or bubblewrap boundary, so the Read tool,
hooks and MCP servers are inside it too, which the per-command sandbox
above never covers. It reads `~/.srt-settings.json` at launch (no file
means no network and no writes outside its own paths, so write one
first); the check recognises it (`SANDBOX_RUNTIME=1`), reads that file
for the deny list and the write grants, and passes the `settings` check
on its own, since Claude's sandbox keys are optional inside it. A file
that fences a slice:

```json
{
  "filesystem": {
    "allowWrite": [".", "~/.claude", "~/.claude.json", "/private/tmp"],
    "denyWrite": [],
    "denyRead": ["~/.ssh", "~/.aws", "~/.gnupg", "~/.kube", "~/.config/gcloud", "~/.azure",
                 "~/.config/gh", "~/.npmrc", "~/.netrc", "~/.git-credentials", "~/.pypirc",
                 "~/.docker/config.json", "~/.terraform.d/credentials.tfrc.json",
                 "~/.claude/.credentials.json"],
    "allowRead": []
  },
  "network": {
    "allowedDomains": ["api.anthropic.com", "claude.ai", "platform.claude.com", "github.com", "*.github.com"],
    "deniedDomains": []
  }
}
```

Every one of those keys is required (the runtime refuses a file missing
any, rather than run on defaults that would drop its rules). On Linux
use `/tmp` in place of `/private/tmp`. `allowWrite`'s `.` is where
`srt` starts, so start it from the project; add the registry a test run
installs from (`registry.npmjs.org`) when the project needs it.
Nothing inside the session can change that file, which is the point: the
check reports what is missing and the flow stops until the owner restarts
with it. The runtime is a beta research preview; its keys may move. It
runs on macOS, Linux and WSL2, not on native Windows.

So on native Windows the loop is a strong recommendation to use WSL2
(start Claude inside Ubuntu, from the project, and say "what's next"),
never a hard stop: the owner can say "continue unsandboxed" once, and the
log's A line carries that choice for the audit. The settings live in that
session's user file; a `--settings` flag on the session's command line is
not a file and the check cannot see it, so start the session without one,
or put the block in managed settings, where nothing can loosen it.

`skills/orchestrator/scripts/sandbox_check.py --project <root>` is what
the orchestrator runs, inline, before each launch. Because it runs inside
the session's own Bash sandbox, it probes the fence instead of trusting
the file: a write to the home directory must fail with the sandbox's own
error, a direct TCP connection to each of two public addresses must fail
with "network unreachable" (a timeout or a refusal is a firewall, not a
sandbox), no credential-shaped environment variable may reach the shell
(Claude Code's own `CLAUDE_CODE_*` are listed and exempt), each
credential path must be unreadable from the shell if it exists and named
in `denyRead` whether or not it exists (a login can create one later),
and each must be covered by a `Read(...)` rule, recursive for a directory
(`*` does not cross a slash in the matcher, so `Read(~/.ssh/*)` does not
count); the settings above it reads from the merged settings files, since
an escape hatch leaves no trace until it is used; and the project's
`.worktreeinclude`, which copies gitignored files into every worktree, may
match no credential-shaped file, by name or by living under a credential
directory, with gitignore's `**/` rules. `--secret <path>` adds a path to
the list, with a trailing `/` for a directory that may not exist yet. The
last line is `sandbox check: PASS` or `FAIL`; the exit code is 0, 1 for a
failure the settings can fix, 2 when the platform has no sandbox.

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
