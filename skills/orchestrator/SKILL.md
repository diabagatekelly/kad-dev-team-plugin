---
name: orchestrator
description: Route a problem to whichever kad-dev-team persona/skill applies next, by inspecting what already exists (problem doc, scope map, requirements, slices) rather than the user having to name the right persona each time. Use when the user wants to move a problem forward and hasn't said which persona/skill to use, or says "what's next" / "keep going" on a problem already in progress — including when they guess at the next stage in passing or conditionally ("if the next step is the implementation, go ahead", "probably the security pass next"). A stage guessed at is not a skill named, and the implementation stage in particular reaches tdd-implementation (or tdd-implementation-lite) only through this skill's sandbox check and chunk loop (a design-readiness gate first, one implementer per chunk, a gate, one combined reviewer and one smoke run per commit, one fix round per scope, a Definition of Done and a slice review at the end, then delivery), under the implementation policy the user picks there, never by invoking either directly.
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
invokes requires it. **The one exception is the `tdd-coach:tdd-implementation`
row** — see "The chunk loop" below — which genuinely launches real async
`Agent` calls, the only place in this skill that does.

**Skip this skill** when the user already named what they want directly
("write an ADR for X," "audit the docs for staleness") — routing only
earns its keep when the user hasn't said which persona/skill applies and
you'd otherwise have to guess or ask them to pick. A stage the user
guesses at while asking to move forward ("if the next step is the
implementation, go ahead") is not that: they named what they expect, not
a skill, and the routing table decides. This matters most for
implementation, which `tdd-implementation` invoked directly would do
inline in the real tree with no sandbox check, no chunking, no gate and
no reviewers.

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

**1. Identify the target.** You're invoked with the artifacts directory as
a parameter, or not:
- **Given one** — that's the target. Skip straight to step 2. Don't
  second-guess it, don't search for a different one.
- **Not given one** — ask once, before doing anything else: "Where do this
  problem's artifacts already exist, or where should they be created if
  we're starting from scratch?" Whatever the user answers becomes the
  target for every persona this skill invokes on this problem, this
  session and any future one — record it nowhere except by virtue of the
  first artifact actually landing there. Never guess a location yourself
  and never search the project for one instead of asking — if it wasn't
  handed to you, ask.

**2. Inspect what already exists in the target directory** — cheap,
mechanical checks only, never a semantic read of full artifact prose:
- A problem framing doc (a file whose top heading is `# Problem: ...`)?
- Any `scope-map-*.md` files? If more than one, the current one is the
  highest-numbered file whose `## Status` says `Active` (not `Superseded
  by ...`).
- Any `requirements-*.md` files? Same Active/Superseded rule. Which unit
  (scope-map step, or "the problem" if there's no scope map) does the
  current one belong to?
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
  persona existed, an explicit not-authored-here placeholder)?
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
skipped for it.

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
| The current unit has a requirements-refinement doc but no slice yet | `product-slicer` (`vertical-slicing` + `acceptance-criteria`), using the requirements doc as the primary input for WHAT to slice — not re-deciding it |
| A slice exists for the current unit but hasn't been written up as a user story yet | `docs-writer:user-story-writeup` |
| The current unit's slice has been written up as a user story but has no design doc yet | `software-architect:architecture-design` for that slice |
| The slice has a design doc but its security criteria are still an unfilled placeholder | `devsecops-engineer:security-requirements` for that slice |
| The slice's security criteria are filled but its reliability criteria are still an unfilled placeholder | `devsecops-engineer:reliability-requirements` for that slice |
| The slice is UI-touching, its runtime-safety criteria are filled, and the project has no design-system artifact yet | `ux-designer:design-system` |
| The slice is UI-touching, its runtime-safety criteria are filled, a design-system exists, but this slice has no screen-design artifact yet | `ux-designer:screen-design` for that slice |
| The slice is UI-touching, has a screen-design artifact, but its accessibility criteria are still an unfilled placeholder | `accessibility-engineer:accessibility-review` for that slice |
| The slice is designed with its runtime-safety criteria filled (and, if UI-touching, its screen designed and its accessibility criteria filled), and the project has no stack yet | `software-architect:technology-bootstrap` for that slice |
| The slice has a design doc, its runtime-safety criteria are filled (and, if UI-touching, its screen designed and its accessibility criteria filled), the project has a stack, but the slice hasn't been implemented yet | `tdd-coach:tdd-implementation` for that slice |
| The slice has been implemented — `tdd-coach:tdd-implementation` has produced working, tested code for it | **Stop — see step 5.** Don't advance to the next scope-map step. |

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
writing the first failing test, which is `tdd-coach:tdd-implementation`'s
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
`tdd-implementation`'s own row — that's not a spine stage either, it's
part of how that one row does its job.

**`architecture-cartographer:map-query` is another inline advisor consult,
not a spine stage — it doesn't get its own row here either.**
`software-architect:architecture-design` consults it before writing a
design doc, at the structural level ("does a comparable module or
interface already exist"), the same inline, hand-control-straight-back
pattern that row already uses for its `devsecops-engineer` consult.
`tdd-coach:tdd-implementation` consults it again before writing each Test
List entry's code, at the implementation level ("does a comparable
function or helper already exist") — below `architecture-design`'s own
conceptual altitude, squarely inside what that row actually writes. Both
consults are instructed in the asking skill's own `SKILL.md`, not
something this file dispatches; nothing about routing changes because of
them. `architecture-cartographer:map-update` has its own wiring inside the
chunk loop below — see "The chunk loop."

**4. Execute exactly one routed step.** For every row except
`tdd-coach:tdd-implementation`, execute inline: invoke the skill the
trigger matched with the `Skill` tool (`kad-dev-team:<skill>`), passing the
target directory. Don't go looking for the persona's `AGENT.md`: it sits
outside the project, a read of it may be refused, and everything a routed
step needs from its persona is in that skill. Follow the skill directly —
this is live use, not a dry run: if it would ask the user something,
actually ask via `AskUserQuestion`.

**The arguments you pass say two things and nothing else about
mechanics**: where to save (the location resolved in step 1, so the skill
neither asks where nor invents a different location) and that any
question the skill's own procedure puts to the user goes through
`AskUserQuestion`, one question per call. The second is said to every
routed skill, including one that rarely asks: it changes how a question
is asked, never whether. Say nothing about other
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

**The `tdd-coach:tdd-implementation` row doesn't execute inline — it runs
the chunk loop below, every time, by default.** There is no separate "is
this slice worth it" judgment call here: no signal anywhere in this
roster's pipeline reliably predicts implementation risk, and inventing one
would be worse than having none. The cost is bounded by `product-slicer`
already keeping each unit at the smallest shippable slice and by the loop
building it one small commit at a time. If the user explicitly wants a
specific slice built without it, that's their call to make by saying so
directly; this skill doesn't offer a way to opt out on its own judgment.

**Which skill the implementer builds with is the user's call, asked once
per slice, after the sandbox check and before anything is launched.** The
question, its options and when to skip it are in step A.2 of "The chunk
loop" below. The policy chosen is written on the entry's A line; "not now"
stops here and gets its own entry later, as below.

**Append one entry to `orchestrator-log.md`, in the target directory,
every time this step runs — as soon as you've routed, before invoking the
routed skill.** A routed skill often stops partway to ask the user
something, so an entry left until the step finishes may never be written.
The same goes for any question you put to the user yourself about the
routed step, such as the sandbox question or the policy question, or
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
indented bullets below, never on the Artifact line.

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

### The chunk loop — the `tdd-coach:tdd-implementation` row's own procedure

Five steps, A to E, replacing the normal single inline execution for this
one row only. Every other row in the table is unaffected. The planning is
checked for readiness before anything is built; one implementer builds the
slice one chunk at a time, each chunk a commit on a slice branch; a
mechanical gate, one combined reviewer and one smoke run check every
chunk; each scope gets one fix round and a regressions-only re-review, no
more; the whole slice is held to a Definition of Done and reviewed once
more at the end; then the branch is pushed, a pull request opened, the
standing Mediums filed, and the external reviewer's comments triaged.
Nothing in it runs "until clean", nothing runs in the background, and
nothing is resumed by message to fix something: every build and every fix
is a fresh agent on a short context.

**Every launch below passes `model` explicitly on the `Agent` call**:
`"sonnet"` for every implementer and fixer, `"opus"` for every reviewer,
smoke agent, consult and the triage. An agent definition's `model:` line
is documentation; in practice the launch parameter is what decides.
Builders and fixers are launched with `maxTurns: 120`; the Definition of
Done fixer at D with `maxTurns: 160`.

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
reads them itself, and `rounds_record.py` (C.3) is the only thing that
parses one.

**Budget** (the A line records it; counted at every chunk boundary):
loop time 5 h, 2 reviewer launches per chunk, 1 fixer per scope plus 1
for regressions, 8 consults per slice, unless the owner's message named
other numbers. At each chunk boundary read the clock and the counts; when
one is exceeded, the flow ends there: the branch stays as it is, the C
line says `budget exceeded: <which>`, and step 5 says what is built. The
dollar figure is not estimated during the run; `cost_by_role.py` computes
it at E.

**A. Start.** In this order:

0. **Repository.** Inline with Bash: `git rev-parse --show-toplevel` from
   the target and `git remote get-url origin`. If the target is not
   inside a git repository, or the repository has no `origin`, write the
   A line as `flow not started: no repository` and route to
   `release-engineer:repo-bootstrap` as a backward route (its own entry),
   then stop at step 5. Nothing is asked first: a flow that cannot start
   should not cost the owner four answers. Never `git init`, `gh repo
   create` or push outside that skill.
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
   - Exit `1` (`settings`, `shell-secrets`, `read-secrets`, and `write` or
     `network` with the settings not yet in place): ask once, with
     `AskUserQuestion`, whether to write the block into this session's
     user settings file; on yes, run the same command with
     `--write-settings` added, no path. It merges only what it needs,
     prints what changed, and runs the checks again in the same call. If
     the probe lines still fail in that call, run the check once more
     without `--write-settings` as its own Bash command (the session reads
     the settings again between commands). If it prints `settings not
     written: the write ... was refused`, write exactly the content it
     prints between its marker lines to the path it names with the `Write`
     tool, then re-check. Never write without the question, never into a
     project's `.claude/`, never anything but the printed content.
   - Exit `2`, or the probes still failing after the settings are in: this
     platform cannot fence the agents. Ask once, with `AskUserQuestion`,
     one question: continue unsandboxed (the agents run with the session's
     normal permission prompts and whatever `Read(...)` deny rules the
     settings carry), or stop and run the session where a sandbox exists
     (WSL2 on Windows). On exit 2 the settings question, when asked, still
     offers `--write-settings`, which on this platform writes the deny
     rules only and never `sandbox.enabled` or `failIfUnavailable` (a
     session with those set and no backend refuses every command). This
     is a strong recommendation and a logged choice, never a hard stop:
     on "continue", the A line says `sandbox — none on <platform>; owner
     opted to continue unsandboxed`, and every later sandbox check in this
     flow is still run and still logged, as information. On "stop", write
     the A line with the failing checks and `flow not started`, report in
     step 5, and stop.
   - `env` or `worktreeinclude`: name the variables or files; unsetting
     the one and removing the pattern are the user's. Stop.
   - `write` or `network` failing with the settings already in place and
     the platform having a sandbox: the session is not sandboxed or
     something is open; report the line as printed, and stop.

   The check is not once per flow but before every launch: before each
   chunk's build (C.1), its reviewer and smoke agent (C.3), its fixer
   (C.4), a consult (C.5), the slice reviewers (D) and the triage (E). A
   `PASS` that turns into a `FAIL` between steps ends the flow the way a
   second gate failure does, unless the user opted out at A, in which
   case the later checks are logged and the flow continues.
2. **Questions, one per `AskUserQuestion` call, four separate calls at
   most, in this order: settings, sandbox, policy, delegation.** Never
   bundle two of them into one call, whatever the tool allows: a call
   carrying two questions is this rule broken. A question the owner's own
   message already answered is skipped (a plain "go ahead" answers none);
   the settings and sandbox questions exist only when A.1 raised them.
   - **Settings** and **sandbox**: as A.1 says.
   - **Policy**: heavy first as the recommended default, lite second,
     "not now" third, each with its one-line distinction: **heavy** builds
     every chunk with `tdd-coach:tdd-implementation` (the full loop: Test
     List, one test at a time, RED seen failing, the per-cycle
     `test-quality-review` self-check, the can-it-fail check); **lite**
     builds every chunk with `tdd-coach:tdd-implementation-lite` (tests
     before code, seen failing on their assertions, the suite green, one
     deliberate break caught, the loop between left to the model; about
     a quarter of heavy's cost on the first real slice for the same design
     quality). Skip it only when the owner's message named a policy by one
     of these words. "Not now" stops here and gets its own entry later.
   - **Delegation**: "May decisions that come up during the build be
     settled with the owning persona without asking you? Each is logged,
     committed under the persona's name, and you can overturn it." On
     yes, write `<target>/delegation-slice-<nnn>.md`: the owner's words,
     the date, the slice, what it covers (design decisions, security and
     reliability criteria, screen states, accessibility criteria) and
     what it never covers (scope, requirements, anything that changes a
     confirmed requirement: those stay backward routes to the owner).
     Skip the question when the owner's message already said it; write
     the file anyway. On no, write no file: a mid-build gap then stops the
     flow for the owner (C.5).
3. **Branch and base.** Inline with Bash: `git status --porcelain` on the
   target directory. Then `git switch -c slice-<nnn>-<slug>` from the
   current commit, the number from the slice file's name and the slug from
   its title, lower-case, hyphens. If any planning document is modified or
   untracked (the delegation file is), commit them now on this branch, by
   name, as `Planning: slice <nnn> ready for implementation`; this is the
   only planning commit the flow makes, and it exists so the gate's
   `--protect` checks have a committed version to compare with. Then
   `git rev-parse --short HEAD` is the **base**: every gate and every
   reviewer diff in this flow is computed against it or against the
   previous chunk's commit, so no baseline file is needed. Create the
   records directory. Nothing is pushed here.
4. **Design-readiness gate**, inline with Bash:

   ```
   python3 -I "${CLAUDE_SKILL_DIR}/scripts/readiness_check.py" --planning '<target directory>' --slice <nnn>
   ```

   Eight mechanical checks over the planning documents: every criterion
   quoted under a design component; every failure path homed; a number on
   every retry, wait, poll and give-up; security and reliability agreeing
   on shared failure paths; a mockup for every named state; no open
   question routed to the implementer; a "Kept for later slices" line; a
   failure-mode row for an external provider's unusable reply. Its last
   line is `readiness: PASS` or `FAIL`, with a `route:` line per failed
   check naming the persona. On FAIL, each failed check is a backward
   route (step 3's rule): write its own log entry naming the check and the
   document, run the named skill inline with the `Skill` tool (telling it
   which check failed and which document to revise in place), and when it
   returns run the gate again. Repeat until it passes; the chunk loop's
   entry stays open meanwhile and no builder is launched. Then write the
   A line: `readiness — PASS` when it passed first time, otherwise
   `readiness — PASS after <check> (entry <n>), <check> (entry <m>)`.

Write the A line now (format below), then go to B.

**B. Plan.** Launch one implementer, `kad-dev-team:tdd-coach:AGENT`,
`model: "sonnet"`, real async `Agent` call, no worktree isolation (the
slice branch in the real tree is the worktree, and one agent writes at a
time). Its task: invoke the policy's skill first, by name
(`kad-dev-team:tdd-implementation` or `kad-dev-team:tdd-implementation-lite`),
and follow its "The chunk plan" section: read the slice file, the design
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

**C. Chunks, one at a time.** For chunk k of n, in the plan's order:

1. **Build.** Sandbox check (as A.1; logged). Launch a fresh implementer,
   `kad-dev-team:tdd-coach:AGENT`, `model: "sonnet"`, `maxTurns: 120`,
   with: the policy's skill to invoke first, by name; the chunk's five
   plan lines verbatim; the report's path (its earlier chunk sections are
   the handover from whoever built them, and the code is in the tree); the
   slice documents by absolute path (a decision document a consult
   committed since the plan is one of them, nothing more); two lines
   carried word for word on every build task: that `orchestrator` reviews
   the result (so the skill's final review is skipped), and that chunks
   are committed (so the skill's "Committing a chunk" applies: the chunk
   ends with one commit whose subject is the chunk's title, the report
   section appended in the same commit, nothing pushed). Nothing about
   reviewers, other chunks' findings, scope rules, or the flow's state.
   Wait for it.

   **Stall rule.** If the agent returns at its turn cap, or returns saying
   it is not done, with no new commit on the branch (`git log --oneline
   <previous>..HEAD` is empty), send it one message with `SendMessage`:
   commit what passes its done check, report the rest as not built, stop.
   If it returns again with no commit, record the stall on the C line,
   leave the working tree as it is (discard nothing), and launch a fresh
   implementer for the same chunk with the stalled agent's report section
   as handover and one line saying the tree may hold uncommitted work from
   a previous attempt that it should read before writing. A second stall
   on the same chunk ends the flow: C line, step 5.
2. **Gate**, inline with Bash, on the chunk's commit range:

   ```
   python3 -I "${CLAUDE_SKILL_DIR}/scripts/validation_gate.py" --project '<project root>' --base '<previous commit>' --test-cmd '<the project'''s documented test command>' --allow '<each path from the chunk'''s Files line>' --allow '<records directory>/' --module-dir '<each module directory the design names>' --protect '<every other document in the target directory>' [--coverage]
   ```

   (`python -I` where that is the interpreter's name; every project path
   in single quotes; a quote inside a path as `'\''`.) `--base` is the
   commit before this chunk's first commit (the base at chunk 1, the
   previous chunk's last accepted commit after). It checks the full suite
   is green, the project's `typecheck` and `lint` scripts pass when the
   manifest has them, the change set is not empty, every `--protect`
   document is unchanged, and, with `--coverage` (pass it when the project
   runs on Node's test runner), coverage holds on the changed source. Its
   scope check is three-way: a changed file on the Files line or in the
   records directory is in scope; a file inside a design module but off
   the Files line is a **deviation**, printed on the `scope` line and
   recorded on the C line as `deviations <n>`, not a failure (the builder
   names it in its report section; nobody edits the plan entry); a file
   outside both is the `FAIL` that goes to the fixer. It also prints
   report-only `INFO` lines (comment density, files over 300 lines,
   functions over 40, lines at depth 4 or more); read them, log nothing
   from them, and let D act on the slice's figures. Save the output as
   the gate file. Read its last line; read the rest only on `FAIL`. On
   `FAIL`, hand the failing checks to a fresh fixer (`model: "sonnet"`,
   the policy's skill, its "Applying a fix handed back from review" path,
   the gate's output verbatim, chunks are committed), once; run the gate
   again on the fix's range with the same `--base`. A second `FAIL` ends
   the flow: the branch stays as it is, the C line says which checks
   failed, step 5 says what is built. Don't widen `--allow`, don't drop a
   `--protect`, don't fix it yourself.
3. **Review and smoke: two launches, never more.** Sandbox check. Then,
   in parallel, real async `Agent` calls, `model: "opus"`, each handed
   nothing of the flow's own state (no finding from the other, no
   severity, no escalation, nothing the user has been told, no "check
   whether X"):
   - **The combined reviewer**: `kad-dev-team:code-reviewer:AGENT`, told to
     invoke `kad-dev-team:code-review` first and follow its "Combined
     chunk review" paragraph: `code-review`, then `test-quality-review`,
     then `reliability-review` when the chunk's Touches line includes
     HTTP, storage or error handling, and **one** report in the shared
     finding format, Critical, High, Medium and `needs-decision` only, at
     most eight findings, ranked. It is handed the chunk's diff as a range
     (`<previous>..HEAD`, which it reads with `git diff`), the files the
     chunk touched (the report left out), the slice's criteria and design
     by absolute path, the Touches line, the report path
     `chunk-<k>-r0-review.md`, and the instruction to hand back counts and
     the path.
   - **The smoke agent**: `kad-dev-team:accessibility-engineer:AGENT` when
     Touches includes UI, else `kad-dev-team:tdd-coach:AGENT`. Its task:
     start the app the way the README (or, before a README exists, the
     project's manifest) says, wait for it to answer, drive the chunk's
     **Done when** through the real interface (the browser via the Chrome
     tools for UI, HTTP requests otherwise), stop the app and leave no
     process behind, and write `chunk-<k>-r0-smoke.md` in the shared
     finding format: a `## Result` of `PASS` and no findings, or one
     finding per thing that broke; an app that does not start is one
     Critical titled "the app does not start from the documented
     command". The accessibility agent additionally invokes
     `kad-dev-team:accessibility-review` in its "Smoke run" mode and checks
     the chunk's accessibility criteria on the built screen, in the same
     report. It is handed the Done when line, the criteria by path, the
     report path, and nothing else.

   Wait for both. Their hand-backs are the counts and the paths. Then,
   inline with Bash:

   ```
   python3 -I "${CLAUDE_SKILL_DIR}/scripts/rounds_record.py" --sidecar '<records dir>/rounds-slice-<nnn>.jsonl' --report '<review report>' --report '<smoke report>' --chunk <k> --round 0
   ```

   It writes one sidecar row per finding and prints the round's C-line
   fragment (`r0 <C/H/M> ... ; smoke PASS|<n> findings`) and one line per
   `needs-decision` finding. **Only its printed counts reach the log**:
   you never parse a report yourself, never tally severities by reading,
   and never write a script to do either.
4. **One fix round, then a regressions-only re-review.** If round 0
   raised any Critical, High, Medium or smoke finding (after C.5 for any
   `needs-decision`): sandbox check, then one fresh fixer (`model:
   "sonnet"`, `maxTurns: 120`, the policy's skill, its handed-back path,
   chunks are committed) with every finding of both reports verbatim, as
   the paths of the two report files to read plus the list of which
   findings in them are handed back (and the decision commit from C.5, if
   any); it commits, one commit per fix or one for the batch, its call,
   and appends a `Fix r1` line to the chunk's report section. Then the
   gate on the fix's range (`--base` the commit before the fix). Then the
   **re-review**: the same combined reviewer kind, `model: "opus"`, on
   the fix's diff only (`<before fix>..HEAD`) and the files it touched,
   with the report path `chunk-<k>-r1-review.md` and nothing of round 0;
   and the smoke agent again only when round 0's smoke report had
   findings (`chunk-<k>-r1-smoke.md`). Then:

   ```
   python3 -I "${CLAUDE_SKILL_DIR}/scripts/rounds_record.py" --sidecar '<sidecar>' --report '<r1 review>' [--report '<r1 smoke>'] --chunk <k> --round 1 --project '<project root>' --range '<before fix>..HEAD' --fix '<sha>' --fixer '<agent id>' --turns <n>
   ```

   It classifies each finding by hunk: **regression** when its line is
   inside the fix's diff (a smoke finding always is), **pre-existing**
   otherwise, and prints the `(reg <r>, pre <p>)` split and one
   `standing:` line per pre-existing Critical, High or Medium. Regressions
   go to a **second and last** fixer (a fresh launch, the same shape,
   `Fix r2` line), then the gate; the chunk is done: **no third review**.
   Pre-existing findings are never fixed in this scope: they stand. A
   standing Critical or High ends the flow before the next chunk (C line,
   step 5, the owner decides); standing Mediums go to the pull request
   body's "Standing" list at E. A round 0 with nothing to fix is clean
   and the chunk is done.
5. **A gap that stops a fix.** When a report rates a finding
   `needs-decision (<persona>)` (no planning document states the rule it
   would need), or the fixer's report says so of a finding it was handed,
   the decision is made before that fixer runs, or before the second one:
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
     <n> <sha> (<persona>)`, and pass the hash to the fixer. Consults
     count against the budget; one per persona per round.
   - **Without a delegation file**: launch the persona the same way; it
     hands back a recommendation and writes nothing (its skill says so).
     Write the C line with `needs-decision <persona>: <recommendation
     path>` and stop the flow for the owner at step 5; the owner's answer
     resumes it at this round.

   Nothing else goes to a persona mid-loop: no "apply this edit", no
   decision you reached yourself, no editing a planning document on a
   persona's behalf. If the persona refuses to write, the flow stops as
   in the second case.
6. **C line**, then the records commit (`Records: slice <nnn> chunk <k>`:
   the reports, gate files and sidecar), then the budget check, then the
   next chunk. Between launches the only thing you say to the user is one
   short paragraph per event, with the hashes; you never restate a
   finding, keep a digest, or narrate an agent's turns.

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
   (`maxTurns: 160`, the policy's skill, its handed-back path, chunks are
   committed). Then the gate on the fix's range, then the check again. A
   check still failing after that stands: README, typecheck, lint, code
   in strings and the persisted names are High (the flow stops for the
   owner before the reviewers); comment density, planning references, env
   defaults and padding are Medium (the pull request body's Definition of
   Done table). Only then:
3. **The six reviewers once.** Sandbox check. `model: "opus"`, in
   parallel, each handed the whole slice's diff as the range
   `<base>..HEAD` (the records directory and the map left out), the map
   diff, the slice documents by path, and its report path
   `slice-r0-<reviewer>.md`: `tdd-coach:test-quality-review`,
   `code-reviewer:code-review`, `software-architect:architecture-review`,
   `devsecops-engineer:security-review`,
   `devsecops-engineer:reliability-review`, and
   `accessibility-engineer:accessibility-review` only if the slice is
   UI-touching. Lows are allowed here and only here: they go to the pull
   request body under "Known Lows", grouped by theme, and are not filed.
   `rounds_record.py` with `--chunk D --round 0` on all the reports. Then
   one fix round exactly as C.4: one fixer for every Critical, High and
   Medium (and any `needs-decision` through C.5 first), the gate, a
   regressions-only re-review by the same reviewers on the fix's diff
   (`slice-r1-<reviewer>.md`), `rounds_record.py` with `--range`, a
   second and last fixer for the regressions, the gate, no third review;
   standing Criticals and Highs stop the flow before E, standing Mediums
   go to the body.
4. **The stranger test**, once, in D's last review round (round 1 when
   there was a fix round, round 0 otherwise, launched alongside that
   round's reviewers): the smoke agent (`accessibility-engineer` if
   UI-touching, else `tdd-coach`, `model: "opus"`) clones the repository
   into a fresh temporary directory (`git clone <project root> <tmp>` at
   the branch), follows the README and nothing else from clone to
   running, drives the slice's thin path once, removes the clone, and
   writes `slice-r<i>-smoke.md`. What it raises goes to that round's
   fixer (as a round-0 finding when it ran with round 0, as a regression
   when with round 1); a README that does not get a stranger to a running
   app is a High for `docs-writer:readme` again, inline, then the fixer's
   gate.
5. The D line; the records commit `Records: slice <nnn> review`.

**E. Delivery.** No question is asked in this step; the user decided on
2026-10-24 that the branch is pushed and the pull request opened without
one. **Nothing in this step runs in the background**: every command and
every launch is waited for, and the step ends in the same turn that
finishes its last action.

1. If D's fix rounds changed anything, `map-update` again and commit the
   map.
2. **CI.** If the repository has no continuous-integration configuration
   (no `.github/workflows/*.yml`, no equivalent for the host the remote
   names), invoke `release-engineer:ci-pipeline` inline with the `Skill`
   tool: it writes the workflow for the project's stack, mirroring the
   gate's commands (install with a frozen lockfile, typecheck, lint, the
   suite with its coverage gate), pinned action SHAs, least-privilege
   permissions, and commits it by name. If one exists, skip; a gate
   command the workflow does not run is a line in the report, not a change
   you make. An audit job that fails on a dependency advisory is a named
   fix for a fresh Sonnet fixer with `supply-chain-review`'s
   recommendation, then the gate; you edit no manifest or lockfile
   yourself.
3. **Push and pull request.** Invoke `release-engineer:delivery` inline
   with the `Skill` tool, telling it: the branch, the base, the report's
   path, the records directory and the sidecar, the Definition of Done
   results, and the tracker `user-story-writeup` recorded for this project
   (or that none is recorded). It pushes the branch, has
   `docs-writer:pr-writeup` write the body from the report (what was built
   chunk by chunk, decided gaps and decision commits, escalations, the
   Definition of Done table, the standing Mediums, the Known Lows grouped
   by theme, the model and tool provenance), opens the pull request
   against the default branch, files **each standing Medium** as one issue
   in the recorded tracker (title from the finding, body from its text,
   file and line, label `tech-debt` where the tracker has labels), **files
   no Low** (they stay in the body; the owner may ask for them later),
   edits the body so each standing Medium links its issue, and returns
   the pull request number and the issue numbers. With no tracker
   recorded, the standing Mediums stay listed in the body and the E line
   says so; nothing is asked.
4. **External review triage, until nothing to fix, capped at five
   rounds.** `delivery` waits for the pull request's checks to finish
   (polling `gh pr checks` and the reviews, up to the bound its skill
   states), then reads every review comment not left by this flow. If
   there are any: sandbox check; launch `kad-dev-team:code-reviewer:AGENT`,
   `model: "opus"`, to invoke `code-reviewer:external-review-triage` with
   the pull request number, the slice documents by path, the records
   directory (the plugin's own findings on the same files) and a report
   path; it returns a verdict per comment: **fix**, **decline** with the
   reason, or **defer**. Fixes go to a fresh fixer as in C.4 (one batch,
   commits), then the gate on the fix's range, then `delivery` pushes,
   posts each decline's reason as a reply on its comment and files each
   deferral as an issue. The push brings the external reviewer back; its
   new comments on the fix are the next round, through the same triage,
   until a round has no comment to fix or round 5 is done. Comments that
   arrive after that are the user's. Every comment and verdict goes to
   the sidecar with `"chunk": "pr"`; the comments file is committed with
   the records.
5. **Cost.** Inline with Bash:
   `python3 -I "${CLAUDE_PLUGIN_ROOT}/evals/tools/cost_by_role.py" --project '<project root>'`
   over the session transcripts audit mode kept (when audit mode is off it
   says so and the E line records `cost not measured`). Its total goes on
   the E line.
6. **Audit sync.** When `KAD_AUDIT_REPO` is set and `<project>/audit-docs/`
   exists, run
   `python3 -I "${CLAUDE_SKILL_DIR}/scripts/audit_sync.py" --project '<project root>' --slice <nnn>`
   inline: it copies the planning documents, the log, the report, the map,
   the records directory and the sidecar into the audit repository's slice
   folder, refuses on a credential-shaped string, commits there and
   pushes. Its last line names the audit commit.
7. The E line, in this same turn, then step 5 below: report what happened
   at each of the five steps, with the pull request and issue numbers, the
   standing findings if any, and the open external comments if the cap was
   hit; the slice has reached the terminal row.

**Pausing and resuming.** On a context clear, a rate limit, a session end
or an owner's "hand off" mid-loop, before anything else write
`<records dir>/handoff-slice-<nnn>.md`: the A–E state (which step, which
chunk, which round), the next action, the standing list, the budget
counters (start time, reviewer launches, consults), the environment facts
a successor needs (test command, module directories, records directory,
whether the owner opted out of the sandbox), and the owner's standing
directions; commit it with the records; and write a memory pointer to it.
On invocation with a handoff file present for the slice, resume from it:
no new A step, no second policy question; append `Resumed <date> at
<step>` as an indented line under the entry's last line and continue at
the step the file names. The handoff file is removed by the records commit
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
- **A. Start:** sandbox — `<PASS (<platform>) | none on <platform>; owner opted to continue unsandboxed | FAIL: <checks>; flow not started | flow not started: no repository>`; policy — `<heavy | lite>`; delegation — `<file path | none>`; budget — `5h, 2 reviews/chunk, 1 fix/scope (+1 regressions), 8 consults`; branch — `<name>`; base — `<sha>`<, planning commit `<sha>`>; records — `<dir>`; readiness — `<PASS | PASS after <check> (entry <n>), …>`
- **B. Plan:** `<k>` chunks — `<title 1>`; `<title 2>`; … (`<report path>`, commit `<sha>`); modules — `<dir>`, `<dir>`
- **C. Chunk <k>/<n>:** `<title>`; sonnet `<turns>`t `<min>`m; commits `<sha…>`; gate `<PASS | PASS after <sha> | FAIL: <checks>; ended>`; deviations `<n>`; review `<co tq [re]>` r0 `<C/H/M>`< nd `<n>`>; smoke `<PASS | <n> findings>`<; r1 fix `<sha>` → `<C/H/M>` (reg `<r>`, pre `<p>`)><; r2 fix `<sha>` gate PASS>; standing `<C/H/M>`; budget `<h>`h `<reviews>`r `<consults>`c; records `<sha>`<; stall: <relaunched | ended>><; budget exceeded: <which>>
  - decision `<n>` `<sha>` (`<persona>`)
- **D. Slice review:** map `<path>` (`<sha>`); done `<PASS | PASS after <sha> | standing: <checks>>`; reviewers `<initials>`; r0 `<C/H/M/L>`; stranger `<PASS | <n> findings>`<; r1 fix `<sha>` → `<C/H/M>` (reg `<r>`, pre `<p>`)><; r2 fix `<sha>` gate PASS>; standing `<C/H/M>`; records `<sha>`
- **E. Delivery:** CI `<present | added <sha>>`; pushed `<sha>`; PR `<#>`; issues `<#…>` (M `<m>`, deferred `<x>`); Lows `<n>` in body; ext r1 `<n>`c: fix `<f>` (`<sha>`), decline `<d>`, defer `<x>`; r2 …; `<clean r<i> | cap: <open>>`; cost `$<n> | not measured`; audit `<sha | not configured>`
  - Resumed <date> at <step>
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
  owner decision to start (the implementation policy, a destination, a
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
- **If the current unit just reached the terminal row** (its slice is
  designed, its runtime-safety criteria are filled, its screen is designed
  and its accessibility criteria filled if it's UI-touching, the project
  has a stack to build on, and `tdd-coach:tdd-implementation` has produced
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
