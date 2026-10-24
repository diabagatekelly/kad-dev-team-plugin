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
  orchestrator/scripts/validation_gate.py  # the chunk loop's mechanical gate: suite green, scope,
                       # protected files, coverage; run on every chunk commit and every fix commit
                       # before any reviewer; --accept-protected takes in a protected document the
                       # user amended while the loop was running
  orchestrator/scripts/ts_runtime_lines.mjs # which lines of a TypeScript file keep runtime code, for the
                       # gate's coverage check (type-only modules exempt, erased type lines discounted)
  orchestrator/scripts/sandbox_check.py    # the loop's first step: the session's Bash sandbox probed from
                       # inside, secrets unreadable, no direct network, escape hatches off; exit 2 when
                       # the platform has no sandbox at all, which the orchestrator turns into a logged
                       # choice, not a stop (see below)
  orchestrator/scripts/audit_sync.py       # the loop's last step when KAD_AUDIT_REPO is set: a slice's planning
                       # documents, log, report, map, reviewer reports and fix-round sidecar copied into
                       # the audit repository's clone, refused on a credential-shaped string, committed
                       # and pushed
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

## Local development

Load this plugin directly from disk without installing it, so changes take
effect on the next restart:

```bash
claude --plugin-dir /Users/kellydiabagate/Documents/kad-developer-suite
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
starts, and delivers the branch as a pull request. In order:

- **A. Start:** the sandbox check (below), the policy question, a
  `slice-<nnn>-<slug>` branch (uncommitted planning documents are committed
  on it first), the base commit recorded.
- **B. Plan:** one implementer (Sonnet) reads the slice, consults the map
  and writes a **chunk plan** into the implementation report: four to
  eight vertical chunks, each with a title, the criteria it delivers, its
  files, its done check and the reviewer territories it touches. The
  orchestrator checks the plan mechanically and commits it.
- **C. Chunks:** for each chunk a fresh implementer (Sonnet, short
  context, a turn cap) builds it test-first and commits it with the
  chunk's title. The gate runs on the commit range. Reviewers (Opus) read
  the diff: test-quality, code and architecture always; security,
  reliability and accessibility when the chunk's territories call for
  them. Every Critical, High and Medium goes to a fresh fixer (Sonnet),
  the gate and the chunk's reviewers run again on the fix, and so on
  until a round is clean, capped at five rounds; new findings are
  classified as regressions (inside the fix's diff) or pre-existing, and
  every round is recorded in a sidecar the audit tools read. A standing
  Critical or High after the cap stops the loop for the user; Lows are
  listed, never fixed here.
- **D. Slice review:** the map is regenerated, all six reviewers read the
  whole slice diff, and the same fix rounds apply.
- **E. Delivery:** CI is written if the repository has none
  (`release-engineer:ci-pipeline`), the branch is pushed and a pull request
  opened without asking (`release-engineer:delivery`, body by
  `pr-writeup`), every Low and standing Medium is filed as an issue in the
  project's recorded tracker, the external reviewer's comments are triaged
  (`code-reviewer:external-review-triage`: fix, decline with a reply, or
  defer to an issue) for up to five rounds, and the audit material is
  synced to the audit repository when one is configured.

Every launch passes `model` explicitly (an agent definition's `model:`
line is not applied in practice); every reviewer writes its report to a
file under the audit directory and hands back counts, so no report is
carried in the orchestrator's context. The log entry for the row has one
terse line per step and per chunk, with commit hashes and per-round
counts; the detail lives in the reviewer files and the sidecar.

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
| Windows, native session | none; Claude Code runs every command unsandboxed | exits 2; the orchestrator asks once whether to continue unsandboxed (the `Read(...)` deny rules are still written) or to stop and run the session in WSL2, and logs the choice |

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
