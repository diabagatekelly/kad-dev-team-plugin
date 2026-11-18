---
name: technology-bootstrap
description: Decide the smallest set of technology choices that must exist before a slice's first failing test can be written — language, runtime, test runner, package manager and its pinning posture — give everything a later chunk of the slice may force one default, the runtime's built-in unless a chunk forces a dependency, approved once as a set, and leave what no chunk forces explicitly open. Recommends with trade-offs and gets approval; never decides unilaterally. Use when a designed slice is about to be implemented in a repo that has no stack yet, when a later slice forces a technology category nothing has chosen, or when a chunk forces a dependency the approved set excluded.
---

# Technology Bootstrap

## What this decides

The smallest set of technology choices that must exist before the first
failing test can be written in a repo that has none — and nothing else.
This is not a stack plan for the project. It's the answer to "what has to
be true before anyone can type `test` and watch it fail?"

Everything a slice doesn't force stays explicitly undecided, with a named
owner. That's the whole discipline here: an empty repo invites deciding the
entire stack in one sitting, and most of those decisions would be made
against a system nobody has built yet.

## The demand test

One question per candidate technology:

> **Can this slice's first failing test be written without deciding this?**

Yes → don't ask. That's the only filter.

"Is it project-specific?" is *not* a filter, and reaching for it is the
most likely way to get this wrong. A CI/CD pipeline is not project-specific
and still doesn't belong here: the slice ships without one, so asking
produces infrastructure ahead of need — the "technical plumbing" shape this
plugin's `vertical-slicing` skill already rejects at the slice level. The
same goes for a container runtime, a cloud provider, or an observability
stack.

**Almost always forced**, because no test can be written without them:

- **Language and runtime.**
- **Test runner** — including how tests are invoked.
- **Package manager**, and with it the **lockfile and pinning posture**.
  This one rides along whether or not anyone asks: the moment a dependency
  is installed there's a lockfile, and pinning is far cheaper to set now
  than to retrofit across a dependency tree later.

**Sometimes forced — decide by looking at the test, not the category:**

- **UI framework**, if the slice's actor is a person and the first test
  drives a screen.
- **HTTP framework**, if the actor is programmatic and the first test goes
  over the wire.

**Almost never forced by a first slice**, each with an owner:

| Category | Who owns it, and when |
|---|---|
| Database / persistence technology | `architecture-design`, per boundary — and only once the slice actually needs to survive a restart |
| Hosting, deployment, CI/CD | `devsecops-engineer:operational-readiness`, once there's a delivery path to review |
| Auth provider | `architecture-design` per boundary, with a `devsecops-engineer` consult — only if this slice authenticates someone |
| Secrets storage | Same — only if this slice actually handles a secret |

## Why persistence usually isn't forced

The most common mistake this skill exists to prevent: a design names a
persistence boundary, and that gets read as "we need to choose a database."

It isn't. A boundary is an interface. The first implementation behind it
can be in-memory — a map that lives as long as the process — and every test
for the slice's business behavior passes against it. The technology
question arrives later, when data has to outlive a restart, and by then
you'll know the access patterns instead of guessing them. The boundary was
what made deferring free.

Apply the same reasoning to anything else the design isolated behind an
interface. If a real in-memory implementation satisfies the slice's tests,
the technology behind that interface is not a bootstrap decision.

## On the package manager: prefer defaults over flags

The package manager is the one bootstrap choice that quietly sets a
security posture for the life of the project, so it gets a criterion of its
own beyond ergonomics and speed.

Managers within the same ecosystem differ in **whether the safe posture is
the default or an opt-in flag** — whether the lockfile carries content
hashes for transitive dependencies without being asked, and whether install
verifies them without being asked. Both end states look identical in a
review. They are not the same choice.

**Prefer the manager where the safe posture is the default.** A posture
that depends on a flag depends on everyone remembering the flag — every
contributor, every CI job, every one-off script someone writes in a hurry
two years from now. Defaults hold without anyone remembering anything.

Two limits on this:

- **It's a tiebreak, not an override.** Don't drag in a tool that doesn't
  fit the ecosystem or the team for this reason alone. When two credible
  options are otherwise close, this decides.
- **It's a choice, not an audit.** `supply-chain-review` owns the *standard*
  — what counts as pinned, and what keeps a lockfile honest — and it's worth
  consulting for that. Don't run it here: it audits an existing repository's
  posture, and at bootstrap there is no posture yet, no lockfile, and no
  build to compromise.

Record the resulting posture as a decision like any other, so the next
person can tell it was chosen rather than inherited.

## Recommend, don't decide

Technology choices belong to the user. Your job is to make each one easy to
decide well, not to make it.

For each forced category, one at a time: state what needs deciding, your
recommended choice and *why*, and the alternative(s) you considered and
rejected with concrete reasons — then stop and get approval via
`AskUserQuestion` before moving to the next one. Same loop
`architecture-design` runs, for the same reason: a choice surfaced only in
a finished document is a choice the user reviews rather than makes.

Two things to hold on to inside that loop:

- **A strong recommendation is still a question.** You will often have a
  genuinely obvious answer here — the ecosystem's default test runner is
  usually right. Recommend it confidently and still wait. Confidence
  changes the wording, not the loop.
- **A delegation covers what it names.** "Whatever you'd recommend for the
  test runner" approves the test runner, not the UI framework you decide
  is also forced. A category the user hasn't spoken to still gets its own
  recommendation and its own wait.
- **The default set is one question.** What a later chunk may force gets
  its defaults as one set (the next section) and one approval for the
  whole of it, not a wait per category: it decides nothing now, it says
  what the build does by default.
- **Scale the recommendation to the situation.** Ask who's building and
  maintaining this if it isn't already established. A one-person project
  and a team of eight have different right answers about tooling weight,
  and recommending the team-sized answer to one person produces setup
  nobody maintains.

## Consult `devsecops-engineer` when a choice carries a runtime-safety question

Some bootstrap choices are simultaneously security choices. When you hit
one, get the answer from the persona that owns it rather than reasoning
about it yourself.

**This is an inline consult, not a spawn.** Both personas are
`background: false`. Invoke the relevant skill with the `Skill` tool, ask
the narrow question it covers, record the answer in your decision, and
return to this skill — the same in-conversation invocation `orchestrator`
uses. The consult returns an answer, not the turn: carry on with this skill in the same response. Don't hand the
design over, and don't launch anything.

When to consult:

- **Package manager and pinning posture** → `supply-chain-review`, for its
  standard only: what "pinned" actually means and what keeps a lockfile
  honest. The choice itself stays yours — see the section above.
- **A bootstrap choice that touches secrets or authentication** →
  `security-requirements`.

Don't consult reflexively. A test runner choice carries no security
question, and manufacturing one wastes the user's turn.

## Record what you rejected

Every declined option gets written down with its reason. This is not
bookkeeping — it's what stops the same choice being relitigated in three
months, and it's the same instinct the `adr` skill's "Alternatives
considered" section serves.

"YAGNI," "too heavy for a project this size," and "we already decided
against this family" are complete reasons. A rejection with no reason is
worse than no record at all, because it looks settled without being
checkable.

## Built-ins by default for what a later chunk may force

The first failing test forces three or four choices. The build forces
more, one chunk at a time: the chunk whose seam test goes over HTTP needs
a server; the chunk that talks to the external service needs a client;
the chunk whose data must outlive a restart needs a store on disk; a
chunk may need the machine's credential store, a log, a rendered page,
a test DOM, a linter. One run left each of those "not yet decided" and
re-entered this skill six times mid-build (incident 25: `node:http`, the vendor SDK's exact pin,
`node:crypto`, `/usr/bin/security`, a JSON-lines writer on `node:fs`,
server-rendered HTML), each an interruption of the loop for a choice that
came out as the runtime's own built-in.

So settle them now, as one set, with one default: **the runtime's
built-in unless a chunk forces a dependency.** Walk the design's
boundaries and the slice's criteria once, list every category a chunk of
this slice may force that the first test does not, and give each its
default:

- the runtime's own module where it has one (on Node, `node:http` for a
  server, `node:crypto` for encryption and randomness, `node:fs` for a
  file store or a JSON-lines log);
- the operating system's own tool for an OS facility (its command for
  the credential store), called without a shell;
- the vendor's official client, exact-pinned, for the one external
  service the slice exists to integrate with (the design's third-party
  isolation names it), or plain `fetch` where the vendor has none;
- server-rendered HTML with no framework for a page the first test does
  not drive in a browser;
- a named dependency only where no built-in can do the job, with its
  reason (a test DOM for page tests; a database engine when the criteria
  require encryption a file cannot give; a linter and formatter,
  exact-pinned).

Recommend the set once, with what each default gives up (a hand-written
router and no middleware ecosystem; a file rewritten whole on each save;
a client whose transitive dependencies ride along), and get **one
approval for the whole set**: one `AskUserQuestion`, not one per
category. A category the user changes is recorded with their choice and
their reason, like any other decision. The set is not a stack plan: it
settles nothing a chunk never reaches, and a category outside every chunk
of this slice (hosting, CI, deployment, an auth provider, a store that
only a later slice needs) stays in the next section, open, with its
owner.

During the build the set is the rule. A chunk whose need is inside it
re-enters nothing: the builder uses the built-in, and its report names
the category and what it used. A chunk that needs a dependency the set
excluded (a native library, a framework, a package where the set said
"built-in") is the only re-entry: this skill again, for that category
only, appended to the document (under the orchestrator's chunk loop,
through its gap step, with `software-architect` as the persona and this
skill named), never a choice the builder makes alone.

## Gate checks, picked per stack

The chunk loop's gate runs the suite, the typecheck and the lint on every
commit. Eight more categories are things a tool decides and a reviewer
reading by eye does not (incident 36), and which tool does it depends on
the language, so the tool is picked here: once, with the default set
above, inside the same one approval.

| Category | What it holds | TypeScript or JavaScript | Python |
|---|---|---|---|
| type-aware lint | a promise nothing awaits, an `any` leaking through a call, a condition that is always true | the linter's type-checked preset (the linter's own type-aware engine when the compiler version in use has no API the preset can load) | Ruff with a wide rule selection |
| stricter compiler flags | undefined from an index, optional against undefined, a path with no return | `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitReturns`, `noFallthroughCasesInSwitch`, `noImplicitOverride`, `noPropertyAccessFromIndexSignature` | the type checker's strict mode |
| complexity and length limits | a function, a file or a line past the size a reader holds | the linter's `complexity`, `max-depth`, `max-params`, `max-lines-per-function` (function expressions counted) and `max-lines`; the formatter's line width | Ruff's complexity and size rules; the formatter's line length |
| duplication | a block copied across files | jscpd | jscpd |
| unused code | a file, export or dependency nothing uses | knip | vulture and deptry |
| changed-line coverage | new lines no test runs while the file stays above its minimum | the gate's own read of the runner's lcov report: nothing to install | diff-cover on the coverage report |
| test timeouts and random order | a test that hangs; tests that pass only in one order | the runner's own flags in the test script | pytest-timeout and pytest-randomly |
| secret and workflow scans | a committed credential; a workflow that injects, is unpinned or over-permitted | gitleaks; actionlint and zizmor once a workflow exists | the same |

For another language, the ecosystem's equivalent of each, named with why.

**And every other command the project's CI runs.** The eight are what a
stack needs a tool picked for; a ninth row, `format and other CI
checks`, has no tool to pick: it lists each check the continuous
integration runs, or will run, that the gate would otherwise not (the
format check first; a licence check, a build), with the exact command.
A check CI runs and the gate does not turns a pull request red hours
after the gate passed on the same commit: reviewers spent Highs on a
format failure, twice in one slice, and a fixer's shell edit sent a pull
request red on it. One row per command; a project with none says so in
the row ("none: CI runs nothing the gate does not").

**A tool that brings a known advisory is said with the recommendation.**
Before recommending a single-purpose tool, run the ecosystem's audit on
it where that costs one command (`npm view <tool>@<version>` is not an
audit; `npm audit` on a scratch install is), or say that it was not
checked. A tool whose dependency tree carries an open advisory at the
level the project's CI fails on is recommended only with that said, and
with the next candidate named: the owner approves the set knowing it,
and the audit job does not go red at delivery because of a tool the
gate brought in.

What the recommendation says, per category:

- **The tool, and why that one**: what the project already has first (a
  rule set of the linter it uses, a flag of its compiler, a flag of its
  runner), then one single-purpose tool, exact-pinned. A category with
  no credible tool on this stack is recorded as **not picked** with the
  reason; it is never left out without a word.
- **The limits, as numbers**: complexity 10, depth 4, parameters 4, a
  function 40 lines, a file 300, a line 100 columns, a test 5 seconds,
  unless the owner names others. A limit is a choice like any other and
  the owner may change it; a category recommended with no number has
  not been recommended.
- **The existing code is the baseline.** Only a new violation fails. A
  tool that keeps its own baseline keeps it (a suppressions file, a
  baseline file); for the others the count the tool finds today is the
  baseline in `gate-checks.json`, and the gate fails on one more. Never
  recommend clearing the existing violations first: that is a slice of
  its own, the owner's to ask for.

**Recorded twice, by two hands.** This skill writes the `## Gate checks`
section of its document (the output format below): one row per category
with the tool and its version, the command, the limits, and how the
baseline is held. The build wires them, never this skill: the tools
installed, their configuration and manifest scripts written, and
`gate-checks.json` at the project root, one entry per category
(`{"category", "name", "cmd"}` for a tool with its own baseline;
`{"category", "name", "cmd", "count": "<regex over its output>",
"baseline": <n>}` for a counted one; `{"category", "covered_by":
"suite" | "typecheck" | "lint" | "coverage", "note"}` when a check the
gate already runs holds it; `{"category", "not_picked": "<reason>"}`; and one `{"category":
"format and other CI checks", "name", "cmd"}` per command of the ninth
row).
The orchestrator's A step launches that wiring once, from this section.

A project whose bootstrap predates this section re-enters for it alone
(below): the eight rows, one approval, nothing else reopened.

## Leave the rest explicitly open

Name the categories no chunk of this slice forces as *not yet decided*,
with the owner from the table above — don't just omit them. An omitted
decision is indistinguishable from a forgotten one, which is exactly why
`vertical-slicing` writes placeholders instead of dropping criteria it
can't fill. A category in the default set above is not open: it has its
default and its approval.

## When a choice is ADR-worthy

Apply the same three-part bar `adr` uses — architectural, significant,
non-obvious. A runtime choice that the whole system's hiring and library
ecosystem follows from usually clears it; a test runner usually doesn't.
Say so at the moment you present that decision, keep a running list, finish
the approval loop, then hand off to `docs-writer` inline in the same
session.

## Output format

```markdown
# Technology bootstrap: <what forced this>

## Situation
Who's building and maintaining this, and the slice whose first test is
being unblocked. Everything below is scaled to this.

## Decided
One entry per forced category: the choice, why this slice forced it, the
recommendation made, and what the user approved or changed. Note any
flagged as ADR-worthy.

## Built-in unless a chunk forces a dependency
The set, approved once: one line per category a chunk of this slice may
force, its default (the runtime's module, the OS tool, the vendor's
exact-pinned client, plain HTML, or the named dependency with its
reason) and what the default gives up; then the approval line, who
approved the set and when, and any category the user changed.

## Gate checks
One row per category of the eight: the tool and its exact version (or
what already in the project holds it), the command, the limits as
numbers, how the baseline is held (the tool's own file, or a count in
`gate-checks.json`); or `not picked` and why. Approved with the set
above.

## Considered and rejected
Per category, the options declined and the concrete reason.

## Deliberately not decided yet
Categories no chunk of this slice forces, and who owns each when it does.

## Consults
Any `devsecops-engineer` question asked and the answer recorded.
```

Keep it short. If the honest output is four choices and a list of things
left open, that's the correct output — a bootstrap document longer than
the design it serves is a sign the demand test wasn't applied.

**Where the output goes is given, not chosen.** If `orchestrator` invoked
this skill, it named the target directory: save there. Invoked directly,
use the location the user gave or that the conversation plainly implies;
if nothing says, ask before writing anything. Never search the project
for a place to put it.

## Re-entering this skill

This runs once per project and then stays additive. Three things bring it
back, and only these:

- **A later slice forces a category that was left open** — the first
  slice that needs data to survive a restart, the first one that
  authenticates: run it again for *that category only* and append, and
  extend the default set the same way, once, for that slice's chunks.
- **A chunk forces a dependency the set excluded**: the one mid-build
  re-entry, for that category only, appended with the chunk that forced
  it and why the built-in could not do the job.

- **The document has no `## Gate checks` section** (it was written before
  the gate took the eight categories): the orchestrator's A step sends
  the flow back here for that section only.

A chunk that stays inside the set is not a re-entry. Never reopen a
settled choice unless the user asks; a bootstrap decision that keeps
getting revisited isn't a bootstrap, it's an unresolved argument.
