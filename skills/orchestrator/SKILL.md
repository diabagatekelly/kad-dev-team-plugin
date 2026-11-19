---
name: orchestrator
description: Route a problem to whichever kad-dev-team persona/skill applies next, by inspecting what already exists (problem doc, scope map, requirements, slices) rather than the user having to name the right persona each time. Use when the user wants to move a problem forward and hasn't said which persona/skill to use, or says "what's next" / "keep going" on a problem already in progress — including when they guess at the next stage in passing or conditionally ("if the next step is the implementation, go ahead", "probably the security pass next"). A stage guessed at is not a skill named, and the implementation stage in particular reaches tdd-implementation-lite only through this skill's sandbox check and chunk loop (a design-readiness gate first, one chunk runner per chunk carrying one implementer, a gate, one combined reviewer and one smoke run per commit and one fix round per scope, a Definition of Done, a slice review and the criteria walked in a real browser at the end, then delivery), never by invoking it directly. Before any planning document is read it asks the tracker what is open (a pull request from a slice branch, a Critical or High issue) and routes that first.
---

# Orchestrator

**This is a skill the main agent loads, not a persona to spawn.** Every
persona in this roster that plans work (`docs-writer`, `product-manager`,
`product-slicer`, `software-architect`, `devsecops-engineer`) blocks on
`AskUserQuestion` and must run inline — never as an async `Agent` spawn. Orchestrating them means *you* invoke each routed skill in turn, in this
same conversation, the same way you would if the user had asked for it
directly. `accessibility-engineer` is
`background: true` and *could* be launched async outside this skill, but
this skill still runs it inline like every other row,
since routing here is sequential by design, not because every persona it
invokes requires it. **The one exception is the `tdd-coach:tdd-implementation-lite`
row** — see "The chunk loop" below — which genuinely launches real async
`Agent` calls, the only place in this skill that does.

**Skip this skill** when the user already named what they want directly
("write an ADR for X," "audit the docs for staleness") — routing only
earns its keep when the user hasn't said which persona/skill applies and
you'd otherwise have to guess or ask them to pick. A stage the user
guesses at while asking to move forward ("if the next step is the
implementation, go ahead") is not that: they named what they expect, not
a skill, and the routing table decides. This matters most for
implementation, which `tdd-implementation-lite` invoked directly would
do inline in the real tree with no sandbox check, no chunking, no gate
and no reviewers.

**Stay inside your lane while inspecting.** Every read you do — in step 2,
and while running the routed skill in step 4 — is confined to (a) what
that skill itself directs you to read, and (b) the resolved target
directory. Never read anywhere else in the project "for context" —
not this plugin's own `evals/`, not other skills' fixtures, not unrelated
directories. If this is being dogfooded inside the plugin's own repo,
those directories look like real project content but aren't; outside that
repo, they won't even exist. Either way, wandering into them isn't this
skill's job.

## Procedure

**When your context has been summarised** (the conversation opens with a
summary of its earlier part, or a step's wording is something you
remember and cannot see), invoke this skill again by name with the
`Skill` tool before the next step, and read the step from what it
returns. Never open a skill's file by its path with `Read` or the shell
to recover its wording: the path is the plugin's install, outside the
project, and the owner is asked to allow a read they cannot place
(incident 45). The log's last entry and its bullets say where the flow
is; the skill, invoked again, says what the step is.

**0. Session setup.** Once per session, before the target question and
before anything is read. The launcher `bin/kad` is the one way a flow
runs: it starts Claude Code inside the sandbox runtime (the whole session
fenced: file tools, hooks, every agent) with audit mode on (each prompt,
skill and agent call logged and the transcripts kept, on the owner's
machine, synced to the audit repository at the end of each slice), the
GitHub token, Claude in Chrome and the permission set the owner approved
once for the project. A session started as plain `claude` has none of
that, and nothing inside it can turn any of it on, so nothing in this
step asks, prepares, restarts or relaunches a session (0.13.1's relaunch
opened a terminal window that carried this session's variables and lost
two runs' transcripts; gone since 0.14.0). Inline with Bash, one command:

```
echo "session: runtime $([ "${SANDBOX_RUNTIME:-}" = 1 ] && echo yes || echo no); launcher $([ -n "${KAD_SRT_SETTINGS:-}" ] && echo yes || echo no); audit ${KAD_AUDIT:-off}; chrome ${KAD_CHROME:-off}"
```

`runtime yes` is `SANDBOX_RUNTIME=1`, set by the runtime itself for every
process it fences, the same test `sandbox_check.py` makes; `launcher yes`
is `KAD_SRT_SETTINGS`, which only `bin/kad` exports.

- **Runtime yes**: the fence is there. Under the launcher (`launcher
  yes`) everything else was decided when it started; fenced by something
  else (`srt claude` by hand, or a harness that fences its runs) audit
  mode is whatever the environment says and nothing here can change it.
  Say so in one line and go to step 1. Nothing is asked.
- **Runtime no**: this session cannot run the flow, and nothing it can do
  makes it able to. Say so in one line that carries the one command to
  type, then stop: no target question, no routing, no question, no
  handoff file, no new window. The command is `kad` from the project's
  root when the owner has it on PATH, else the launcher by its full path,
  `"${CLAUDE_SKILL_DIR}/../../bin/kad" --project <project root>`, with
  the path resolved (print the real path, never a placeholder). The first
  run on a project shows the permission set and asks one yes; every later
  run starts on one line. On native Windows the same command, from WSL2.
- **No Bash in this session**: nothing of this step can run. Say so in
  one line and go to step 1; the chunk loop's own check (A.1) still runs
  when the flow gets there and stops a flow whose session is not fenced.
- **Resumed**: a session that picks up a flow from a handoff file (the
  owner's message names one, or the chunk loop's resume rule finds one)
  follows the same bullets: `runtime yes`, one line and on; `runtime no`,
  the one line with the command and stop, the handoff file left where it
  is for the fenced session to resume.

The outcome is reported in step 5's text as one `session` line (`under
the launcher`, `fenced without the launcher, audit <on | off>`, or `not
fenced: stopped`); it is not a log entry, since no target exists yet when
it is made.

**1. Identify the target.** You're invoked with the artifacts directory as
a parameter, or not:
- **Given one** — that's the target. Skip straight to step 2. Don't
  second-guess it, don't search for a different one.
- **Not given one, and the project says where** — when the project's own
  memory (what this session was started with) or the `CLAUDE.md` at its
  root names the directory its planning artifacts live in, that directory
  is the target: take it and go to step 1b. Nothing is asked. **Say so
  before the next tool call**, in one line of text that names the
  directory and where it is written ("target: `planning/`, as the
  project's `CLAUDE.md` names it"), and again as the first line of step
  5's report: a target taken silently looks to the owner like a guess.
  The first log entry written carries it too, as one indented bullet,
  `target: <dir> (named by <where>)`. One read of the root's
  `CLAUDE.md` is the whole of the looking: no search, no listing of
  directories, no guess from a folder's name. Two directories named, or a
  sentence that could mean either of two, is not the project saying
  where: ask. An owner once typed a folder their project's memory already
  named, after being offered two guesses that did not exist.
- **Not given one** — ask once, before doing anything else: "Where do this
  problem's artifacts already exist, or where should they be created if
  we're starting from scratch?" Whatever the user answers becomes the
  target for every persona this skill invokes on this problem, this
  session and any future one — record it nowhere except by virtue of the
  first artifact actually landing there. Never guess a location yourself
  and never search the project for one instead of asking — if it wasn't
  handed to you, ask.

**1b. Open work first.** Before any planning document is read, inline
with Bash, one read of the repository decides whether there is a tracker
to ask: `git remote get-url origin` from the target. When the session
has Bash and that URL is on `github.com`, two questions to GitHub, with
`gh`:

```
gh pr list --state open --limit 500 --json number,headRefName,url
gh issue list --state open --limit 500 --json number,title,labels,body
```

A `gh` call that fails there (not installed, not signed in, no network)
stops the routing with the command's error on the line, as one log entry
(`**Routed to:** none (tracker unreachable)`, `**Artifact:** this log`)
and a report in step 5; the flow never proceeds as if nothing were open.
When there is nothing to ask (no Bash in the session, no repository, no
`origin`, or an `origin` that is not on `github.com`: a local path, a
bare repository, another host) the step is one indented bullet under the
next entry written (`tracker: no shell`, `tracker: no repository`,
`tracker: not GitHub (<url>)`) and the routing goes on: no question, no
stop, no planning document opened to find out. Another tracker's
equivalent of these two calls waits for a project that records one.
Then:

- **An open pull request from a slice branch** (`headRefName` matching
  `slice-<nnn>-*`): that slice is not closed, so nothing newer starts.
  Write the entry (`**Routed to:** \`code-reviewer:external-review-triage\`
  (chunk loop E.4, PR #<n>)`, `**Artifact:**` the triage report's path in
  the records directory) and run the chunk loop's E.4 on it: `delivery`
  collects every unresolved review thread and issue comment on the pull
  request, whoever wrote it (an external reviewer, a bot, the owner, the
  owner writing from the same GitHub account the session pushes as); the
  only comments skipped are the ones this flow posted itself, recognised
  by the plugin's footer line in their body (`delivery` writes it on
  everything it posts and filters by that marker, never by author); then
  the triage, the fixes under the loop's fix-round rules (one fixer plus
  one regressions round per round of comments, the gate before each),
  `delivery` to push, reply and file, until a round has nothing to fix or
  round 5 is done; then report that the pull request is clean. **Its
  checks come first**: a pull request whose checks are red or have no
  result gets `delivery`'s "CI watch" before any comment is triaged (the
  chunk loop's E.4 says how a red check is fixed), and is never reported
  as clean or ready while one is. A pull
  request whose comments are all resolved and whose checks are green is
  reported as `ready to merge` in one line, and the flow waits for the
  merge before any slice work: merging is the owner's. Two open slice
  pull requests are reported together and the lower-numbered slice is
  taken first.
- **An open pull request from a planning branch** (`headRefName`
  matching `planning-<nnn>-*`): that slice's plan is waiting for the
  owner, so its build does not start and nothing newer is planned. Its
  checks first, as above. A comment on it that this flow did not post is
  the owner's correction to the plan: a backward route to the owner of
  the document it names (step 3's rule), revised in place on the
  planning branch and committed by name; then `delivery` pushes it ("A
  planning pull request"). With nothing to answer, write the entry
  (`**Routed to:** none (planning pull request #<n> open)`,
  `**Artifact:** this log`), report `planning pull request #<n> is open:
  the build of slice <nnn> starts once it is merged`, and stop: merging
  is the owner's.
- **Open issues at Critical or High**: `delivery` files every issue with
  a `severity:<level>` label as well as the title prefix, so read the
  label first, the title prefix (`[High]`, `High:`) second, and a
  `**Severity:**` line quoted in the body third, so issues filed before
  the label existed are still found. Each such issue is one
  `AskUserQuestion` with three answers: **fix it in the open slice's fix
  round** (it joins the triage round above as a fix), **fix it first on
  its own branch** (a backward route to the chunk loop for that issue
  alone, before any slice), or **accept it as known and recorded** (the
  owner's words go on the issue as a comment with the footer line, and
  the issue stays open with a `known` label). A Critical is never
  "accept": its two answers are the first two. One question per issue,
  one issue per call, the log entry written before each.

Only then does the planning-document inspection below run; both checks
are entries in the log like any route, and a GitHub project with nothing
open gets one indented bullet under its next entry: `tracker: nothing
open`.
Why: on 2026-11-08 PR #20 of the project this plugin is measured on sat
open with eighteen findings as comments while the next slice would have
been cut on a branch behind it, and a High open since 2026-11-02 had never
been routed by any stage.

**2. Inspect what already exists in the target directory** — cheap,
mechanical checks only, never a semantic read of full artifact prose:
- A problem framing doc (a file whose top heading is `# Problem: ...`)?
- Any `scope-map-*.md` files? If more than one, the current one is the
  highest-numbered file whose `## Status` says `Active` (not `Superseded
  by ...`).
- Any `requirements-*.md` files? Same Active/Superseded rule. Which unit
  (scope-map step, or "the problem" if there's no scope map) does the
  current one belong to?
- **Project-level:** does the current unit's Active requirements doc have
  an `## Outside systems and lasting things` section that names anything
  (not `none`)? If so, is there a `domain-model.md` in the target
  directory with a `## ` table heading for each thing named? A
  requirements doc with no such section (one written before the section
  existed) asks for no model.
- Any slice files? For each, does its title name a source scope-map step
  (e.g. "scope-map-001 step 2")? A slice with no such reference was cut
  directly from the problem doc. Has it been written up as a user story
  yet (a matching user-story artifact, if this project tracks those
  locally — otherwise take the user's word for whether filing happened)?
  Has it been designed yet (a matching design-doc artifact from
  `architecture-design`, if this project tracks those locally — otherwise
  take the user's word)? Does it still carry unfilled placeholder
  acceptance criteria naming `devsecops-engineer` (or, in artifacts written
  before this persona existed, `security-engineer` / `reliability-engineer`)?
  Is it UI-touching — does its thin path describe a screen or view a
  person looks at and acts on? Take this as stated by the slice's own
  text; a genuinely ambiguous case is worth asking about, not guessing.
  If UI-touching, does it have a screen-design artifact yet (a matching
  artifact from `screen-design`, if this project tracks those locally —
  otherwise take the user's word)? Check both the target directory itself
  and a `visual-ux/` subfolder inside it — `ux-designer` saves its written
  artifacts in either place depending on the run, and both are valid; don't
  conclude one doesn't exist just because the root came up empty. If it has
  one, does it still carry an unfilled accessibility-criteria placeholder
  (naming `accessibility-engineer`, or, in artifacts written before this
  persona existed, an explicit not-authored-here placeholder)? A slice
  whose thin path has no user-facing interface carries, by
  `vertical-slicing`'s rule, an accessibility line saying `not applicable,
  this slice has no screen`: read that as filled, route no review, and
  treat the slice as not UI-touching for every row below. The line is
  required, not optional: a slice that is not UI-touching and carries a
  plain accessibility placeholder, or no accessibility line at all, has
  no status and goes back to `product-slicer` to say which it is (the
  table's row for it). And the not-applicable line on a slice whose thin
  path does describe an interface a person perceives and acts on (a
  screen, a voice flow, a document, a notification) is a slicer mistake:
  the same backward route, not a review you run around it.
- **Project-level, not per-unit:** is there a technology-bootstrap artifact
  in the target directory? If not, take the user's word for whether this
  project already has a working stack — a repo someone has been building in
  for months has obviously settled this without an artifact, and asking it
  to produce one retroactively is busywork. Only a repo with no stack yet
  routes to this row.
- **Project-level, not per-unit:** is there a design-system artifact in the
  target directory, or inside a `visual-ux/` subfolder of it — check both,
  same as the screen-design check above? Only relevant once some unit is
  actually UI-touching — a problem where nothing has needed a screen yet
  never routes to this row, the same way a problem with no stack decision
  forced yet never routes to the technology-bootstrap row below.
- **Only when step 1b found a GitHub tracker:** is the slice's plan on
  the default branch? Inline with Bash, `git fetch origin` (a fetch that
  fails is said in one line, and the repository's own `origin/<default
  branch>` is compared as it stands), then `git status --porcelain --
  '<slice file>' '<design document>'` is empty and `git diff --quiet
  'origin/<default branch>' -- '<slice file>' '<design document>'` exits
  0: merged. Anything else: not merged. Never asked of a project with no
  tracker, of an issue fix, or of a slice whose build has already
  started (a `slice-<nnn>-*` branch exists, or the log holds its
  chunk-loop entry): those were planned before this rule or are past it.
- Has the current unit's slice actually been implemented — real,
  working code, not just design/criteria artifacts? There's no fixed
  convention for detecting this mechanically (it's application source, not
  a markdown artifact this plugin names) — take the user's word for it,
  the same way you already do for an established project's stack.

**3. Route by what's missing**, in this order. Each row assumes everything
above it in the table is already satisfied for the current unit of work
(a scope-map step, or the whole problem if no scope map applies).

**Backward routing takes precedence over the whole table.** Before matching
any row, check whether a later artifact has invalidated an earlier one.
Signals, all cheap to spot: a section headed "handed back," "blocking," or
similar naming another persona; an artifact stating it contradicts or
supersedes something upstream; an artifact whose own text says a stage was
skipped for it. They sit at the **end** of the document that found the
problem (a filled security or reliability document whose last section is
the hand-back looks complete from its first screen), so read every
planning document to its last line before matching a row; the table is
consulted only once that scan has come up empty. A hand-back found after
a forward step was already taken is a forward step that should not have
happened, not a correction to narrate.

When you find one, **route to the persona that owns the invalidated
artifact — not the one that found the problem.** A security pass that
discovers a slice needs a capability nobody scoped has found a
`product-slicer` problem; a slice created without a requirements pass is a
`product-manager` problem. The finder reports; the owner decides. Letting
the finder resolve it in place is how a scope decision gets made by a
persona that doesn't own scope, and how a stage gets skipped without anyone
choosing to skip it.

Three rules for the backward step. **The owner revises its document in
place while the document is still its own, and supersedes it once a later
stage has built on it**: `scope-map`, `requirements-refinement` and `adr`
each state this rule and number sequentially for the superseding case; a
slice file is revised in place, never copied to a `-v2`; the entry names
which of the two it was. **A backward route is one routed step.** When the
owner's revision invalidates the next artifact down (a slice cut from the
old requirements, a story written from the old slice), that is the next
backward route, with its own entry and its own `Skill` call, never a
"follow-on" edit under this one. **Once a backward step completes, return
to step 2 and re-inspect from scratch, without asking**: a revised scope
map can move the forward position by more than one row.

That "return to step 2" instruction governs your own next invocation once
the backward step actually completes — it is not something to narrate now.
When reporting a backward route (step 5), state the single routed
destination, why it was routed there and what the owner produced; don't
add what re-inspection will find or where the forward position might land
once it resolves. Describing that round trip is the same chaining step 5
forbids, just spelled backward instead of forward.

| Detected state | Route to |
|---|---|
| No problem framing doc | `docs-writer:problem-framing-doc` |
| Problem doc exists; no scope map, no requirements doc, no slice anywhere yet | `docs-writer`, to decide — per `scope-map`'s own trigger criteria, by reading the problem doc — whether this needs a scope map or is small enough to treat as one unit. This is the persona's judgment call from the problem doc's own content, not an orchestrator-level question; it may still ask the user if genuinely torn, just not by default. |
| A unit is identified (the lowest-numbered Active scope-map step with no requirements doc yet, or — if no scope map exists — the problem itself) and has no requirements-refinement doc | `product-manager:requirements-refinement` for that unit |
| The current unit's requirements doc names outside systems or lasting things, and `domain-model.md` is missing or has no table for one of them | `software-architect:domain-model` |
| The current unit has a requirements-refinement doc but no slice yet | `product-slicer` (`vertical-slicing` + `acceptance-criteria`), using the requirements doc as the primary input for WHAT to slice — not re-deciding it |
| A slice exists for the current unit but hasn't been written up as a user story yet | `docs-writer:user-story-writeup` |
| The current unit's slice has been written up as a user story but has no design doc yet | `software-architect:architecture-design` for that slice |
| The slice has a design doc but its security criteria are still an unfilled placeholder | `devsecops-engineer:security-requirements` for that slice |
| The slice's security criteria are filled but its reliability criteria are still an unfilled placeholder | `devsecops-engineer:reliability-requirements` for that slice |
| The slice's accessibility line disagrees with its thin path: a not-applicable line on a slice with a user-facing interface, or a plain placeholder or no line on a slice with none | `product-slicer` (`vertical-slicing`) to fix the line in place: a backward route, before any review of the slice |
| The slice is UI-touching, its runtime-safety criteria are filled, and the project has no design-system artifact yet | `ux-designer:design-system` |
| The slice is UI-touching, its runtime-safety criteria are filled, a design-system exists, but this slice has no screen-design artifact yet | `ux-designer:screen-design` for that slice |
| The slice is UI-touching, has a screen-design artifact, but its accessibility criteria are still an unfilled placeholder | `accessibility-engineer:accessibility-review` for that slice |
| The slice is designed with its runtime-safety criteria filled (and, if UI-touching, its screen designed and its accessibility criteria filled), and the project has no stack yet | `software-architect:technology-bootstrap` for that slice |
| The slice has a design doc, its runtime-safety criteria are filled (and, if UI-touching, its screen designed and its accessibility criteria filled), the project has a stack, step 1b found a GitHub tracker, and the slice's plan is not on the default branch | `release-engineer:delivery` for a planning pull request, after the readiness gate: "The planning pull request row" in step 4. Then stop. |
| The slice has a design doc, its runtime-safety criteria are filled (and, if UI-touching, its screen designed and its accessibility criteria filled), the project has a stack, its plan is on the default branch when there is a tracker, but the slice hasn't been implemented yet | `tdd-coach:tdd-implementation-lite` for that slice |
| The slice has been implemented — `tdd-coach:tdd-implementation-lite` has produced working, tested code for it | **Stop — see step 5.** Don't advance to the next scope-map step. |

**Why the requirements rows come *after* design, not before.** These are
the only non-functional criteria in the spine that depend on structural
decisions: what data a slice actually handles is determined by how it's
built. A design that puts a third-party vendor between the system and a
credential means the credential never enters at all — which is a completely
different set of security criteria than the same slice built to hold that
credential itself. Running these before the design decision would produce
criteria for a system nobody is building.

**Why screen design comes after security and reliability, not before.**
Those two rows are exactly the ones most likely to surface a backward
route — a slice discovers it needs a capability nobody scoped, and the fix
can change the slice's shape entirely. Designing a screen for a slice whose
scope might still move is wasted work at best and a screen built for the
wrong slice at worst. Placing screen design after both runtime-safety rows
means it only ever runs against a slice that's already survived its most
likely sources of change.

**Why accessibility review comes right after screen design, not before.**
There's nothing to check before a screen has actually been rendered —
`accessibility-review` verifies an artifact `screen-design` produced, the
same dependency `screen-design` itself has on `design-system`. Running it
before the stack is chosen also keeps its findings technology-agnostic: a
missing label or a failing contrast pair is a property of the rendered
markup and tokens the mockup already committed to, not of whatever
framework eventually renders it for real — the same reason runtime-safety
criteria get written before a stack exists rather than after.

**Why the bootstrap row comes last, not first.** An empty repo makes
"choose the stack" feel like step one, but a structural design needs no
technology to exist — it names boundaries and what crosses them — and
runtime-safety criteria are deliberately technology-agnostic ("bank
credentials never enter the system" holds regardless of what's storing
anything). The one thing that genuinely can't proceed without a stack is
writing the first failing test, which is `tdd-coach:tdd-implementation-lite`'s
job, the next stage after this row. Putting it here means the choices get
made against a slice that's fully
specified, and only the ones that slice actually forces get made at all.
This is also why screen design, when it applies, runs before bootstrap
rather than after: `technology-bootstrap`'s own "sometimes forced"
UI-framework decision depends on whether the first failing test actually
drives a screen, which is only knowable once that screen has been
designed.

Never invent a stage this table doesn't cover. ADRs, `staleness-audit`,
`tdd-coach:test-quality-review`, `code-reviewer`, and all four of
`devsecops-engineer`'s review/posture skills (`security-review`,
`reliability-review`, `supply-chain-review`, `operational-readiness`) are
event-triggered, not part of this forward spine — they run against code, a
test file, or a repo that already exists, which most of this spine hasn't
reached. Hand off to them only if the user asks. `code-reviewer` (applying
`code-review`, `test-quality-review` and, by territory, `reliability-review`
in one launch) also runs as the chunk loop's per-chunk reviewer, and all
six review skills run once on the whole slice at its D step, inside
`tdd-implementation-lite`'s own row — that's not a spine stage either, it's
part of how that one row does its job.

**`architecture-cartographer:map-query` is another inline advisor consult,
not a spine stage — it doesn't get its own row here either.**
`software-architect:architecture-design` consults it before writing a
design doc, at the structural level ("does a comparable module or
interface already exist"), the same inline, hand-control-straight-back
pattern that row already uses for its `devsecops-engineer` consult.
`tdd-coach:tdd-implementation-lite` consults it again before writing each Test
List entry's code, at the implementation level ("does a comparable
function or helper already exist") — below `architecture-design`'s own
conceptual altitude, squarely inside what that row actually writes. Both
consults are instructed in the asking skill's own `SKILL.md`, not
something this file dispatches; nothing about routing changes because of
them. `architecture-cartographer:map-update` has its own wiring inside the
chunk loop below — see "The chunk loop."

**4. Execute exactly one routed step.** For every row except
`tdd-coach:tdd-implementation-lite`, execute inline: invoke the skill the
trigger matched with the `Skill` tool (`kad-dev-team:<skill>`), passing the
target directory. Don't go looking for the persona's `AGENT.md`: it sits
outside the project, a read of it may be refused, and everything a routed
step needs from its persona is in that skill. Follow the skill directly —
this is live use, not a dry run: if it would ask the user something,
actually ask via `AskUserQuestion`, **unless the question is one the
owner has said not to be asked**:

**A design or technical question that has a recommended option is taken,
not asked** (the owner, 2026-11-17: asked thirteen questions in a day,
they took the recommended option on every one of this kind, incident
42). When a routed skill's procedure reaches a question, sort it before
anything is put to the owner:

- **What the owner wants** (a requirement, the scope, what the product
  does for them, the content of a criterion only they can know): asked,
  as the skill says.
- **A risk or a permission** (an advisory accepted, a check weakened or
  exempted, where their own data lives or what may read it, money spent,
  anything `autopilot.md` lists as always asked): asked.
- **How it is built** (where a value is kept, which mechanism of a
  provider, which tool or setting, which states get a capture, which
  file a formatter ignores) **when the skill recommends one option**:
  not asked. Take the recommended option; the skill's document records
  it as decided, with each alternative and why it was not taken, the way
  it would have after the owner's answer; and one indented bullet goes
  under the entry: `taken as recommended: <the choice>, over
  <the alternatives> (<skill>)`. The step's report lists what was taken
  this way in one line each, so the owner can overturn one by saying so:
  an overturn is a backward route to that skill, which revises its
  document in place.
- A how-it-is-built question the skill cannot recommend on (the
  documents give no ground to prefer one option) is asked.

This sorts your own questions too (the chunk loop's A step keeps its
three, which are permissions), and it is said in the arguments to every
routed skill, below.

**The arguments you pass say two things and nothing else about
mechanics**: where to save (the location resolved in step 1, so the skill
neither asks where nor invents a different location) and that any
question the skill's own procedure puts to the user goes through
`AskUserQuestion`, one question per call, except a design or technical
question with a recommended option, which is taken as recommended and
recorded in the document as decided (the rule above). The second is
said to every routed skill, including one that rarely asks. Say nothing about other
stages' documents: never "then point the slice's placeholder at it",
never "and sync the story", never which file another persona should
update afterwards. What a skill may touch is in its own text, and a
document it doesn't own is re-synced by that document's owner on the
next re-inspection. Pass the skill's inputs by path and the question it
is being asked (which check failed, which document to revise in place)
when a backward route names one; pass no answer the owner hasn't given.

Produce the real artifact and save it there, using that persona's own
filename/heading convention — once the skill's own procedure gets there.
Routing doesn't hurry it: a skill whose first response is questions asks
them and stops, even here, and the artifact comes in a later turn. Don't
fill the skill's questions with answers inferred from the repository to
reach the artifact sooner. Re-invoking a skill whose text is already in
context (a redo after a backward route, a stage resumed after a
correction) still goes through the `Skill` tool: the call is what the log
check and a reviewer look for, and a stage run from memory is a stage
that ran unlogged.

**The planning pull request row** puts the finished plan to the owner
before any build money is spent (the owner, 2026-11-18: the loop waits
for the merge). Inline, in this order:

1. `git switch -c planning-<nnn>-<slug>` from the current commit (the
   number from the slice file's name, the slug from its title), and
   commit every modified or untracked file of the target directory, by
   name, as `Planning: slice <nnn>`. Nothing outside the target
   directory goes in.
2. The design-readiness gate, exactly as the chunk loop's A.4 says, its
   backward routes and its two owner questions included; each revision
   is committed on this branch by name.
3. On `readiness: PASS`, write the entry, then invoke
   `kad-dev-team:delivery` with the `Skill` tool for "A planning pull
   request", handing it the branch, the default branch, the target
   directory, the slice file and this slice's `taken as recommended`
   bullets from the log. It pushes, opens the pull request and watches
   its checks.
4. Report the pull request, the slice's size line and what was taken as
   recommended, say that the build starts once it is merged, and stop.
   Nothing of the chunk loop runs on a plan that is not merged.

**The `tdd-coach:tdd-implementation-lite` row doesn't execute inline — it runs
the chunk loop below, every time, by default.** There is no separate "is
this slice worth it" judgment call here: no signal anywhere in this
roster's pipeline reliably predicts implementation risk, and inventing one
would be worse than having none. The cost is bounded by `product-slicer`
already keeping each unit at the smallest shippable slice and by the loop
building it one small commit at a time. If the user explicitly wants a
specific slice built without it, that's their call to make by saying so
directly; this skill doesn't offer a way to opt out on its own judgment.

**Append one entry to `orchestrator-log.md`, in the target directory,
every time this step runs — as soon as you've routed, before invoking the
routed skill.** A routed skill often stops partway to ask the user
something, so an entry left until the step finishes may never be written.
The same goes for any question you put to the user yourself about the
routed step, such as the sandbox question, or
whether something is already built: write the entry first, then ask. The entry records where the state table routed, not the user's
consent to proceed, and a reply of "not now" gets its own entry later.
This is the only
retrospective record that every stage actually ran rather than getting
silently skipped; a graded final artifact says nothing about the path
that produced it. Create the file if it doesn't exist yet. One entry per
invocation, appended, never reordered; a prior entry being wrong gets a
new entry noting the correction. The log is a process record, so it is
only ever added to, even on a project that revises its planning documents
in place. Each entry:

```markdown
## <sequence number>. <date> — <the detected-state row that matched>

**Routed to:** `<persona:skill, or "chunk loop" for that row>`
**Artifact:** <path the routed step will save to, or "see sub-entries below">
```

The **Artifact** line is in every entry and holds one path, never
omitted and never conditional. The entry is written before the routed
step runs, so the path is where that step's output will go: a file under
the target directory, named by the persona's own convention
(`problem-framing.md`, `scope-map-001.md`, `requirements-002.md`,
`slice-001.md`, a screen design under `visual-ux/`), with a parenthetical
where the skill may name it differently. Not the bare directory: that
says where without saying what. Three cases need saying:
- the implementation row: `see sub-entries below`, even when the loop has
  not started yet — a step that stops to ask has still routed, and a "not
  now" gets its own entry later;
- a routed skill that may decide nothing needs writing (`docs-writer`
  deciding whether a scope map is warranted): the path the artifact takes
  if it is written, stated flatly — not "`scope-map-001.md` if warranted,
  otherwise none". If the skill decides none is needed, it records that
  where its own procedure says, and an indented bullet under the entry
  says so;
- `user-story-writeup`, which asks where this project files stories: the
  path a locally filed story takes under the target directory, with a
  parenthetical that the skill may file it elsewhere. Where it then went
  is an indented bullet under the entry, never an edit of the Artifact
  line; "to be decided by the skill" names no path.

**An entry that records an owner direction or housekeeping rather than a
route** (a consolidation the owner asked for, a correction to the process,
a repository created at the owner's request) has `**Routed to:** none
(<reason>)` and `**Artifact:**` the one file changed, in backticks, or
`this log` when nothing but the log changed. What else changed goes in
indented bullets below, never on the Artifact line. **Never while a
chunk loop is open**: between the A line and the E line, an owner's
direction is an indented bullet under the loop's own entry (`- Owner
<date>, word for word: "<their words>"; taken as: <what changes>`), and
the loop's next bold line follows it in the same entry. A new entry
there splits the loop's A to E lines across entries, and the next
reader, and the log check, find a loop with no C lines (one loop's were
spread over four entries).

**What may be added to an entry after it is written, and what may not.**
An entry may gain indented plain bullets once its step runs (its outcome,
a correction, an owner direction, a resume), as the chunk-loop entry
does; the bullets are added, never rewritten. Its heading, its Routed to
line and its Artifact line are never edited, and no entry ever gets a
second bold step line. A prior entry whose route or artifact turned out
wrong gets a new entry noting the correction.

For a backward route (the step 3 rule that supersedes the table), log it
the same way, naming which artifact is revised, whether in place or by
superseding, and why, not just the forward destination.

### The chunk loop — the `tdd-coach:tdd-implementation-lite` row's own procedure

Five steps, A to E, replacing the normal single inline execution for this
one row only. Every other row in the table is unaffected. The planning is
checked for readiness before anything is built; one **chunk runner** per
chunk (an Opus agent, `kad-dev-team:chunk-runner`) carries that chunk's
whole round, one implementer building it as a commit on the slice branch,
a mechanical gate, one combined reviewer and one smoke run in a real
browser, one fix round and a regressions-only re-review, no more, and
hands back one line; the orchestrator keeps the records, the log and the
owner's questions; the whole slice is held to a Definition of Done, its
changed lines are mutated against the suite, it is reviewed once more at
the end and read cold by an agent with no planning document, and, when
it has a screen, its acceptance criteria are walked in a real browser; then the branch is pushed, a pull
request opened, the standing Mediums filed, and the external reviewer's
comments triaged. Nothing in it runs "until clean", nothing runs in the
background, and nothing is resumed by message to fix something: every
build and every fix is a fresh agent on a short context. The one measured
exception is the `light` cadence (P3.2 of `handoff-slice2.md`, one arm on
one slice), where D's fixes go back to the chunk's own builder by message.

**Every launch below passes `model` explicitly on the `Agent` call**:
`"sonnet"` for every implementer and fixer, `"opus"` for every reviewer,
smoke agent, criteria walk, consult, the triage and the chunk runner. An
agent definition's `model:` line is documentation; in practice the launch
parameter is what decides. Builders and fixers are launched with
`maxTurns: 120`; the Definition of Done fixer at D with `maxTurns: 160`;
the chunk runner with `maxTurns: 200`.

**Scripts.** Every script below lives in `${CLAUDE_SKILL_DIR}/scripts/`;
the chunk runner is handed that directory by absolute path (its own
`CLAUDE_SKILL_DIR` is another skill's), and so is every agent that starts
the app (`scratch_run.py`, the data rule below).

**The data rule** (P2.3; two smoke agents once started the app on the
owner's real data and login credential store, incident 10). Every agent that starts the
app (a smoke run, the criteria walk, the slice accessibility review, the
cold read) starts it through `scratch_run.py`, handed by absolute
path with a scratch folder outside the project
(`${TMPDIR:-/tmp}/kad-run-<slice>-<k>-<round>`): the app's data paths are
given explicitly inside that folder (`--env NAME=<relative path>` for each
variable the README or the design names), `HOME` is pointed there as
well, the script refuses to start when any resolved path is outside the
folder, made-up data (the fixture's or data the agent builds), the
project's fake credential tool or a disposable store, never the owner's
login credential store, not even for reading, no provider connection started,
and `scratch_run.py --clean <folder>` after. The agent never opens the
owner's data directory, so the before-and-after check of the real data
files is the launcher's step around the launch, not the agent's:
`scratch_run.py --hash '<data dir>'` before and after, the data directory
being the one the design or the README names (`data not named` when
neither does), and `data unchanged` or `data CHANGED` on the C or D line.
`CHANGED` stops the flow before the next step and is reported to the
owner in step 5.

**Every launch below names a file for the agent's report** and tells the
agent to hand back counts and the path, not the report. Records live in
the **records directory**, `<target>/implementation/` (the owner's
choice, 2026-10-25): the implementation report
`implementation-report-slice-<nnn>.md`, one report per launch
(`chunk-<k>-r<i>-review.md` and `chunk-<k>-r<i>-smoke.md` in C;
`slice-r<i>-<reviewer>.md` and `slice-r<i>-smoke.md` at D; `pr-r<i>-…` at
E), the gate outputs (`gate-chunk-<k>-r<i>.txt`, `gate-slice-r<i>.txt`),
the sidecar `rounds-slice-<nnn>.jsonl`, and the handoff file. The gate
allows that directory as a whole and protects every other document in the
target directory; the records are committed after each chunk as
`Records: slice <nnn> chunk <k>` and after D as `Records: slice <nnn>
review`. You open one of those files only to decide something; the fixer
reads them itself, and `rounds_record.py` (the runner's step 3) is the only thing that
parses one.

**Budget** (the A line records it; counted at every chunk boundary):
loop time 8 h for a UI-touching slice and 5 h otherwise (a UI slice
reached 5 h at chunk 7 of 8 and the owner lifted it, incident 11; decided
2026-11-06), 2 reviewer launches per chunk plus the last-fix review when
a regressions fix ran, 1 fixer per scope plus 1 for regressions (a
gate's own fixer is not counted), unless the owner's message named other
numbers. **Under autopilot the clock is the only cap** (the owner,
2026-11-16): the per-chunk counts are then no cap at all. They are
counted and written in the C line's `budget` field as always, a count
above its number ends nothing and asks nothing, and the budget check at
a chunk boundary reads the clock alone. The loop time still ends the
flow, with or without autopilot, since it is a number the owner
approved.
Consults are counted, never capped: the count goes on the E line
(0.13.1's cap of 8 per slice produced owner questions nobody wanted;
dropped 2026-11-08). At each chunk boundary read the clock and the
counts; when one is exceeded, the flow ends there: the branch stays as
it is, the C line says `budget exceeded: <which>`, and step 5 says what
is built. The dollar figure is not estimated during the run;
`cost_by_role.py` computes it at E.

**Autopilot.** A standing answer in `<target>/autopilot.md`, asked once
per project at A.2 like the delegation file. With it, at the stops
listed here and no others, the loop takes its own recommendation
without a question and, for the last two, writes an indented bullet
under the line it belongs to, `taken as recommended: <what>
(autopilot)`:

- a per-chunk count above its number (the budget paragraph above; the
  C line's `budget` field is its record, and it gets no bullet);
- **the autopilot round** for a Critical or High left standing when a
  scope's rounds are over (below), twice at most per scope;
- a readiness route that changes no decision (A.4).

**It always asks**, autopilot or not, when what it would do changes a
number or a decision the owner approved (the loop time, a criterion, a
design decision, a delegation), deletes, reverts or rewrites committed
work, pushes anything whose gate or checks are red, or touches scope or
requirements. A planning fork that carries a recommendation stays a
question: those are the owner's product decisions, and autopilot is
read by nothing outside the chunk loop. Without the file every stop
below is the owner's, as it was. Why: 41 of 47 questions that carried a
recommendation were answered with it, and three of one loop's seven
were the loop asking leave to keep its own bar.

**The last-fix review** (the owner, 2026-11-13: "any change should
always be reviewed"). Every commit that changes source or tests after a
scope's last review is read once, by one reviewer, on its diff, before
that scope is reported: in a chunk, the regressions fix and its gate
fixer's commit (the runner's step 5, on its line as `last <C/H/M>`);
at D, the last fix of the fix round; at E, once, every CI fix and
triage fix together. One launch per scope, never one per commit:
`kad-dev-team:code-reviewer:AGENT`, `model: "opus"`, `code-review`'s
"Combined chunk review" on the diff only (no cold pass), handed the
project root, the test command, the range `<the scope's last reviewed
commit>..HEAD`, the files it touched, the report path
(`chunk-<k>-last-review.md`, `slice-last-review.md`,
`pr-last-review.md`) and the last gate output, and nothing of any
earlier round. Recorded with `rounds_record.py … --round <i> --last
--project '<project root>' --range '<range>'`: nothing it raises is
handed to a fixer in the scope's own rounds, so its Critical, High and
Medium all stand (the script prints them), its Mediums are filed at E
like any standing Medium and its Lows go to the body. A range that
changes no source or test file (a records commit, the map, a README)
gets no review. A last fix nobody read held three bugs a later cold
read found.

**The autopilot round.** When a scope's rounds are over and a Critical
or High stands (the runner's line says so, D's fix round left one, or a
last-fix review raised one): without `autopilot.md` the flow stops for
the owner, as before. With it, at most **two** rounds per scope (the
owner, 2026-11-16), each in this order, every launch after a sandbox
check, and one `taken as recommended` bullet per round:

1. **Verify.** One `kad-dev-team:code-reviewer:AGENT`, `model: "opus"`,
   handed the standing Critical and High findings by report path and
   title, the project root, the test command and a report path
   (`<scope>-auto-r<i>-verify.md`, the scope being `chunk-<k>`, `slice`
   or `pr`), and told one thing: for each, run the code at `HEAD` and
   say whether the finding is still true. What it reproduces it writes
   as a finding in the shared format at the severity it finds; what it
   cannot reproduce it lists under `## Not reproduced`, one line each
   with what it ran. A last-fix review's own Critical or High was read
   on the diff minutes ago and is not verified again: it goes straight
   to step 2. Record the report (`--chunk <k | D | pr> --round <i>
   --last`).
2. **Fix.** Nothing confirmed and nothing from a last-fix review: the
   round ends here, `auto r<i> verify 0 confirmed, <n> not reproduced`,
   and the scope goes on (the unreproduced findings stay in the sidecar
   and are filed at E with that sentence). Otherwise one fresh fixer
   (`model: "sonnet"`, `maxTurns: 120`, `tdd-implementation-lite`, its
   handed-back path, chunks are committed) with the confirmed findings
   by report path, then the gate on its range (its own one fixer on a
   `FAIL`, as everywhere).
3. **Read the fix.** The last-fix review on that fix's range
   (`<scope>-auto-r<i>-last-review.md`), recorded with `--last`.

A Critical or High after round 1 gets round 2; one after round 2 stops
the flow for the owner at step 5, with both rounds' reports named. The
fragment on the C, D or E line: `auto r<i> verify <c> confirmed, <n>
not reproduced< fix <sha> → last <C/H/M>>`. The round never runs for a
`gate FAIL … ended`, a `stall: ended`, a hand-back that failed its hash
check, `data CHANGED` or the loop time: those end the flow as they did.
A stop once went to the owner over a Critical the last fix had already
removed, and the extra review they allowed found a real High.

**An issue fix** (the owner answered "fix it first on its own branch"
at step 1b, or asked for one issue to be fixed) is this same loop on the
slice the issue belongs to, after the backward routes that revised that
slice's documents for it, with four differences and no others:

- **The branch** is `slice-<nnn>-issue<n>-<slug>` (A.3; the slug from the
  issue's title), so step 1b still reads its pull request as a slice's.
- **The records carry the prefix `issue<n>-`**, in the slice's own
  records directory, wherever a name in this procedure says
  `slice-<nnn>` or begins a record: `implementation-report-issue<n>.md`,
  `issue<n>-chunk-<k>-r<i>-review.md` and `-smoke.md`,
  `gate-issue<n>-chunk-<k>-r<i>.txt`, `issue<n>-slice-r<i>-<reviewer>.md`,
  `gate-issue<n>-slice-r<i>.txt`, `issue<n>-pr-r<i>-…`,
  `rounds-issue<n>.jsonl`, `handoff-issue<n>.md`; the commits read
  `Planning: issue <n> ready for implementation`, `Plan: issue <n> in <k>
  chunks`, `Records: slice <nnn> issue<n> chunk <k>`. Nothing of the
  slice's own records is renamed, appended to or overwritten, and every
  launch is told the prefix with its report path, the chunk runner
  first (its records are the prefixed ones), and every script that takes
  a records file takes the fix's by path: `rounds_record.py --sidecar`,
  the gate's `--expect-tests-from`, `cost_by_role.py --sidecar` at E.
  The audit sync copies the records directory whole, so the fix's files
  travel with the slice's. The entry's heading
  reads `issue <n> ready for implementation`.
- **The fix base** is the commit the branch grows from, read at A.3
  before the planning commit (`git rev-parse --short HEAD`) and written
  on the A line as `fix base <sha>`. The readiness gate takes it
  (`--fix-base '<sha>'`, A.4) and judges what the fix revised: a gap the
  slice's documents already had at that commit is an older gap, printed
  as `INFO  older-gap:` and never a route.
- **Older gaps are filed once, as one issue.** When the gate's `older
  gaps: <n>` line is above zero: if `gh issue list` shows no open issue
  titled `Older planning gaps: slice <nnn>`, file one with that title
  (`delivery`'s issue form: the `tech-debt` label, the footer line), its
  body one checkbox per `older-gap` line as printed, and write `older
  gaps <n> → #<issue>` on the A line; an issue that exists is named
  there, never filed twice. No backward route, no persona and no
  question for any of them.

A fix once had no such rule: its records' names were improvised, and the
gate sent it back four times over documents it had not touched
(incident 35).

**A. Start.** In this order:

0. **Repository.** Inline with Bash: `git rev-parse --show-toplevel` from
   the target and `git remote get-url origin`. If the target is not
   inside a git repository, or the repository has no `origin`, write the
   A line as `flow not started: no repository` and route to
   `release-engineer:repo-bootstrap` as a backward route (its own entry),
   then stop at step 5. Nothing is asked first: a flow that cannot start
   should not cost the owner four answers. Never `git init`, `gh repo
   create` or push outside that skill.

   **The plan is merged first.** With a GitHub tracker and a slice that
   is not an issue fix, run step 2's check that the slice's plan is on
   the default branch. When it is not, write the A line as `flow not
   started: planning pull request not merged`, report which pull
   request is waiting (or that none is open and the planning row comes
   first), and stop at step 5: nothing is asked and nothing is built on
   a plan the owner has not merged, whoever asks for the build.
1. **Sandbox check**, inline with Bash:

   ```
   python3 -I "${CLAUDE_SKILL_DIR}/scripts/sandbox_check.py" --project '<project root>'
   ```

   The code-writing instances this flow launches, and the reviewers after
   them, run unattended with Bash in hand, and nothing in this plugin can
   fence them: the sandbox that keeps a command off the machine's keys and
   off the network is a setting of the session they run in, which a plugin
   cannot ship. The script probes the fence from inside it and reads the
   escape hatches from the settings; its last line is `sandbox check: PASS`
   or `FAIL`, one line per check above it, and its exit code says which
   kind of failure: `1` for a failure a settings file can fix, `2` when
   the platform has no sandbox at all (native Windows today; the
   `platform` line names what each platform has).
   - **Under the launcher** (`KAD_SRT_SETTINGS` set; the `platform` line
     says "under the sandbox runtime"): the settings are the launcher's,
     written outside the fence from the set the owner approved, and
     nothing inside the session can change them. `PASS` goes on the A
     line's sandbox field. A `FAIL` is a launcher or environment problem,
     never a question: report the failing lines as printed, write the A
     line as `FAIL: <checks>; flow not started`, and stop; the owner fixes
     the cause outside the session. An `env` line naming a variable the
     launcher kept on purpose (`GH_TOKEN` for delivery) is information,
     not a failure. No settings, sandbox or transcript question exists
     under the launcher. The check still runs and is logged before every
     launch (below).
   - **Fenced without the launcher** (the `platform` line says "under the
     sandbox runtime", no `KAD_SRT_SETTINGS`: `srt claude` by hand, or a
     harness that fences its runs): the runtime's own file fences the
     session and nothing inside can write it. On `PASS`, go on. On `FAIL`,
     report the lines as printed; when the owner's message already said to
     continue unsandboxed, the A line says `none on <platform>; owner
     opted to continue unsandboxed` and every later check in this flow is
     logged as information; otherwise write the A line with the failing
     checks and `flow not started`, and stop. `--write-settings` is never
     offered: the file lives outside the session.
   - **Not under the sandbox runtime** (the `platform` line without "under
     the sandbox runtime"): step 0 stops such a session before any flow
     starts, so reaching this means step 0 could not run (no Bash then).
     Write the A line as `FAIL: not fenced; flow not started` with step
     0's one command in the report, and stop. Nothing is asked and no
     settings are written: 0.13.1's per-command sandbox, its
     `--write-settings` offer and the "continue unsandboxed" choice on a
     platform that has a sandbox are gone since 0.14.0; the fence is the
     launcher's.
   - `env` or `worktreeinclude`: name the variables or files; unsetting
     the one and removing the pattern are the owner's. Stop.

   **Browser**, only when the slice touches UI (step 2's reading of the
   slice file), inline, after the sandbox check: with `KAD_CHROME=1` in
   the environment (the launcher's default since 0.14.0), ask the Chrome
   tools once, here, for the connected browsers
   (`list_connected_browsers`). A browser that answers puts `PASS
   (<platform>; Chrome)` on the A line's sandbox field. None answering, or
   no `KAD_CHROME`, is an error with the fix on the line, in the report:
   the browser is not open; the Claude in Chrome extension is not
   installed or not connected (`/chrome` in a plain `claude` session
   reconnects it); or the launcher ran with `--no-chrome`. Then the
   **browser question**, with `AskUserQuestion`: **restart with Chrome**
   (the owner opens the browser with the extension and runs `kad` again
   from the project root; write the A line as `sandbox — no browser; flow
   not started` and stop: nothing below has run, nothing to hand off), or
   **continue with every screen check owed** (the A line says `PASS
   (<platform>; no Chrome, screen checks owed)`, and every UI smoke run
   raises its one owed finding (the runner's step 3), so what was not checked is on the
   record). Skip the question when the owner's message already chose. On
   a slice with no screen the field says `PASS (<platform>; browser not
   needed)`, no Chrome tool is called, and `--no-chrome` costs nothing.
   One run learned at its first UI smoke run that no browser had ever
   answered while its smoke reports said `PASS`; the next ran with no
   browser because the field said `no Chrome` and the flow was allowed to
   go on (incident 12).

   **Cadence**, never a question: `light` when the owner's message for
   this slice names it (the word `light`, or "no per-chunk review"), else
   `loop`. It goes on the A line as `cadence — <loop | light>` and the
   chunk runner is told it. `light` is one measured arm on one slice
   (handoff-slice2 P3.2, H6's fourth question; the owner, 2026-11-17: the
   next slice runs it, with no per-chunk smoke run): per chunk the build
   and the gate only, no reviewer, no smoke run and no fix round; at D
   the six reviewers, the criteria walk (the one place the browser is
   driven) and the cold read once; fixes by the chunk's own builder
   resumed by message, an Opus fixer for what it cannot clear. The
   review of that slice says whether `light` becomes the default; until
   then `loop` is, and `light` is the owner's word in the message.

   **Audit and session**, inline with Bash, after the sandbox check and
   whatever it asked:

   ```
   python3 -I "${CLAUDE_SKILL_DIR}/scripts/audit_sync.py" --check --project '<project root>'; echo "session $CLAUDE_CODE_SESSION_ID"; bash "${CLAUDE_PLUGIN_ROOT}/hooks/audit.sh" --snapshot
   ```

   Its one line goes on the A line's `audit` field as printed: `audit:
   not configured` (no audit repository), `audit clone: <dir>`, or `audit
   clone FAILED: <why>` (git's own message as the SessionStart hook
   recorded it, or a clone that points at another repository than the
   configured one). A failed clone is reported to the owner in step 5 and
   stops nothing: the loop runs, every sync line says `FAILED` until a
   clone exists (the launcher makes one before the fence starts; a plain
   session's hook makes one at `$KAD_AUDIT_DIR/repo/`), and the material
   stays in the records directory meanwhile. With `KAD_AUDIT` unset the
   field says `off` and no sync or snapshot runs in this flow. The session
   id goes on the A line's `session` field: a resumed flow adds the new
   id on its `Resumed` bullet, so the E step's cost covers every session.

   The snapshot's line is the proof that this session's transcript is
   being written, taken here and not discovered at E: `snapshot: …` puts
   `transcript — kept` on the A line, `snapshot FAILED: …` puts
   `transcript — MISSING: <why, as printed>`, and with audit mode off
   (the script answers "audit mode off") the field says `transcript — not
   checked (audit off)`. Claude Code saves no transcript for a session
   started from a shell that carries another session's
   `CLAUDE_CODE_CHILD_SESSION` (its start screen says "Transcript saving
   is off"; the launcher drops the marker since 0.13.1): two sessions
   reached E with `cost not measured: transcript missing` and nothing for
   the audit to read (incident 13). A
   MISSING transcript is a fact for the record, reported to the owner in
   step 5 and asked about nowhere: the launcher drops the marker, so
   nothing a restart could change is left, the flow goes on, and the E
   step's cost says `not measured` (0.13.1's transcript question is
   gone). A resumed flow runs the same snapshot and puts the same field
   on its `Resumed` bullet.

   The check is not once per flow but before every launch: before each
   chunk's runner (C.1; the runner runs it again before each of its own
   launches and counts them on its hand-back), a consult (C.5), the slice
   reviewers (D) and the triage (E). A
   `PASS` that turns into a `FAIL` between steps ends the flow the way a
   second gate failure does, unless the user opted out at A, in which
   case the later checks are logged and the flow continues.
2. **Questions: three at most in this step, one per `AskUserQuestion`
   call, in this order: browser, delegation, autopilot.** Never bundle two of them
   into one call, whatever the tool allows: a call carrying two questions
   is this rule broken. A question the owner's own message already
   answered is skipped (a plain "go ahead" answers none). **A session
   with no question tool asks in plain text and ends its turn on the
   question**: a question is never skipped, and its answer never
   assumed, because the tool is missing; nothing after this step (the
   branch, the gate, a launch) runs until the owner has answered. The settings,
   sandbox and transcript questions of 0.13.1 no longer exist: the
   launcher guarantees what they asked about (2026-11-08).
   - **Browser**: as A.1 says, only on a UI-touching slice with no
     browser answering.
   - **Delegation**, asked once per project and stored. When
     `<target>/delegation.md` exists it holds the owner's standing
     answer: read it and ask nothing. If it says yes, write
     `<target>/delegation-slice-<nnn>.md` for this slice from it (the
     standing answer's date and words quoted, this slice's number and
     today's date); if it says no, write no per-slice file, and a
     mid-build gap stops the flow for the owner (C.5). Without it, ask:
     "May decisions that come up during the build be settled with the
     owning persona without asking you, on this slice and every later one
     on this project? Each is logged, committed under the persona's name,
     and you can overturn it." Write `<target>/delegation.md` with the
     answer either way: the owner's words, the date, the slice it was
     asked on, what it covers (design decisions, security and reliability
     criteria, screen states, accessibility criteria), what it never
     covers (scope, requirements, anything that changes a confirmed
     requirement: those stay backward routes to the owner), and how it is
     changed (the owner says so in a message, or edits the file). On yes,
     also write the per-slice file as above. An owner's message that
     answers for this slice only ("no delegation on this one") applies to
     this slice and leaves the standing file as it is. The per-slice file
     stays the record C.5 reads and the planning commit carries.
   - **Autopilot**, asked once per project and stored. When
     `<target>/autopilot.md` exists it holds the owner's standing answer:
     read it and ask nothing. Without it, ask: "May the loop take its
     own recommendation without asking you, on this slice and every
     later one, at three stops: a per-chunk review or fixer count that
     is exceeded (the loop time still ends the flow), up to two rounds
     of verify, fix and review for a Critical or High left standing, and
     a planning correction that changes no decision? Each round and
     each correction is logged as taken as recommended. Anything that changes a number or decision
     you approved, accepts a risk (a dependency advisory, a check
     weakened, skipped or exempted, a baseline raised), deletes or
     rewrites committed work, pushes anything red, or touches scope or
     requirements is still asked." Write
     `<target>/autopilot.md` with the answer either way: the owner's
     words, the date, the slice it was asked on, the three stops, the
     always-ask list, and how it is changed (the owner says so in a
     message, or edits the file). It is committed with the planning
     commit. A message that answers for this slice only applies to this
     slice and leaves the file as it is. The A line carries `autopilot —
     <file path | none>`.
3. **Branch and base.** With a merged planning pull request (step 0),
   first `git switch '<default branch>'` and `git pull --ff-only`, so
   the slice branch grows from the merged plan. Inline with Bash: `git
   status --porcelain` on the target directory. Then `git switch -c slice-<nnn>-<slug>` (an issue
   fix: `slice-<nnn>-issue<n>-<slug>`, and the current commit is its fix
   base) from the
   current commit, the number from the slice file's name and the slug from
   its title, lower-case, hyphens. If any planning document is modified or
   untracked (the delegation file is), commit them now on this branch, by
   name, as `Planning: slice <nnn> ready for implementation`; with a
   merged planning pull request this holds only what was written since
   (the delegation file, the log), and it exists so the gate's
   `--protect` checks have a committed version to compare with. Then
   `git rev-parse --short HEAD` is the **base**: every gate and every
   reviewer diff in this flow is computed against it or against the
   previous chunk's commit, so no baseline file is needed. Create the
   records directory. Nothing is pushed here.
4. **Design-readiness gate**, inline with Bash:

   ```
   python3 -I "${CLAUDE_SKILL_DIR}/scripts/readiness_check.py" --planning '<target directory>' --slice <nnn>
   ```

   Twelve mechanical checks over the planning documents: every criterion
   quoted under a design component; every failure path homed; a number on
   every retry, wait, poll and give-up; security and reliability agreeing
   on shared failure paths; a mockup for every named state; on a slice
   with a screen design, its `## States this slice changes` section, each
   state by its mockup's name (the list the screen-change check reads at
   delivery); no open
   question routed to the implementer; a "Kept for later slices" line;
   every open or deferred item in the slice file triaged (`usable without
   it`, with how, or a blocker); a failure-mode row for an external
   provider's unusable reply; with a `domain-model.md`, every state the
   slice file names in the model with a way out or left unsupported by
   the owner; no value of a file the owner provided
   (`sources.md` in the target directory lists them by location) in the
   planning directory or anywhere in the code. An issue fix adds
   `--fix-base '<fix base>'`: the checks then fail only on what the fix
   added or reworded, and what already failed at that commit is listed
   (`INFO  older-gap:`, then `older gaps: <n>`), for the one issue the
   issue-fix rule above files. Its last line is `readiness: PASS` or
   `FAIL`, with a `route:` line per failed check naming the persona. On
   FAIL, each failed check is a backward route (step 3's rule): write its
   own log entry naming the check and the document, run the named skill
   inline with the `Skill` tool (telling it which check failed and which
   document to revise in place), and when it returns run the gate again.
   Repeat until it passes; no builder is launched meanwhile. Under
   autopilot the routed skill is told one more thing with the failed
   check: the autopilot file by path, and that a revision which changes
   no decision (a number the documents already state, written where the
   check looks for it; a heading; a home for a failure path the design
   already decides) is written without a question, while a new number,
   a choice between two readings or anything of scope is still asked.
   The entry's bullet says `taken as recommended: <check> (autopilot)`
   when nothing was asked.

   **A blocker** (`route: open-items-triaged -> the owner (blocker)`) is
   the one readiness failure that goes to the owner, not a persona: one
   `AskUserQuestion` per blocking item, the item quoted, three answers:
   **decide it now** (the answer is a backward route to the document that
   owns the question, `requirements-refinement` or `vertical-slicing`,
   which records it), **cut it into its own slice first** (a backward
   route to `product-slicer:vertical-slicing`), or **the slice is usable
   without it** (the owner's words, recorded on the item by
   `vertical-slicing` as its `Usable without it:` sentence). Why: a
   deferral six reviewers accepted left a first choice permanent and a
   misclick without undo, which a cold read found (incident 14).

   **A source value** (`route: no-source-values -> the owner (source
   values)`) is the other readiness failure that goes to the owner
   first: the check found a text or an amount of a listed source in a
   document or in the code, and only the owner can say whether
   `Groceries` on a line is a row of their file or the app's own word.
   The gate's output names files, lines and cells, never a value, and is
   safe in the log. **The log never holds a value**, not as the sheet
   has it and not as the document writes it: the log is committed, and
   its entry for this reads `no-source-values: <n> places in <file>,
   put to the owner`, nothing more. For the question, run the scan once
   more with `--show`, inline, its output never saved to a file:

   ```
   python3 -I "${CLAUDE_SKILL_DIR}/scripts/source_scan.py" scan --planning '<target directory>' --show
   ```

   Its `value:` lines give each distinct value as the documents write
   it, with its places. Put them to the owner in **one**
   `AskUserQuestion`, the list in the question, the source named as its
   `sources.md` row names it (the Source cell, its tab, the `Read on`
   date and the stage that listed it; never "your file" or "the
   workbook" alone, which an owner asked cold cannot place), three
   answers: **none of
   these is from my file** (add each under `## Allowed by the owner` in
   `sources.md`, as the document writes it, with the owner's words and
   the date; these lines are the one edit of a planning document that is
   yours, and they are the owner's sentence, not your judgment), **these
   are** (the owner names which: each document that holds one is a
   backward route to its owner, told the file and the lines and to
   rewrite them with invented values, step 3's rule; a value in code from
   an earlier slice is the owner's next decision, a fix or `delivery`'s
   "Removing a value from history"; everything the owner did not name is
   allowed as above), or **stop**. Then the gate again. A listed source
   the scan could not read (`not readable`) stops the flow for the owner
   in one line naming the row: the file put back at its location, or the
   row corrected; the scan is never skipped. You never open a listed
   source yourself, with any tool: one command that dumps a file puts
   the whole of it in the session's transcript for good (incident 15).

   **The log after the routes.** The backward routes are entries of
   their own, so once the gate passes after one or more of them, write a
   **new** chunk-loop entry (heading `slice ready for implementation,
   readiness PASS after <check> (entry <n>), <check> (entry <m>)`,
   `**Routed to:** chunk loop`, `**Artifact:** see sub-entries below`)
   and put the A line and everything after it under that entry; the
   first chunk-loop entry gets one indented bullet, `readiness routed
   back (entries <n>, <m>); the loop continues under entry <new>`, and
   nothing else. A run that appended A to E under its second backward
   route had all sixty of its loop calls read as unlogged by the checker
   (incident 17; the checker now reads either form; the skill
   says this one). When the gate passed first time the entry already
   written is the one. Then write the A line: `readiness — PASS` when it
   passed first time, otherwise `readiness — PASS after <check> (entry
   <n>), <check> (entry <m>)`.
5. **Gate checks.** The gate runs the project's own checks from
   `gate-checks.json` at the project root: the eight categories
   `technology-bootstrap` picks a tool for per stack (type-aware lint,
   stricter compiler flags, complexity and length limits, duplication,
   unused code, changed-line coverage, test timeouts and random order,
   secret and workflow scans), each held against the existing code as
   its baseline, so only a new violation fails (incident 36). Inline
   with Bash, look for the file and for a `## Gate checks` heading in
   the bootstrap document, and take the first that applies:
   - **The file is there**: nothing to do; `gate checks — present`.
   - **No file, the section is there, the project has a manifest**: one
     fresh Sonnet fixer on the slice branch, before B
     (`kad-dev-team:tdd-coach:AGENT`, `model: "sonnet"`, `maxTurns:
     120`, `tdd-implementation-lite`, its handed-back path, chunks are
     committed), handed the bootstrap document by path and one named
     fix: wire the section as written (each picked tool installed
     exact-pinned, its configuration and manifest script, and
     `gate-checks.json` with one entry per category in the forms the
     section's skill gives), change no source or test file to make a
     check pass, then run

     ```
     python3 -I '<scripts>/validation_gate.py' --project '<project root>' --record-gate-baselines
     ```

     then run **the project's own dependency audit**, the command CI
     runs or the manifest names (`pnpm audit --audit-level=high`, `npm
     audit`, `pip-audit`), and say in its report what it printed: a tool
     wired here that brings an advisory with it turns CI red at
     delivery, hours later, on a branch that did nothing wrong (one did,
     incident 46). An advisory the audit names that came in with a tool
     of the section is not the fixer's to accept, pin around or ignore:
     its hand-back names the tool and the advisory, the A line says
     `gate checks — wired <sha>, advisory <id> through <tool>`, and the
     owner is asked, once, here: keep the tool with the advisory
     recorded as accepted (by `supply-chain-review`, with an expiry),
     pick the section's next tool for that category, or leave the
     category unwired. Then
     commit everything as `Gate checks: wired`. Check the hash it
     hands back as C.2 checks a runner's; `gate checks — wired <sha>`.
     A category the fixer could not wire is its report's, and the A
     line says `gate checks — wired <sha>, <n> not wired` for step 5.
   - **No file, the section is there, no manifest yet** (a first slice
     in an empty repository): the same launch after chunk 1's records
     commit, when there is something to run the tools on; `gate checks —
     after chunk 1`, and an indented bullet under chunk 1's C line with
     the hash.
   - **No file and no section**: a backward route, its own entry, to
     `software-architect:technology-bootstrap` for that section alone
     (its re-entry rule), then step 2 again. Nothing else of the
     bootstrap is reopened.

   **Every command CI runs is a gate check.** The file that is there
   may be older than this rule: read the CI workflow's `run:` lines (or
   the manifest's check scripts when there is no workflow yet) against
   the file's commands, inline. A check CI runs that the gate does not
   (the format check is the usual one: reviewers raised it as a High on
   two chunks of one slice, and a pull request went red on it) is
   handed to that same fixer as one more named fix: add it to
   `gate-checks.json` under the category `format and other CI checks`,
   as an exit-code check, with the command CI uses. `gate checks —
   present, <n> added from CI` on the A line.

   You never write `gate-checks.json`, pick a tool or set a baseline
   yourself, and never lower or raise a baseline to make a gate pass: a
   count over its baseline is the gate's `FAIL`, and it goes to the
   fixer like any other.

Write the A line now (format below), then go to B.

**B. Plan.** Launch one implementer, `kad-dev-team:tdd-coach:AGENT`,
`model: "sonnet"`, real async `Agent` call, no worktree isolation (the
slice branch in the real tree is the worktree, and one agent writes at a
time). Its task: invoke `kad-dev-team:tdd-implementation-lite` first, by
name, and follow its "The chunk plan" section: read the slice file, the design
doc, the security and reliability criteria, the screen design and
accessibility criteria if UI-touching, and the unit's read context (the
Active requirements document, every slice file cut for the unit, every
design doc for any of its slices), all by absolute path; consult
`map-query`; write the chunk plan under `## Chunk plan` in the
implementation report (create the file with the report's heading if it
does not exist) and stop, building nothing. One line saying the
orchestrator reviews the result. Nothing about chunks being committed yet:
this agent commits nothing. Wait for it.

When it returns, check the plan mechanically and nothing else: the file
has a `## Chunk plan` heading with two to eight chunks; every chunk has a
Title, Delivers, Files, Done when and Touches line; every Delivers names
at least one criterion (an identifier, or the criterion's text quoted when
the document numbers nothing) and every Files at least one path; every
**Done when** names a **seam test** (its first quoted test name is
preceded by the word `seam`, as the skill prescribes); no path is outside
the slice's module directories as the design names them, the project's
test directory, the root configuration files, or the records directory.
Note the design's module directories: they are the gate's `--module-dir`
list for every chunk. A plan that fails a check goes back once to a fresh
planner with the failing check named, as a new launch with the same task;
a second failure ends the flow with the B line saying why. You do not edit
the plan, reorder it or judge its chunking: the plan is the implementer's.
Commit the plan, by name, as `Plan: slice <nnn> in <k> chunks`. Write the
B line: the chunk titles in order.

**C. Chunks, one at a time.** For chunk k of n, in the plan's order, one
chunk runner carries the round and the orchestrator keeps the records.
Why: an orchestrator thread that carried the mechanics itself averaged
about 427k cache-read tokens per call over 396 calls and was 44% of the
slice's cost (incident 8); the v4 design (D9) said to build the runner
above about 250k. The runner's own
procedure is `skills/chunk-runner/SKILL.md`; what follows is the
orchestrator's side.

1. **Launch the runner.** Sandbox check (as A.1; logged). Then the data
   hash (`scratch_run.py --hash '<data dir>'`, the data rule above).
   Then one `kad-dev-team:chunk-runner:AGENT`, `model: "opus"`,
   `maxTurns: 200`, a real async `Agent` call, with: `kad-dev-team:chunk-runner`
   to invoke first, by name; chunk k of n; the chunk's five plan lines
   verbatim; the report's path; the slice documents by absolute path (a
   decision document a consult committed since the plan is one of them,
   nothing more); the project root, the records directory, the sidecar,
   the base commit (the plan commit for chunk 1, the previous chunk's
   last accepted commit after), the documented test command, the module
   directories and deviation zones as B noted them, the protect list,
   this skill's `scripts/` directory by absolute path, `scratch_run.py`'s
   path and the chunk's scratch folder, the cadence, whether a browser
   answered at A, whether the slice touches UI, and the A line's sandbox
   field (`PASS` under the launcher, or that the owner opted to continue
   unsandboxed, so the runner knows whether a later `FAIL` ends the round
   or is information). Nothing about other
   chunks' findings, the owner, the budget or the flow's state. Wait for
   its hand-back, and by the runner's own rule: waiting is ending the
   turn with no tool call, never a background command, a poll or a
   monitor, and nothing of the runner's result exists until the
   hand-back is in front of you. The runner launches the builder, runs the gate (with `--agent
   <builder id>`, so the C line's `shell edits` is the counted number;
   nobody reports one), launches the reviewer and the smoke agent
   (`loop` only),
   records the rounds with `rounds_record.py`, launches the fixer and the
   regressions re-review, and never asks the owner, never consults a
   persona, never writes the log and never commits the records.
2. **The hand-back** is one line in the C line's own field order, as far
   as the runner's work went, plus `builder <agent id>` and `reviews <n>
   fixers <m>` for the budget. Three endings need you:
   - `needs-decision <persona>: <report path> — <title>` (round 0 is
     recorded; the fixer has not run): C.5 below, then relaunch a runner
     for the same chunk with the hand-back line and the decision commit,
     telling it to resume at the fix round (its resume rule).
   - A standing Critical or High (the line's `standing`, its `last`
     counts among them): the autopilot round above when `autopilot.md`
     says yes, its fragment appended to the C line; without the file, or
     after its second round, the flow ends there for the owner.
   - `gate FAIL: <checks>; ended` or `stall: ended`: the flow ends there,
     the C line says why, step 5 says what
     is built; the branch stays as it is. `gate FAIL: sources; ended` (a
     changed file still holds a value of a file the owner provided after
     the runner's one fixer) ends it the same way, and step 5 carries
     A.4's source question over the chunk's files (the scan with
     `--show`, the same three answers): the owner's answer resumes the
     chunk.
   - `flaky: <test>`: information on the C line; the runner already
     handled it (one re-run, then one fixer at the cause on the second
     sighting, counted as the gate fixer).
   **The line is the last line of the hand-back.** A runner that put
   sentences before it has still handed back: read the last line as the
   line and nothing above it as a result (what it says there is in no
   field, so it goes on no C line and to no question).

   **Check the line before anything rests on it.** Every hash the
   hand-back names (`commits`, `PASS after`, `red commit`, `r1 fix`, `r2
   fix`) goes through `git cat-file -e '<sha>^{commit}'` and is looked
   for in `git rev-list <base>..HEAD` (a commit that exists outside the
   chunk's range is not the chunk's), inline, before
   the C line is written, the records are committed, or the owner is
   told or asked anything built on the line. All of them exist: go on.
   One does not, or is not in the range: the line is not a result. Nothing is written from it
   and none of it is put to the owner as fact; relaunch a runner for the
   same chunk, once, with the line, the hash the repository does not
   hold, and what `git log --oneline <base>..HEAD` and `git status
   --short` print, telling it to resume from what the tree holds (its
   resume rule). A second line with a hash that does not exist ends the
   flow: the C line carries the fields `git log` confirms, `?` in the
   others and `hand-back unverified: <sha>`, and step 5 reports what the
   tree holds, never what the line said. Before any question that would
   discard, revert or rewrite work, read `git log` and `git status`
   again: the question describes what they show now. An owner once
   answered "discard" on a runner's report of commits nobody had made
   (incident 31).

   You never open a report the hand-back names and never run
   `rounds_record.py` yourself at C: the counts on the line are the
   script's as the runner printed them (its rows are already in the
   sidecar), and the fixer read the reports itself.
3. **Data check.** `scratch_run.py --hash '<data dir>'` again; `data
   unchanged` or `data CHANGED` on the C line; `CHANGED` ends the flow
   before the next chunk and is reported to the owner.
4. **Light cadence.** Under `light` the runner runs the build and the
   gate only and hands back with `review none; smoke none` and no fix
   round: nothing is reviewed or driven until D, where the six
   reviewers, the walk and the cold read find it and the chunk's own
   builder fixes it (D.3). The data check of step 3 still runs (a gate
   starts the suite, and a suite can touch a data folder). Everything
   else in this step is the same.
5. **A gap that stops a fix.** When the runner hands back a
   `needs-decision (<persona>)` finding (no planning document states the
   rule it would need), the decision is made before the fixer runs:
   - **With a delegation file**: sandbox check; launch the owning persona
     once per persona per round, `model: "opus"`, a real `Agent` call:
     `kad-dev-team:software-architect:AGENT` (structure and interfaces,
     invoking `architecture-design`),
     `kad-dev-team:devsecops-engineer:AGENT` (`reliability-requirements`
     or `security-requirements` for a criterion),
     `kad-dev-team:ux-designer:AGENT` (`screen-design` for a state),
     `kad-dev-team:accessibility-engineer:AGENT` (`accessibility-review`
     for its criteria). Hand it: the skill to invoke, the findings by
     report path and title, the planning document it owns by absolute
     path, and the delegation file by absolute path. It revises its own
     document in place, commits `Decision <n>: <title>` (the number
     continuing the document's own numbering) and hands back the hash and
     one sentence. Write one indented line under the C line, `decision
     <n> <sha> (<persona>)`, and pass the hash to the relaunched runner.
     Consults are counted for the E line's `consults` field, never
     capped; one per persona per round.
   - **Without a delegation file**: launch the persona the same way; it
     hands back a recommendation and writes nothing (its skill says so).
     Save what it handed back, as given, to `<records
     dir>/chunk-<k>-r<i>-decision-<persona>.md` (your own record, not a
     planning document), write the C line with `needs-decision <persona>:
     <that path>` and stop the flow for the owner at step 5; the owner's
     answer resumes it at this round.

   Nothing else goes to a persona mid-loop: no "apply this edit", no
   decision you reached yourself, no editing a planning document on a
   persona's behalf. If the persona refuses to write, the flow stops as
   in the second case.
6. **The records commit** (`Records: slice <nnn> chunk <k>`: the reports,
   gate files and sidecar), then, with `KAD_AUDIT=1`, **the snapshot and
   the sync**, one command, inline with Bash, waited for:

   ```
   python3 -I "${CLAUDE_SKILL_DIR}/scripts/audit_sync.py" --project '<project root>' --slice <nnn> --snapshot --transcripts
   ```

   `--snapshot` first copies this session's transcript and its
   subagents' to the audit directory, now, not at a session end that may
   never come (incident 13); the sync then
   copies the whole slice folder, the records directory and every
   session's transcripts, found by session id (the live file Claude Code
   writes or the snapshot, whichever is larger), into the audit
   repository's clone, commits and pushes. With a `sources.md` in the
   target directory it reads every transcript with the source scan first,
   and a session holding a listed source's value is withheld: its
   transcripts stay on disk, uncopied, and the owner decides. Its
   last line goes on the C line's `audit` field as printed: `audit commit
   <sha>`, `audit commit none` (nothing new), or `audit sync FAILED:
   <reason>`, each with `; withheld: <session…>` appended when a
   session was withheld and `; snapshot FAILED: <why>` when the
   snapshot failed; a FAILED of either kind, and a withheld session (the
   owner allows the words under `## Allowed by the owner` or leaves the
   session out), also go into the report to the owner and never stop the
   loop. Without an audit repository the field says `not configured`,
   with `KAD_AUDIT` unset `off`, and nothing runs. **Then the C line**
   (the runner's fields, then `records`, `audit`, `data`), then the
   budget check (the hand-back's `reviews` and `fixers` counts and the
   clock; under autopilot the clock alone ends the flow), then the next chunk. Between launches the only thing you say
   to the user is one short paragraph per event, with the hashes; you
   never restate a finding, keep a digest, or narrate an agent's turns.

**D. Slice review.** When the last chunk is done:

1. Sandbox check; then `architecture-cartographer:map-update` for real,
   inline, against the tree: its skill runs the shipped extractor
   (`skills/map-update/scripts/extract_map.py`, TypeScript, JavaScript and
   Python today); for a language it has no extractor for, the map lists
   the modules from the tree with no edges and says so, and you write
   nothing: no extractor, no parser, no helper. Commit the map by name as
   `Map: slice <nnn>`.
2. **Definition of Done**, inline with Bash, before any reviewer:

   ```
   python3 -I "${CLAUDE_SKILL_DIR}/scripts/done_check.py" --project '<project root>' --planning '<target directory>' --slice <nnn> --test-cmd '<documented test command>'
   ```

   Nine checks: a README that takes a stranger from clone to running;
   linter and formatter configured and clean; the typecheck passing; no
   application code inside string literals; no planning reference in
   code; comment density at or under 5% of non-blank source lines; the
   design's "Kept for later slices" names present in the schema; env and
   deployment defaults pointing at local or sandbox, never production;
   tests that are not padding (share of tests asserting on source text,
   manifests or script bodies at or under 10%). Its last line is
   `definition of done: PASS` or `FAIL` with a `fix:` line per failure.
   Act on the failures in one batch: a missing or incomplete README is
   `docs-writer:readme`, invoked inline with the `Skill` tool, which
   writes it from the manifest, the design and the slice and commits it;
   comment density over the line is first a `code-review` pass on
   comments only (one `code-reviewer` launch, `model: "opus"`, invoking
   `why-comments` on every file over the line, report
   `slice-comments-review.md`); everything else, and the comment
   verdicts, go as named fixes to **one** fresh Sonnet fixer
   (`maxTurns: 160`, `tdd-implementation-lite`, its handed-back path, chunks are
   committed). Then the gate on the fix's range, then the check again. A
   check still failing after that stands: README, typecheck, lint, code
   in strings and the persisted names are High (the flow stops for the
   owner before the reviewers); comment density, planning references, env
   defaults and padding are Medium (the pull request body's Definition of
   Done table). Then:

   **Mutation on the changed lines**, started here and **left running
   beside the reviewers**: a tool breaks each line the slice added, one
   operator at a time, and the suite says whether any test notices. It
   works in a disposable clone under the temp directory, so nothing in
   the project's tree moves while the reviewers read it, and nobody
   waits for it but the one reviewer who needs its report.

   ```
   python3 -I "${CLAUDE_SKILL_DIR}/scripts/mutation_pass.py" changed --repo '<project root>' --base '<base>' --out "${TMPDIR:-/tmp}/kad-mutants-<slice>.json"
   python3 -I "${CLAUDE_SKILL_DIR}/scripts/mutation_pass.py" run --repo '<project root>' --mutants "${TMPDIR:-/tmp}/kad-mutants-<slice>.json" --test '<documented test command>' --base '<base>' --allow-dirty --remove-mutants --first-failure --budget 900 --log "${TMPDIR:-/tmp}/kad-mutation-<slice>.jsonl" --out '<records dir>/slice-mutation.md'
   ```

   `changed` inline; `run` as one Bash call with `run_in_background:
   true`, the only background command of the loop: you go straight on to
   step 3 and are told when it exits. Never a timeout of your own on it
   and never a poll: the script ends a mutant's suite at its first
   failing test, ends a suite that hangs after three times the
   baseline's own time (and everything that suite started), and stops
   starting mutants after 15 minutes, listing the rest as not run. On
   one slice the same pass, run inline with a 30-minute limit per
   command and eight reviewers waiting behind it, took 2 h 54 m
   (incident 38). When the owner asks how far it is, the last line of
   the `--log` file says (`"mutant": <i>` of the count `changed`
   printed), and you say so in one sentence.

   The mutants file holds lines of the source: it stays outside the
   tree, readable by its owner alone, and `--remove-mutants` deletes it
   when the pass ends, however it ends. With `--allow-dirty` a run that
   is killed leaves no mutant in the project's tree. The report carries
   counts, lines and test names only. The run's last line, `mutation:
   <n> mutants, <c> caught, <s> survived` (with `, <h> of the caught by
   a hang`, `, <k> not counted` or `, <m> not run (the 900 s budget)`
   when there are any), goes on the D line as printed. You read no
   survivor and judge none: the test-quality reviewer is handed the
   report and says which matter, and which hangs and unsteady tests the
   report names are findings. A run that cannot start (the baseline
   fails three times, a file would not restore) is `mutation: not run
   (<the script's line>)` on the D line and the test-quality reviewer
   goes ahead without it.
3. **The six reviewers once.** Sandbox check. `model: "opus"`, in
   parallel, **each handed five things and nothing else**: the project
   root, the documented test command, the whole slice's range
   `<base>..HEAD`, its report path `slice-r0-<reviewer>.md`, and the
   path of the last gate output on this tree (the suite's run; six
   suites at once on one checkout contend for ports and files, so no
   reviewer runs it). **Five start now; the test-quality reviewer starts
   when the mutation pass exits**, handed a sixth thing, the path of
   `slice-mutation.md` (it is the one reader of that report, and 15
   minutes later than the others it still ends before the walk and the
   cold read do). Round 0 is recorded, and the fix round starts, when
   every reviewer, the walk and the cold read have reported. Each follows its skill's "Cold pass first": all of
   `src/` and `test/` read, the typecheck, lint and format check run and
   the suite's result read from the gate output (the tree is installed;
   no reviewer installs, since the six share one `node_modules`),
   suspected bugs probed by execution, the cold findings written; then, for the four criteria
   reviewers, the slice documents found from the report path and the
   criteria checked under `## Against the criteria` (`architecture-review`
   takes the map diff from `docs/architecture-map.md` in the tree then).
   The six: `tdd-coach:test-quality-review`,
   `code-reviewer:code-review`, `software-architect:architecture-review`,
   `devsecops-engineer:security-review`,
   `devsecops-engineer:reliability-review`, and
   `accessibility-engineer:accessibility-review` only if the slice is
   UI-touching. No reviewer restates an accepted deferral of the slice
   file: `deferrals.py` lists them once in the pull request's body at E
   (a quarter of one slice review's findings were the same deferrals,
   said by each criteria reviewer, incident 37). Lows are allowed here
   and only here: they go
   to the pull request body under "Known Lows", grouped by theme, and are
   not filed.

   **The criteria walk** (P2.1), a seventh launch when the slice touches
   UI, with the six: `kad-dev-team:accessibility-engineer:AGENT`,
   `model: "opus"`, invoking `kad-dev-team:accessibility-review` in its
   "Criteria walk" mode, handed: the project root, the README's start
   command, the slice's criteria by path (the slice file's Given/When/Then
   list, the accessibility criteria, and the security and reliability
   criteria), the scratch launcher and its folder (the data rule), the
   report path `slice-r0-walk.md`. It opens the built app in the real
   browser, drives every criterion a browser can reach and writes the
   table `rounds_record.py` reads (criterion, PASS / FAIL / NOT
   REACHABLE, how it was driven, a screenshot per state under
   `<records dir>/walk/`); a FAIL is a finding in the shared format and
   goes to the fix round like any other; NOT REACHABLE names why; the
   screen-reader announcements are the owner's manual checks, listed as
   such, and nothing else is. With no browser answering (the owner chose
   to continue at A) every row is NOT REACHABLE with that reason and the
   owed finding stands as in C. The data hash runs around this launch as
   around a smoke run.

   `rounds_record.py` with `--chunk D --round 0` on all the reports (the
   walk's among them; its fragment carries `walk <pass>/<fail>/<not
   reachable>`). Then one fix round: one fixer for every Critical, High
   and Medium (and any `needs-decision` through C.5 first), the gate, a
   regressions-only re-review by the same reviewers on the fix's diff
   (`slice-r1-<reviewer>.md`; the walk re-driven only for its FAIL rows,
   `slice-r1-walk.md`), `rounds_record.py` with `--range` (it charges
   the fix only with lines it wrote: a line the fix moved is
   pre-existing, and a reviewer with no round-0 report is `first-seen`,
   counted apart), a second and last fixer for the regressions and the
   first-seen findings, the gate; then **the last-fix
   review** on that second fix's range (above; `--chunk D --round 2
   --last`), whose findings stand. A Critical or High standing after
   that gets the autopilot round when `autopilot.md` says yes; without
   the file, or after its second round, it stops the flow before E.
   Standing Mediums go to the
   body, NOT REACHABLE rows go to the owner's checklist issue.

   **Who fixes, by cadence.** Under `loop`, the fixer is one fresh
   Sonnet agent as always (`model: "sonnet"`, `maxTurns: 160`,
   `tdd-implementation-lite`, its handed-back path, chunks are committed).
   Under `light` (P3.2's third change, aimed at the fixer being a stranger
   to the code: a quarter of every run's findings have been the fixer's
   own regressions, incident 19) the findings are grouped by the chunk whose
   Files line holds their file, and each group goes by `SendMessage` to
   that chunk's own builder (the agent id on the chunk's C line, `builder
   <id>`), with the same handed-back task; a builder that cannot be
   reached (the send fails, or it returns nothing) leaves its group to
   **one** Opus fixer (`model: "opus"`, `tdd-implementation-lite`) for
   everything no builder cleared; then the gate, the regressions-only
   re-review and the second fixer as above. The D line records `fixes
   builders <n> opus <m>`, and the review measures regressions per
   actionable finding against the 25% of incident 19.
4. **The cold read**, an eighth launch with round 0's reviewers (it was
   the stranger test, a README followed on a clone in the last round;
   it is now the whole reading a stranger gives the code, and early
   enough for its bugs to be fixed): `kad-dev-team:tdd-coach:AGENT`,
   `model: "opus"`, a real async `Agent` call, told to invoke
   `kad-dev-team:cold-read` first, by name, and handed: the project
   root (it clones from it and never works in it), the branch, the
   base commit, the scratch launcher and a scratch folder of its own
   (the data rule holds on a clone too), and the report path
   `slice-r0-cold.md`. **Nothing else**: no planning document or its
   path, no criteria, no report, no gate output, no word on what the
   slice is for. Its skill is the procedure: a fresh clone, the README
   from its first command, every source and test file read, each thing
   the slice adds paired with the older code it runs beside or depends
   on, every suspicion probed by execution, the clone removed. The
   data hash runs around it and goes on the D line.

   Its report is in the shared finding format and is recorded with
   round 0's (`rounds_record.py` reads `slice-r0-cold.md` as reviewer
   `cold`). A finding marked `confirmed by execution` goes to D's fix
   round with the others, at the severity the reader gave it, whether
   the code is the slice's or older (older code the slice runs beside
   is what this reader is for; a bug in it that the slice cannot ship
   with is fixed here, and one it can is a standing finding for the
   body). A `verify` finding is not handed to the fixer: it stands,
   named in the body, for the owner. A README that does not get the
   reader to a running app is a High for `docs-writer:readme`, inline,
   then the fixer's gate, as before. The cold read is not launched
   again at round 1: the regressions-only re-review covers the fix's
   diff. The audit's own cold read after delivery stays as it is, a
   second reader the loop does not see.
5. The records commit `Records: slice <nnn> review`; the snapshot and
   the sync exactly as C.6, their last line on the D line's `audit`
   field; then the D line.

**E. Delivery.** No question is asked in this step; the user decided on
2026-10-24 that the branch is pushed and the pull request opened without
one. **Nothing in this step runs in the background**: every command and
every launch is waited for, and the step ends in the same turn that
finishes its last action.

**A value of the owner's in the branch's commits** (the owner says one
got in, a reviewer's finding says so, or `delivery`'s scan before the
push refuses on it) is removed by `delivery`'s "Removing a value from
history" and by nothing else, at this step or at any other: invoke
`release-engineer:delivery` with the owner's words for the rewrite
quoted as they gave them, and it writes the map, rewrites the branch
and scans every commit. You never open a file `sources.md` lists, never
put a value or a pattern of values into a command, never run
`filter-branch`, `sed` or a rebase over the commits yourself, never
expire a reflog, and the log's line for it is delivery's record line
(counts and files). Without the owner's words for a rewrite the flow
stops at step 5 with delivery's refusal. An improvised removal once put
the values back in its own log bullet (incident 18).

1. **Records.** If D's fix rounds changed anything, `map-update` again and
   commit the map. Then commit the log and the records directory, with the
   handoff file removed, as `Records: slice <nnn> delivery`: `delivery`
   refuses a dirty tree, and the loop never committed the log before this
   (each C and D line names the records commit it follows). The E line
   written at the end stays uncommitted, like every other entry.
   **Nothing is checked again at E**: the Definition of Done results that
   `delivery` and the pull request body carry are the D line's, and the
   last gate output is the one on D's last fix; E runs neither
   `done_check.py` nor the gate (E is mechanics, not judgment, and a check
   re-run here has no fixer to go to).
2. **CI.** If the repository has no continuous-integration configuration
   (no `.github/workflows/*.yml`, no equivalent for the host the remote
   names), invoke `release-engineer:ci-pipeline` inline with the `Skill`
   tool: it writes the workflow for the project's stack, mirroring the
   gate's commands (install with a frozen lockfile, typecheck, lint, the
   suite with its coverage gate) on Linux and macOS, pinned action SHAs, least-privilege
   permissions, and commits it by name. If one exists, skip; a gate
   command the workflow does not run is a line in the report, not a change
   you make. An audit job that fails on a dependency advisory is a named
   fix for a fresh Sonnet fixer with `supply-chain-review`'s
   recommendation, then the gate; you edit no manifest or lockfile
   yourself.

   **The screen-change check**, when the target directory holds a screen
   design for this slice (`visual-ux/screen-*<nnn>*.md`, the file the
   readiness gate read). Every state with a saved baseline is rendered
   again in CI and compared with it; two things have to be in the branch
   before the push:
   - **The check itself.** No `.github/workflows/screens.yml`: invoke
     `release-engineer:ci-pipeline` inline, telling it the target
     directory, for its screen job (the workflow, the capture harness
     with its pinned browser, the comparison's copy, the threshold
     file); it commits them by name. One that exists is left as it is.
   - **A capture for each state the slice lists.** Inline with Bash:

     ```
     python3 -I "${CLAUDE_SKILL_DIR}/scripts/screen_check.py" states --planning '<target directory>' --capture screens/states.mjs --base '<default branch>'
     ```

     Its last line is `states: <n> listed, <m> not driven`, with one
     `missing: <state>` line per state the screen design lists as
     changed or new and the project's capture file does not drive. None
     missing: go on. Otherwise sandbox check, then **one** fresh fixer
     (`model: "sonnet"`, `maxTurns: 120`, `tdd-implementation-lite`, its
     handed-back path, chunks are committed) handed the screen design
     and `screens/capture.mjs` by path (its header is the contract), the
     `missing:` lines as printed, and one named fix: in
     `screens/states.mjs`, one quoted key per missing state, named
     exactly as its line names it, whose function drives the built app
     to that state on made-up data (the data rule: a temporary folder,
     the project's fake credential tool, no provider connection, never
     the owner's data directory), and nothing else changed: no source
     file, no test, no baseline, no threshold, no screen design. Then
     the gate on its range (with `--allow screens/`: the capture file
     is outside the design's modules on purpose) and the script once
     more. A state still
     missing is not asked about: CI reports it and E.4's red path takes
     it. The fixer's commit is read by E's one last-fix review with the
     other fixes of this step. You write no capture code yourself.
3. **Push and pull request.** Invoke `release-engineer:delivery` inline
   with the `Skill` tool, telling it: the branch, the base, the report's
   path, the records directory and the sidecar, the Definition of Done
   results, the slice file's path (its deferrals are listed in the body
   by `deferrals.py`, once), and the tracker `user-story-writeup`
   recorded for this project (or that none is recorded). It pushes the
   branch, has
   `docs-writer:pr-writeup` write the body from the report (what was built
   chunk by chunk, decided gaps and decision commits, escalations, the
   Definition of Done table, the standing Mediums, the deferrals list,
   the Known Lows grouped by theme, the model and tool provenance), opens the pull request
   against the default branch, files **each standing Medium** as one issue
   in the recorded tracker (title from the finding, body from its text,
   file and line, label `tech-debt` where the tracker has labels), **files
   no Low** (they stay in the body; the owner may ask for them later),
   edits the body so each standing Medium links its issue, and returns
   the pull request number and the issue numbers. With no tracker
   recorded, the standing Mediums stay listed in the body and the E line
   says so; nothing is asked.
4. **The CI watch after every push; then the external review triage,
   until nothing to fix, capped at five rounds.** A pushed branch is not
   delivered until its checks are green. After E.3's push, and after
   every later push of this step, `delivery`'s "CI watch" runs before
   anything else and returns one of three states:
   - `CI green <sha>`: go on to the comments.
   - `CI red r<i>: <path>` (the failing tests are in `<records
     dir>/pr-ci-r<i>.md`, with the platform difference): sandbox check;
     one fresh fixer (`model: "sonnet"`, `maxTurns: 120`,
     `tdd-implementation-lite`, its handed-back path, chunks are
     committed) handed that file by path and two lines word for word:
     the tests failed on the platform the file names and passed on this
     one, so the cause is that difference; and the failing tests are not
     weakened (no skip, no platform guard around an assertion, no
     loosened expectation, no retry). Then the gate on the fix's range,
     saved as `gate-pr-ci-r<i>.txt`; on PASS `delivery` pushes and the
     watch runs again. Three rounds at most; every round goes to the
     sidecar with `"chunk": "pr"`.
   - `CI no result`, or red after the third fix: the flow stops at step
     5. Nothing after this point runs.

   **The screens check has two red verdicts, and `delivery` reads which
   before any fixer is thought of** (its "The screens check"). `screens:
   BASELINES OWED` is no failure: only states the slice's screen design
   lists changed, `delivery` adopts their new images as baselines from
   the run's artifact with `screen_check.py adopt`, commits them, pushes
   and watches again; no fixer, no round counted, and the E line carries
   `baselines <sha> (<c> changed, <n> new, <r> removed)`. `screens:
   FAIL` is `CI red r<i>` like any other, the same one fixer and the same
   three rounds, with these two lines word for word in place of the
   platform ones: the states the file names changed on screen and the
   slice's screen design does not list them, so the cause is a style or
   markup change that reached them from something the slice did change;
   and the check is not weakened (no edit to a baseline image, the
   threshold file, the screen design's changed-states list, the workflow
   or the capture of a failing state: the code is made to leave those
   states as they were). You never copy an image out of an artifact or
   commit a baseline yourself.

   **A red or unsettled check is never reported as built.** Whenever
   the last watch did not say green, the report at step 5 opens with the
   CI state and the run's URL, before anything about what was built, and
   says the pull request is not ready; nothing is pushed "to see", and
   merging is never suggested. A pull request once went to the owner as
   built while its checks were failing on a real defect the local gate
   could not see (incident 33).

   Then the comments: `delivery` waits for the reviews (up to the bound
   its skill states), then reads every review comment not left by this flow (the
   ones that carry the plugin's footer line; the author is never the
   test, since the owner may write from the account the session pushes
   as). If there are any: sandbox check; launch `kad-dev-team:code-reviewer:AGENT`,
   `model: "opus"`, to invoke `code-reviewer:external-review-triage` with
   the pull request number, the slice documents by path, the records
   directory (the plugin's own findings on the same files) and a report
   path; it returns a verdict per comment: **fix**, **decline** with the
   reason, or **defer**. Fixes go to a fresh fixer as in the runner's fix round (one batch,
   commits), then the gate on the fix's range, then `delivery` pushes,
   posts each decline's reason as a reply on its comment and files each
   deferral as an issue. The push brings the checks and the external
   reviewer back: the CI watch first, as above, then its
   new comments on the fix are the next round, through the same triage,
   until a round has no comment to fix or round 5 is done. Comments that
   arrive after that are the user's.

   **Then the last-fix review, once.** When this step committed any
   change to source or tests (a CI fix, a triage fix), one last-fix
   review reads them together (above; the range from the head D left to
   `HEAD`, `--chunk pr --round <i> --last`), after the checks are green
   and the comments are done, before the cost. Its Mediums are filed by
   `delivery` like D's standing ones and its Lows join the body. A
   Critical or High gets the autopilot round when `autopilot.md` says
   yes, and its fix is pushed only after its gate passes and is watched
   like every push; without the file, or after the second round, the
   report at step 5 opens with it and says the pull request is not
   ready. Every comment and verdict goes to
   the sidecar with `"chunk": "pr"`; the comments file is committed with
   the records.
5. **Cost.** Inline with Bash:

   ```
   python3 -I "${CLAUDE_PLUGIN_ROOT}/evals/tools/cost_by_role.py" --project '<project root>' --log '<target directory>/orchestrator-log.md' --sidecar '<records dir>/rounds-slice-<nnn>.jsonl' --session "$CLAUDE_CODE_SESSION_ID"
   ```

   The log names every session of this entry (the A line's `session`
   field, each `Resumed` bullet's), the sidecar every session that
   recorded a round, and `--session` adds this one; the script finds
   each one's transcript (the project's
   own directory, else the snapshots audit mode kept) with its subagents'
   and prints the total by role class. A session the log or the sidecar
   names whose transcript is nowhere is skipped and named: the last line
   then reads `cost $<n>, not covering <id> (no transcript)`. This
   session's own (`--session`) is never skipped: without its transcript
   the last line is `cost not measured: transcript missing for <id>` and
   there is no total. Its last line goes
   on the E line as printed, the `not covering` part included: a total
   that leaves a session of the loop out without saying so is never
   written (incident 20).
6. **Audit sync.** With `KAD_AUDIT=1`, the snapshot and the sync exactly
   as C.6 (the sync's `--transcripts` carries every session of the
   project, withholding one that holds a listed source's value), its
   last line on the E line's `audit` field: `audit commit <sha>`, `audit
   commit none`, or `audit sync FAILED: <reason>`, with `; withheld:
   <session…>` when one was, the FAILED and the withheld sessions also in
   the report to the owner; `not configured` without an audit repository,
   `off` without audit mode. A configured repository with no clone is
   that FAILED line, never a skip.
7. **The E line, written before the last push, so the log on the branch
   is the whole log.** Its `consults` field is the number of persona
   consults this flow launched, at C.5 and D; its `checks` field is the
   last watch's state, and only `CI green <sha>` lets the line say
   `clean`. Write it, then commit the log by name with whatever records
   are still uncommitted (`Records: slice <nnn> log`), push, and watch
   that push as step 4 watches every push: a commit that touches only
   the target directory changes no code, so the sha on the line is the
   head the watch last saw green before this commit, and the watch of
   the push itself needs nothing written when it is green too. Red on
   it (nothing in the code changed, so a job that flaked or a runner
   that failed) is an indented bullet under the E line and one more
   records commit, watched the same way. Then the audit sync once more,
   unrecorded, so the audit repository holds the finished log. Three
   runs ended with the log's last lines in the working tree and on no
   branch, and one needed a pull request of its own for them (incident
   43): `git status --short` is empty before the report.

   Then step 5 below: report what happened
   at each of the five steps, the CI state first, with the pull request
   and issue numbers, the standing findings if any, and the open external
   comments if the cap was hit; with `CI green` the slice has reached the
   terminal row, and without it the slice has not.

**Pausing and resuming.** On a context clear, a rate limit, a session end
or an owner's "hand off" mid-loop, before anything else write
`<records dir>/handoff-slice-<nnn>.md`: a first line saying it is resumed
by invoking `kad-dev-team:orchestrator` ("what's next"), never by
invoking the next step's skill directly; the A–E state (which step, which
chunk, which round), the next action, the standing list, the budget
counters (start time, reviewer launches, consults), the environment facts
a successor needs (test command, module directories, records directory,
whether the owner opted out of the sandbox, the autopilot answer, the cadence, each finished
chunk's `builder <id>`, and a runner's hand-back line when a chunk ended
mid-round), and the owner's standing directions; commit it with the
records; and write a memory pointer to it.
On invocation with a handoff file present for the slice, resume from it:
no new A step; run A's snapshot check (`audit.sh --snapshot`) and append
`Resumed <date> at <step>, session <this session's id>, transcript <kept |
MISSING: <why> | not checked (audit off)>` as an indented line under the
entry's last line (the cost at E covers every session the entry names)
and continue at the step the file names. The handoff file is removed by the records commit
at E.

**This row's `orchestrator-log.md` entry needs sub-entries for all five
steps, one line per chunk under C, not the one-line form every other row
gets.** Terse pointers, not prose: hashes, counts and file names locate
everything else, the sidecar holds the findings, and the transcripts audit
mode keeps are the complete record. The format rules: **one bold line per
step** (A, B, one per chunk under C, D, E), each appended as its step
completes and never edited; a decision, a correction, a resume or a budget
note is an **indented plain bullet** under the line it belongs to; **never
a second bold A, D or E line**, whatever interrupted the step (an
interrupted A is one A line written when A completes, with the
interruption as an indented bullet). D-line reviewer initials: `tq`
test-quality, `co` code, `ar` architecture, `se` security, `re`
reliability, `ac` accessibility; a C line's `review` field lists the
lenses the combined reviewer applied (`co tq` or `co tq re`).

```markdown
## <n>. <date> — slice ready for implementation

**Routed to:** chunk loop
**Artifact:** see sub-entries below
- **A. Start:** sandbox — `<PASS (<platform>; <Chrome | browser not needed | no Chrome, screen checks owed>) | none on <platform>; owner opted to continue unsandboxed | FAIL: <checks>; flow not started | no browser; flow not started | flow not started: no repository | flow not started: planning pull request not merged>`; session — `<id>`; audit — `<audit clone: <dir> | audit clone FAILED: <why> | audit: not configured | off>`; transcript — `<kept | MISSING: <why> | not checked (audit off)>`; delegation — `<file path | none>`; autopilot — `<file path | none>`; cadence — `<loop | light>`; budget — `<8h | 5h>, 2 reviews/chunk (+1 last fix), 1 fix/scope (+1 regressions)`; branch — `<name>`; base — `<sha>`<, planning commit `<sha>`>; records — `<dir>`; readiness — `<PASS | PASS after <check> (entry <n>), …>`; gate checks — `<present | wired <sha><, <n> not wired> | after chunk 1>`<; fix base `<sha>`; older gaps `<n>`< → `#<issue>`>>
- **B. Plan:** `<k>` chunks — `<title 1>`; `<title 2>`; … (`<report path>`, commit `<sha>`); modules — `<dir>`, `<dir>`
- **C. Chunk <k>/<n>:** `<title>`; sonnet `<turns>`t `<min>`m; commits `<sha…>`; gate `<PASS | PASS after <sha> | FAIL: <checks>; ended>`<; flaky `<test>`>; deviations `<n>`<; shell edits `<n>`>; review `<co tq [re] | none>`< r0 `<C/H/M>`>< nd `<n>`>; smoke `<PASS | <n> findings | none>`<; r1 fix `<sha>` → `<C/H/M>` (reg `<r>`, pre `<p>`<, first `<f>`>)><; r2 fix `<sha>` gate PASS; last `<C/H/M>`><; owed `<n>`>; standing `<C/H/M>`<; auto r<i> verify `<c>` confirmed, `<n>` not reproduced< fix `<sha>` → last `<C/H/M>`>>; builder `<agent id>`; budget `<h>`h `<reviews>`r; records `<sha>`; audit `<audit commit <sha> | audit commit none | audit sync FAILED: <reason> | not configured | off><; withheld: <session…>>`; data `<unchanged | CHANGED | not named>`<; stall: <relaunched | ended>><; hand-back unverified: `<sha>`><; budget exceeded: <which>>
  - decision `<n>` `<sha>` (`<persona>`)
  - taken as recommended: `<what>` (autopilot)
- **D. Slice review:** map `<path>` (`<sha>`); done `<PASS | PASS after <sha> | standing: <checks>>`; mutation `<<n> mutants, <c> caught, <s> survived<, <h> of the caught by a hang><, <k> not counted><, <m> not run (the 900 s budget)> | not run (<why>)>`; reviewers `<initials>`; r0 `<C/H/M/L>`<; walk `<pass>/<fail>/<not reachable>`>; cold `<<n> confirmed, <m> verify | PASS>`<; r1 fix `<sha>` → `<C/H/M>` (reg `<r>`, pre `<p>`<, first `<f>`>)><; fixes builders `<n>` opus `<m>`><; r2 fix `<sha>` gate PASS; last `<C/H/M>`><; owed `<n>`>; standing `<C/H/M>`<; auto r<i> …, as the C line>; records `<sha>`; audit `<as the C line>`; data `<unchanged | CHANGED | not named>`
- **E. Delivery:** CI `<present | added <sha>>`; pushed `<sha>`; PR `<#>`; checks `<CI green <sha> | CI red r<i>: <jobs> | CI no result>`<; ci r<i> fix `<sha>`><; screens — states fix `<sha>`><; baselines `<sha>` (`<c>` changed, `<n>` new, `<r>` removed)>; issues `<#…>` (M `<m>`, deferred `<x>`); deferrals `<n>` listed; Lows `<n>` in body; ext r1 `<n>`c: fix `<f>` (`<sha>`), decline `<d>`, defer `<x>`; r2 …; `<clean r<i> | cap: <open>>`<; last `<C/H/M>`<; auto r<i> …, as the C line>>; consults `<n>`; cost `$<n><, not covering <id> (no transcript)> | not measured: <why>`; audit `<audit commit <sha> | audit commit none | audit sync FAILED: <reason> | not configured | off><; withheld: <session…>>`
  - Resumed <date> at <step>, session `<id>`, transcript `<kept | MISSING: <why> | not checked (audit off)>`
```

**5. Report as visible text after every step, then continue.** State
what was detected, why it routed where it did, and what got produced.
The report is text in the reply, never only a thinking summary: a stage
whose summary lives in a thinking block has reported nothing, and the
owner sees a run of questions with no account of what they decided. When
an owner's answer asks for an explanation before choosing ("explain the
options first"), the next reply is that explanation as text, and the
question comes after it, in its own turn. Then:
- **If step 3 found a next row** (there's more to do for the current
  unit): name it in the report and continue to it in this same
  conversation, looping back to step 2 for the now-current state (don't
  re-run step 1). Ask whether to continue only when the next row needs an
  owner decision to start (a destination, a
  sandbox stop) or the owner has asked to be asked; re-inspection is
  free, and a question that buys nothing is the one the owner stops
  answering.
  After a backward route the next step is always the same one: return to
  step 2 and re-inspect, now that the owner's revision is in place,
  without asking. Name that and nothing past it — not the row the
  re-inspection might land on, not the artifacts it might call for, not
  the stages the unit will pass through again. The report of a backward
  route is the one routed destination, why it was routed there and what
  the owner produced. When one invalidating fact leaves the same
  mechanical repair in several documents (a changed limit that the
  requirement, the slice and the story all quote), log one backward entry
  per owner, run the owners in sequence, each through its own `Skill`
  call, report once at the end, and prompt once if a prompt is due at
  all.
- **If the step was the planning pull request row**: the report is the
  pull request, the size line and what was taken as recommended, and
  the flow stops there. Don't start the chunk loop, don't ask whether
  to: the owner's merge is the answer.
- **If the current unit just reached the terminal row** (its slice is
  designed, its runtime-safety criteria are filled, its screen is designed
  and its accessibility criteria filled if it's UI-touching, the project
  has a stack to build on, and `tdd-coach:tdd-implementation-lite` has produced
  working, tested code for it, reviewed chunk by chunk by `code-reviewer`
  and a smoke run, held to the Definition of Done and reviewed once whole
  by every applicable reviewer inside the chunk loop, and delivered as a
  pull request): don't
  propose anything further. Moving on to the next scope-map step's
  requirements or slicing before this one is implemented and reviewed would
  repeat the mistake this rule exists to prevent: deciding too much before
  anything's been built. If the user explicitly wants to start a different
  unit anyway, that's their call to make by asking directly — not something
  this skill offers.
