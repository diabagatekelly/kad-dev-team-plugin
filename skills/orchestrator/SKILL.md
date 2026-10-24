---
name: orchestrator
description: Route a problem to whichever kad-dev-team persona/skill applies next, by inspecting what already exists (problem doc, scope map, requirements, slices) rather than the user having to name the right persona each time. Use when the user wants to move a problem forward and hasn't said which persona/skill to use, or says "what's next" / "keep going" on a problem already in progress — including when they guess at the next stage in passing or conditionally ("if the next step is the implementation, go ahead", "probably the security pass next"). A stage guessed at is not a skill named, and the implementation stage in particular reaches tdd-implementation (or tdd-implementation-lite) only through this skill's sandbox check and chunk loop (one implementer per chunk, a gate and reviewers per commit, delivery at the end), under the implementation policy the user picks there, never by invoking either directly.
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

Two rules for the backward step: upstream artifacts are revised by
superseding, never by editing in place (`scope-map`, `requirements-refinement`,
and `adr` all number sequentially for this reason), and once it completes,
return to step 2 and re-inspect from scratch — a superseded scope map can
move the forward position by more than one row.

That "return to step 2" instruction governs your own next invocation once
the backward step actually completes — it is not something to narrate now.
When reporting a backward route (step 5), state the single routed
destination, why it was routed there, what the owner produced, and the
offer to re-inspect; don't add what re-inspection will find or where the
forward position might land once it resolves. Describing that round trip is
the same chaining step 5 already forbids, just spelled backward instead of
forward.

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
reached. Hand off to them only if the user asks. `test-quality-review` and
`code-reviewer` also run as the chunk loop's reviewers, inside
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
actually ask via `AskUserQuestion`. Tell it explicitly where to save its output — the
location resolved in step 1. It should not ask where to save or invent a
different location; you already resolved that. Produce the real artifact
and save it there, using that persona's own filename/heading convention —
once the skill's own procedure gets there. Routing doesn't hurry it: a
skill whose first response is questions asks them and stops, even here,
and the artifact comes in a later turn. Don't fill the skill's questions
with answers inferred from the repository to reach the artifact sooner.

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
invocation, appended, never edited or reordered — a prior entry being
wrong gets a new entry noting the correction, the same append-only
discipline `scope-map`/`requirements-refinement`/`adr` already use for
their own artifacts, applied here to a process record instead of a
decision record. Each entry:

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
  otherwise none", and no outcome appended to the entry afterwards. If
  the skill decides none is needed, it records that where its own
  procedure says, and a later entry can say so;
- `user-story-writeup`, which asks where this project files stories: the
  path a locally filed story takes under the target directory, with a
  parenthetical that the skill may file it elsewhere. Where it then went
  is a new correcting entry, never an edit of this one; "to be decided by
  the skill" names no path.

For a backward route (the step 3 rule that supersedes the table), log it
the same way, naming which artifact got superseded and why, not just the
forward destination.

### The chunk loop — the `tdd-coach:tdd-implementation` row's own procedure

Five steps, A to E, replacing the normal single inline execution for this
one row only. Every other row in the table is unaffected. One implementer
builds the slice one chunk at a time, each chunk a commit on a slice
branch; a mechanical gate and separate reviewers check every commit before
the next chunk starts; the whole slice is reviewed once more at the end;
then the branch is pushed, a pull request opened, the leftovers filed, and
the external reviewer's comments triaged. Nothing in it runs "until clean"
without a cap, and nothing is resumed by message to fix something: every
build and every fix is a fresh agent on a short context, because a
long-lived implementer re-reading its own growing context was where the
previous flow's cost went.

**Every launch below passes `model` explicitly on the `Agent` call**:
`"sonnet"` for every implementer and fixer, `"opus"` for every reviewer
and the triage. An agent definition's `model:` line is documentation; in
practice the launch parameter is what decides.

**Every launch below names a file for the agent's report** and tells the
agent to hand back counts and the path, not the report. The reports go
under `$KAD_AUDIT_DIR/reviews/<slice>/` when audit mode is on
(`KAD_AUDIT=1`), else under `<project>/.git/kad-audit/reviews/<slice>/`;
one file per launch, named `chunk-<k>-r<i>-<reviewer>.md` (`slice-r<i>-…`
at D, `pr-r<i>-…` at E). You open one of those files only to decide
something; the fixer reads them itself.

**A. Start.** In this order, and the sandbox check comes before any
question:

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
     settings carry, which the write above still adds), or stop and run
     the session where a sandbox exists (WSL2 on Windows). This is a
     strong recommendation and a logged choice, never a hard stop: on
     "continue", the A line says `sandbox — none on <platform>; owner
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
   chunk's build (C.1), its reviewers (C.3), its fixer (C.4), the slice
   reviewers (D) and the triage (E). A `PASS` that turns into a `FAIL`
   between steps ends the flow the way a second gate failure does, unless
   the user opted out at A, in which case the later checks are logged and
   the flow continues.
2. **Policy**, one `AskUserQuestion`, heavy first as the recommended
   default, lite second, "not now" third, each with its one-line
   distinction: **heavy** builds every chunk with
   `tdd-coach:tdd-implementation` (the full loop: Test List, one test at a
   time, RED seen failing, the per-cycle `test-quality-review` self-check,
   the can-it-fail check); **lite** builds every chunk with
   `tdd-coach:tdd-implementation-lite` (tests before code, seen failing on
   their assertions, the suite green, one deliberate break caught, the
   loop between left to the model; about a quarter of heavy's cost on the
   first real slice for the same design quality). Skip the question only
   when the user's own message named a policy by one of these words; a
   plain "go ahead" names none. "Not now" stops here and gets its own
   entry later.
3. **Branch.** Inline with Bash: `git status --porcelain` on the target
   directory. Then `git switch -c slice-<nnn>-<slug>` from the current
   commit, the number from the slice file's name and the slug from its
   title, lower-case, hyphens. If any planning document is modified or
   untracked, commit them now on this branch, by name, as `Planning:
   slice <nnn> ready for implementation`; this is the only planning commit
   the flow makes, and it exists so the gate's `--protect` checks have a
   committed version to compare with. Then `git rev-parse --short HEAD` is
   the **base**: every gate and every reviewer diff in this flow is
   computed against it or against the previous chunk's commit, so no
   baseline file is needed. Nothing is pushed here.
4. **Audit location.** Pick the reviews directory named above and create
   it. Record on the A line.

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
`map-query`; write the chunk plan under `## Chunk plan` in
`<target>/implementation-report-slice-<nnn>.md` (create the file with the
report's heading if it does not exist) and stop, building nothing. One
line saying the orchestrator reviews the result. Nothing about chunks
being committed yet: this agent commits nothing. Wait for it.

When it returns, check the plan mechanically and nothing else: the file
has a `## Chunk plan` heading with two to eight chunks; every chunk has a
Title, Delivers, Files, Done when and Touches line; every Delivers names
at least one criterion (an identifier, or the criterion's text quoted when
the document numbers nothing) and every Files at least one path; no
path is outside the slice's module directories as the design names them,
the project's test directory, the root configuration files, or the report.
A plan that fails a check goes back once to a fresh planner with the
failing check named, as a new launch with the same task; a second failure
ends the flow with the B line saying why. You do not edit the plan, reorder
it or judge its chunking: the plan is the implementer's. Commit the plan,
by name, as `Plan: slice <nnn> in <k> chunks`. Write the B line: the chunk
titles in order.

**C. Chunks, one at a time.** For chunk k of n, in the plan's order:

1. **Build.** Sandbox check (as A.1; logged). Launch a fresh implementer,
   `kad-dev-team:tdd-coach:AGENT`, `model: "sonnet"`, with: the policy's
   skill to invoke first, by name; the chunk's five plan lines verbatim;
   the report's path (its earlier chunk sections are the handover from
   whoever built them, and the code is in the tree); the slice documents
   by absolute path; two lines carried word for word on every build task:
   that `orchestrator` reviews the result (so the skill's final review is
   skipped), and that chunks are committed (so the skill's "Committing a
   chunk" applies: the chunk ends with one commit whose subject is the
   chunk's title, the report section appended in the same commit, nothing
   pushed). Nothing about reviewers, other chunks' findings, or the flow's
   state. Wait for it.

   **Stall rule.** The agent definition caps the turns. If the agent
   returns at its cap, or returns saying it is not done, with no new
   commit on the branch (`git log --oneline <previous>..HEAD` is empty),
   send it one message with `SendMessage`: commit what passes its done
   check, report the rest as not built, stop. If it returns again with no
   commit, record the stall on the C line, leave the working tree as it is
   (discard nothing), and launch a fresh implementer for the same chunk
   with the stalled agent's report section as handover and one line saying
   the tree may hold uncommitted work from a previous attempt that it
   should read before writing. A second stall on the same chunk ends the
   flow: C line, step 5.
2. **Gate**, inline with Bash, on the chunk's commit range:

   ```
   python3 -I "${CLAUDE_SKILL_DIR}/scripts/validation_gate.py" --project '<project root>' --base '<previous commit>' --test-cmd '<the project'''s documented test command>' --allow '<each path from the chunk'''s Files line>' --allow '<report path>' --protect '<every other document in the target directory>' [--coverage]
   ```

   (`python -I` where that is the interpreter's name; every project path
   in single quotes; a quote inside a path as `'\''`.) `--base` is the
   commit before this chunk's first commit (the base at chunk 1, the
   previous chunk's last accepted commit after). It checks the full suite
   is green, the change set is not empty, every changed file is inside an
   `--allow` entry, every `--protect` document is unchanged, and, with
   `--coverage` (pass it when the project runs on Node's test runner),
   coverage holds on the changed source. Read its last line; read the rest
   only on `FAIL`. A file the implementer added outside the Files line and
   named as a deviation in its report section is still a scope failure
   here: the plan is the contract, and the fixer below decides whether the
   file moves or the deviation stands by adding it to the plan entry in
   the report (the one edit to the plan anyone makes, recorded in its fix
   commit). On `FAIL`, hand the failing checks to a fresh fixer
   (`model: "sonnet"`, the policy's skill, its "Applying a fix handed back
   from review" path, the gate's output verbatim, chunks are committed),
   once; run the gate again on the fix's range with the same `--base`. A
   second `FAIL` ends the flow: the branch stays as it is, the C line says
   which checks failed, step 5 says what is built. Don't widen `--allow`,
   don't drop a `--protect`, don't fix it yourself.
3. **Validate.** Sandbox check. Then, in parallel, real async `Agent`
   calls, `model: "opus"`, each handed: the skill to invoke first; the
   chunk's diff as a range (`<previous>..HEAD`, which the reviewer reads
   with `git diff`) and the files it touched, the report left out; the
   slice's criteria and design by absolute path; the report file path to
   write to and the instruction to hand back counts and the path; and
   nothing of the flow's own state (no finding from another reviewer, no
   severity, no escalation, nothing the user has been told, no "check
   whether X"). Which reviewers, from the chunk's Touches line:
   `tdd-coach:test-quality-review`, `code-reviewer:code-review` and
   `software-architect:architecture-review` always;
   `devsecops-engineer:security-review` when Touches names adapter or
   secret, HTTP or storage; `devsecops-engineer:reliability-review` when
   it names HTTP, storage or error handling;
   `accessibility-engineer:accessibility-review` when it names UI (it
   drives the built screen, as its skill says). No map diff per chunk:
   `map-update` runs once at D and the architecture reviewer reads the
   diff. Wait for all of them. Their hand-backs are the counts and the
   paths; append each reviewer's Low lines to the report's `### Lows`
   list (create it under the chunk's section) with `file:line` and the
   reviewer's name, one line each. That is your one write to the report.
4. **Fix rounds, until clean, capped at five.** Round 0 is the validation
   above. If it raised any Critical, High or Medium: sandbox check, then
   one fresh fixer (`model: "sonnet"`, the policy's skill, its
   handed-back path, chunks are committed) with every Critical, High and
   Medium finding of this round, verbatim (reviewer, severity, file, line,
   the finding's text), as the paths of the reviewer files to read plus
   the list of which findings in them are handed back; it commits, one
   commit per fix or one for the batch, its call, and appends a `Fix r<i>`
   line to the chunk's report section. Then the gate on the fix's range,
   then every reviewer that ran on this chunk (not only the ones that
   raised findings: the fix one asked for is what another objects to),
   `model: "opus"`, on the files the fix touched and the fix's diff, with
   the fix's own report paths and nothing of the earlier rounds. Before
   logging what they raise, classify each new Critical, High and Medium
   mechanically: **regression** if its line is inside a hunk of the fix's
   diff (`git diff <before fix>..HEAD -U0` names the ranges),
   **pre-existing** otherwise. Record every finding of every round in the
   sidecar `<reviews dir>/rounds-slice-<nnn>.jsonl`, one JSON object per
   line: `{"chunk": k, "round": i, "reviewer", "severity", "title",
   "file", "line", "class": "regression|pre-existing", "fix": "<sha>" or
   null, "fixer": "<agent id>", "turns": n}`. A round that raises no
   Critical, High or Medium is clean: the chunk is done. Otherwise the new
   findings are the next round's batch, through the same fixer launch,
   gate and re-review, until a clean round or until round 5 has been
   re-reviewed. After the cap: a standing Critical or High ends the flow
   before the next chunk (C line, step 5, the user decides); a standing
   Medium is filed at E, never carried silently.
5. **C line**, then the next chunk. Between launches the only thing you
   say to the user is one short paragraph per event, with the hashes; you
   never restate a finding, keep a digest, or narrate an agent's turns.

**D. Slice review.** When the last chunk is done: sandbox check; then
`architecture-cartographer:map-update` for real, inline, against the tree
(this run's output replaces the project's persisted map; if the skill has
no extractor for the project's language it says so and the reviewers below
go without a map diff, and you do not write an extractor). Commit the map
by name as `Map: slice <nnn>`. Then all six reviewers, `model: "opus"`,
in parallel, each handed the whole slice's diff as the range
`<base>..HEAD` (the report and the map left out), the map diff, the slice
documents by path, and a report path; `accessibility-review` only if the
slice is UI-touching. Lows to the report's `### Lows`. Then the fix
rounds exactly as C.4, with all six re-running on each fix's files,
until clean, capped at five; a standing Critical or High after the cap
ends the flow before E; standing Mediums are filed at E. The D line.

**E. Delivery.** No question is asked in this step; the user decided on
2026-10-24 that the branch is pushed and the pull request opened without
one.

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
   you make.
3. **Push and pull request.** Invoke `release-engineer:delivery` inline
   with the `Skill` tool, telling it: the branch, the base, the report's
   path, the reviews directory, and the tracker `user-story-writeup`
   recorded for this project (or that none is recorded). It pushes the
   branch, has `docs-writer:pr-writeup` write the body from the report
   (what was built chunk by chunk, decided gaps, escalations, the Lows and
   standing Mediums left, the model and tool provenance), opens the pull
   request against the default branch, files each Low and each standing
   Medium as one issue in the recorded tracker (title from the finding,
   body from its text, file and line, label `tech-debt` where the tracker
   has labels), links them from the pull request, and returns the pull
   request number and the issue numbers. With no tracker recorded, the
   Lows and Mediums stay listed in the pull request body and the E line
   says so; nothing is asked.
4. **External review triage, until nothing to fix, capped at five
   rounds.** `delivery` waits for the pull request's checks to finish
   (polling `gh pr checks` and the reviews, up to the bound its skill
   states), then reads every review comment not left by this flow. If
   there are any: sandbox check; launch `kad-dev-team:code-reviewer:AGENT`,
   `model: "opus"`, to invoke `code-reviewer:external-review-triage` with
   the pull request number, the slice documents by path, the reviews
   directory (the plugin's own findings on the same files) and a report
   path; it returns a verdict per comment: **fix**, **decline** with the
   reason, or **defer**. Fixes go to a fresh fixer as in C.4 (one batch,
   commits), then the gate on the fix's range, then `delivery` pushes,
   posts each decline's reason as a reply on its comment and files each
   deferral as an issue. The push brings the external reviewer back; its
   new comments on the fix are the next round, through the same triage,
   until a round has no comment to fix or round 5 is done. Comments that
   arrive after that are the user's. Every comment and verdict goes to
   the sidecar with `"chunk": "pr"`.
5. **Audit sync.** When `KAD_AUDIT_REPO` is set and `<project>/audit-docs/`
   exists, run
   `python3 -I "${CLAUDE_SKILL_DIR}/scripts/audit_sync.py" --project '<project root>' --slice <nnn>`
   inline: it copies the planning documents, the log, the report, the map,
   the reviews directory and the sidecar into the audit repository's slice
   folder, refuses on a credential-shaped string, commits there and
   pushes. Its last line names the audit commit.
6. The E line.

Then step 5 below: report what happened at each of the five steps, with
the pull request and issue numbers, the standing findings if any, and the
open external comments if the cap was hit; the slice has reached the
terminal row.

**This row's `orchestrator-log.md` entry needs sub-entries for all five
steps, one line per chunk under C, not the one-line form every other row
gets.** Terse pointers, not prose: hashes, counts and file names locate
everything else, the sidecar holds the findings, and the transcripts audit
mode keeps are the complete record. Reviewer initials: `tq` test-quality,
`co` code, `ar` architecture, `se` security, `re` reliability, `ac`
accessibility.

```markdown
## <n>. <date> — slice ready for implementation

**Routed to:** chunk loop
**Artifact:** see sub-entries below
- **A. Start:** sandbox — `<PASS (<platform>) | none on <platform>; owner opted to continue unsandboxed | FAIL: <checks>; flow not started>`; policy — `<heavy | lite>`; branch — `<name>`; base — `<sha>`<, planning commit `<sha>`>; reviews — `<dir>`
- **B. Plan:** `<k>` chunks — `<title 1>`; `<title 2>`; … (`<report path>`, commit `<sha>`)
- **C. Chunk <k>/<n>:** `<title>`; sonnet `<turns>`t `<min>`m; commits `<sha…>`; gate `<PASS | PASS after <sha> | FAIL: <checks>; ended>`; reviewers `<initials>`; r0 `<C/H/M/L>`; r1 fix `<sha>` → `<C/H/M/L>` (reg `<r>`, pre `<p>`); r2 …; `<clean r<i> | cap: <standing>>`<; stall: <relaunched | ended>>
- **D. Slice review:** map `<path>` (`<sha>`); reviewers `<initials>`; r0 `<C/H/M/L>`; r1 fix `<sha>` → `<C/H/M/L>` (reg `<r>`, pre `<p>`); …; `<clean r<i> | cap: <standing>>`
- **E. Delivery:** CI `<present | added <sha>>`; pushed `<sha>`; PR `<#>`; issues `<#…>` (L `<n>`, M `<m>`, deferred `<x>`); ext r1 `<n>`c: fix `<f>` (`<sha>`), decline `<d>`, defer `<x>`; r2 …; `<clean r<i> | cap: <open>>`; audit `<sha | not configured>`
```

Each line is appended as its step completes, never edited afterwards; a
correction is a new indented line under it, as everywhere in this log.

**5. Report, then ask whether to continue — never chain silently.** State
what was detected, why it routed where it did, and what got produced.
Then:
- **If step 3 found a next row** (there's more to do for the current
  unit): name what that next step would be and ask whether to continue to
  it now, in this same conversation. If yes, loop back to step 2 for the
  now-current state — don't re-run step 1. If no, stop and wait.
  After a backward route the next step is always the same one: return to
  step 2 and re-inspect, now that the owner's revision is in place. Name
  that and nothing past it — not the row the re-inspection might land on,
  not the artifacts it might call for, not the stages the unit will pass
  through again. The report of a backward route is the one routed
  destination, why it was routed there, what the owner produced, and the
  offer to re-inspect.
- **If the current unit just reached the terminal row** (its slice is
  designed, its runtime-safety criteria are filled, its screen is designed
  and its accessibility criteria filled if it's UI-touching, the project
  has a stack to build on, and `tdd-coach:tdd-implementation` has produced
  working, tested code for it, reviewed chunk by chunk and once whole by
  `code-reviewer` and every other applicable reviewer inside the chunk
  loop, and delivered as a pull request): don't
  propose anything further. Moving on to the next scope-map step's
  requirements or slicing before this one is implemented and reviewed would
  repeat the mistake this rule exists to prevent: deciding too much before
  anything's been built. If the user explicitly wants to start a different
  unit anyway, that's their call to make by asking directly — not something
  this skill offers.
