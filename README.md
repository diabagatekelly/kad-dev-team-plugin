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
  orchestrator/scripts/validation_gate.py  # the quarantine flow's mechanical gate: suite green,
                       # scope, protected files, coverage; run per candidate before any reviewer,
                       # and on the finalized build before it is reviewed in full
  orchestrator/scripts/pairwise_judge.py   # the flow's blind pairwise judge: both candidates' changes,
                       # unlabelled, both orders, reasons kept; run in Combine before the orchestrator's call
  orchestrator/scripts/sandbox_check.py    # the flow's precondition: the session's Bash sandbox probed from
                       # inside, secrets unreadable, no direct network, escape hatches off (see below)
hooks/
  hooks.json, audit.sh # audit mode: off unless KAD_AUDIT=1 (see below)
evals/
  <case>/case.yaml     # a `claude plugin eval` case (negative trigger cases use prompt.md + graders/)
  fixtures/library-app # shared fixture app with an answer key; personas plant defects in overlays
  thresholds.json      # each case's bar for the eval gate
  tools/               # eval_gate.py, affected_cases.py, record_thresholds.py, rejudge.py,
                       # freeze-history.sh, audit_report.py, pairwise_judge.py (with/without arms,
                       # a wrapper over the plugin's judge above), new-case.sh,
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
```

The plugin's hooks then log each prompt and every `kad-dev-team` skill and
agent call, and keep the full transcript of any session that used the
plugin. Nothing leaves your machine, and sessions that never used the
plugin aren't kept. In this repo, ask Claude to "review the audit logs"
(the `audit-review` skill): it reads the flagged sessions against the
skills' own rules and proposes fixes and eval cases.
`evals/tools/audit_report.py` gives the raw overview.

## Running the quarantine flow: the sandbox

The orchestrator's `tdd-coach:tdd-implementation` row launches three
code-writing instances and up to eighteen reviewers that run unattended
with Bash in hand. A plugin cannot ship the settings that fence them (a
plugin's settings carry no `sandbox` or `permissions` keys, and a
plugin-shipped agent's `permissionMode` and `hooks` are ignored), so the
flow checks the session it is about to run in, before every step that
launches agents, and refuses to launch when the check fails. You don't
have to write the settings by hand: on a failed check the orchestrator
asks once whether to write them into the session's user settings
(`settings.json` under `CLAUDE_CONFIG_DIR`, or `~/.claude`), runs
`sandbox_check.py --write-settings` on a yes, and continues if the
re-check passes. The script merges only what it needs, keeps the rest of
the file and its mode, and writes through a symlink. When the session's
sandbox is already on but incomplete, Bash cannot write a file outside
the project, so the script prints the intended content and the
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

What each part is for: the sandbox (macOS Seatbelt; bubblewrap and socat
on Linux and WSL2) confines what the Bash tool runs — writes to the
project and the temp directory, network only through its proxy to
`allowedDomains` — but lets a command read the whole machine unless
`denyRead` names the path; the `permissions.deny` rules repeat the list
for the Read tool, which runs outside the sandbox and which every
`tdd-implementation` instance holds (a directory needs the `/**` form, or
the rule covers the directory and not its files);
`allowUnsandboxedCommands: false` makes a retry with
`dangerouslyDisableSandbox` a no-op; `failIfUnavailable: true` makes a
session with no sandbox backend refuse to start instead of running every
command unsandboxed; an empty `excludedCommands` leaves no command
outside the sandbox; `autoAllowBashIfSandboxed` lets sandboxed commands
run without an approval prompt no unattended agent could answer. Don't
deny `~/.claude` wholesale: the plugin's own scripts live under
`~/.claude/plugins/`. `allowedDomains` is the project's call (a test run
that needs a registry names it); the orchestrator records the list in
the log. On native Windows there is no sandbox at all — Claude Code runs
commands unsandboxed — so the flow runs in a WSL2 session there, and a
settings file is the one thing the script cannot write for you: start
Claude inside Ubuntu, from the project, and say "what's next". The
settings live in that session's user file; a `--settings` flag on the
session's command line is not a file and the check cannot see it, so
start the session without one, or put the block in managed settings,
where nothing can loosen it.

`skills/orchestrator/scripts/sandbox_check.py --project <root>` is what
the orchestrator runs, inline, before each launch (the candidates, each
round of reviewers, the finalize instance). Because it runs inside the
session's own Bash sandbox, it probes the fence instead of trusting the
file: a write to the home directory must fail with the sandbox's own
error, a direct TCP connection to each of two public addresses must fail
with "network unreachable" (a timeout or a refusal is a firewall, not a
sandbox), no credential-shaped environment variable may reach the shell
(Claude Code's own `CLAUDE_CODE_*` are listed and exempt), each
credential path must be unreadable from the shell if it exists and named
in `denyRead` whether or not it exists (a login can create one later),
and each must be covered by a `Read(...)` rule, recursive for a directory
(`*` does not cross a slash in the matcher, so `Read(~/.ssh/*)` does not
count); the settings above it
reads from the merged settings files, since an escape hatch leaves no
trace until it is used; and the project's `.worktreeinclude`, which
copies gitignored files into every worktree, may match no
credential-shaped file, by name or by living under a credential
directory, with gitignore's `**/` rules. `--secret <path>` adds a path to
the list, with a trailing `/` for a directory that may not exist yet. The
last line is `sandbox check: PASS` or `FAIL`; nothing is launched on
`FAIL`, and the orchestrator reports what to change rather than working
around it.

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
