---
name: accessibility-review
description: Verify whether a UI-touching slice's rendered artifact — a screen-design mockup today, real built markup once code exists — actually conforms to accessibility standards, rather than merely being designed to make conformance possible. Drives the artifact (keyboard tab-through, computed contrast, DOM structure) rather than only reading its markup. Produces a severity-ranked findings report and turns the result into the slice's accessibility acceptance criteria. Use once a UI-touching slice has a screen-design artifact and its accessibility criteria are still an unfilled placeholder, or whenever a rendered screen needs an accessibility pass.
---

# Accessibility Review

## What you're producing

Four modes, told apart by what the task hands you. **Design time** (a
screen-design mockup, the slice's placeholder still unfilled): the full
review below and the slice's accessibility criteria. **Smoke run** (the
orchestrator's chunk loop hands you a chunk's Done when and a report path):
the "Smoke run" section below, nothing else. **Slice review** (the whole
built slice's diff at the chunk loop's D step): the full review below on
the built screens, every state, in the shared report format, no criteria
rewritten. **Criteria walk** (the chunk loop's D step hands you the
slice's criteria by path, the start command and a report path ending in
`-walk.md`): the "Criteria walk" section below, nothing else.

**Every mode that starts the app starts it through the launcher the task
hands you** (`scratch_run.py`, by path, with a scratch folder): the
app's data paths given explicitly inside that folder, `HOME` pointed
there, made-up data (the project's fixture or data you build), the
project's fake credential tool or a disposable store, never the owner's
login credential store, not even to read, no provider connection started, and
the folder removed after (`scratch_run.py --clean`). You never open the
owner's data directory; the launcher refuses a path outside the folder,
and the orchestrator hashes the real data around your launch. Two smoke
runs once started the app on the owner's real data and credential store,
and nothing in the text then said not to (incident 10).

At design time, two things from one pass: a findings report on the artifact
in front of you, and the slice's actual accessibility acceptance criteria —
filling the placeholder that has been sitting in its acceptance criteria
until now.
Nobody could write a real, testable accessibility criterion before there
was a rendered screen to check it against; this is the first point in the
roster's spine where that becomes possible; it's not the last, since real
built code deserves this same pass again later.

**Your file is the artifact, and the only document you edit.** The report
and the criteria are one document, `accessibility-slice-<nnn>.md`, in the
target directory (or its `visual-ux/`, next to the screen design). You
may replace the slice's accessibility placeholder line with a one-line
pointer to it and nothing more: not the story (`docs-writer`'s, re-synced
by `user-story-writeup` on the next re-inspection), not another
criterion, not any other section or document, whatever the invoking
instructions say. A functional criterion that would have to be weakened
to resolve a finding is a finding for `product-slicer` under your Open
questions (see the escalation rules below), routed by the orchestrator,
never an edit.

The test for whether a criterion you write passes: could someone check the
finished slice against it without asking you what you meant? "The screen is
accessible" fails that test the same way "handled securely" fails
`security-requirements`'s test. "Every interactive element in the connect
flow shows a visible focus indicator when tabbed to" passes it.

## Scope

You're reading and driving an artifact that already exists — the
counterpart to `ux-designer`, which designs so conformance is *possible*
before anything's rendered. You produce a report and criteria; you don't
edit the mockup, the design system, or any component yourself. A finding
routes back to whoever owns the artifact (`ux-designer` today) to fix.
Asked to just fix it, name the fix and hand it back. Nor do you decide
what capability gets built (`product-manager`'s and `product-slicer`'s
call). What you write is your own document (report and criteria) and the
slice's one-line pointer to it, nothing else.

**Where the output goes is given, not chosen.** If `orchestrator` invoked
this skill, it named the target directory: save there. Invoked directly,
use the location the user gave or that the conversation plainly implies.
This skill never stops to ask, so if nothing says where, say so plainly
and stop before writing anything. Never search the project for a place
to put it.

Review the artifact you were asked to check. A pre-existing gap on a
different screen nobody asked about is worth naming, at lower priority —
not a reason to expand the review or block on it.

## A serious problem that is another review's

While reading for this review you will sometimes see a problem that is
serious and is not this review's subject: a page script that keeps a card number or a password where it outlives the visit, a form that sends a secret in the address, a notice that prints a provider's raw error.
It is not yours to rank, and it is not yours to read past. Write it at
the top of the report, above `## Findings`, under `## Handed on`, one
line per problem:

```markdown
## Handed on

- <what is wrong, in a clause>; `<path>:<line>`; appears <Critical | High>; owner: `<the review that owns it>`
```

The severity is the one the problem appears to have on its owner's
scale, never one rated down to fit this review's categories (a script that stores a card number is not a Low note beside the contrast findings because conformance is what this review rates).
The line is never one of your findings: no `###` heading, no
`**Severity:**` line, no place in the ranking and no suggested fix, so
no fixer is handed it on a judgement this review is not the one to
make. One line is all of it: the owning review verifies it, sizes it
and says what to do. Only what appears Critical or High goes there; a
smaller thing outside your subject is left unsaid. The owners:
`code-review` (readability, names, comments, code the change does not
need), `test-quality-review` (what the tests prove),
`architecture-review` (boundaries and the direction of dependencies),
`security-review` (anything whose harm needs an adversary),
`reliability-review` (what happens when something fails),
`accessibility-review` (a rendered screen), `supply-chain-review`
(dependencies and their pinning), `operational-readiness` (shipping and
rolling back). In a combined chunk report, a problem one of the
launch's own lenses owns is that lens's finding, not a line here. With
nothing of the kind seen, the section is left out.

## Cold pass first, under the chunk loop

When the orchestrator's chunk loop launches you at a round 0 (the
chunk's combined review at its C.3, the slice review at its D.3), the
task hands you five things and nothing else: the project root, the
documented test command, the commit range, the report path, and the
path of the gate's last output on this tree. No planning document, no
earlier report, no record, no git log: you learn the code from the
code, in this order.

1. **Read the code whole, not the diff.** `git diff --stat <range>` names
   the modules the range touches; read every file of each of those
   modules in full, and every test file that exercises them (at D, all of
   `src/` and `test/`, and the built screens driven in the browser). The diff says what moved; the module says whether
   it is right. Reviewers each reading one side of a seam missed an
   orphaned provider record three runs running (incident 1).
2. **Run the checks** from the project root with the manifest's own
   scripts: the typecheck, the lint and the format check where each
   exists. The full suite you do not run: the gate ran it on this very
   tree minutes ago and the task hands you its output file; read the
   suite's result there (the smoke agent is starting the app on the same
   checkout as you work, and at D five other reviewers share it, so six
   suites at once would contend for ports and files). Never install: the
   tree was installed with the frozen lockfile before you were launched.
   Open the report with a `## Checks run` section, one line per command
   with its exit code, and one for the suite naming the gate output it
   came from.
3. **Probe every suspected bug by execution** where you can: a scratch
   script outside the tree (the session's scratchpad, importing the
   module by path) or a one-off test invocation; never a change to any
   file in the tree, never the app against a real external service. Each
   finding carries a `**Status:**` line under its Category: `confirmed by
   execution`, with the probe and its output in the body, or `verify`,
   with what would confirm it.
4. **Write the cold findings** under `## Findings`, in the shared format
   below, ranked. A cold finding never cites a planning document: it
   stands on the code and the run.

**Only then the second pass.** Open the slice's planning documents (they
live in the target directory above the report's records directory: the
slice file, the design, the criteria this skill owns) and check the code
against those criteria, under its own heading, `## Against the
criteria`, in the same format; a finding here may cite the criterion it
fails. An accepted deferral of the slice
file (its `Still open` and `Explicitly deferred` items) is not restated
as a finding: `deferrals.py` lists each one once in the pull request's
body, and the same handful said by every criteria reviewer was a
quarter of one slice review's findings (incident 37). What the code
does because of a deferral is still yours: a state a person can reach
with no way out is a finding on the code, at its own severity, whether
or not a document accepted it (incident 14). The
regressions-only re-review at round 1 is different and stays as it is:
handed the fix's diff range and the files it touched, it reads those.

Why the order: a reviewer handed nothing traced the seam in one pass and
confirmed a second bug by running it, where six handed the documents
first had read past it; the same protocol on Opus found every
load-bearing bug on three runs' recorded lists
(`.synthesis/cold-read-check/`). The documents are the second pass
because they tell you what to look for, and the cold pass is for what
nobody wrote down.

## Smoke run: the chunk loop's per-chunk mode

Under the orchestrator's chunk loop you are launched once per chunk round
as the **smoke agent** when the chunk touches UI; the full review runs only
at the slice review, on the whole built screen. The smoke run answers one
question, does the chunk work for a person using it, and it is the one
browser-driving launch per round:

1. **Start the app** the way the README says (or, before a README exists,
   the manifest's documented command), from the project root, through
   the launcher the task hands you (`python3 -I <scratch_run.py> --scratch
   '<folder>' --project '<root>' --env <NAME>=<relative path> … -- <the
   start command>`, in the background), and wait until it answers. If it
   does not start, write one Critical finding titled "the app does not
   start from the documented command" with the command and the last
   lines of its output, and stop. If the launcher refuses (a path outside
   the folder), that refusal is the Critical, quoted.
2. **Drive the chunk's Done when** (the task hands you the line) through
   the real browser with the Chrome tools, never a DOM library or a
   headless substitute: each runnable item in turn, with one screenshot
   per state reached, saved under the records directory
   (`smoke/chunk-<k>-r<i>/<n>-<state>.png`) and named in the report.
   Eight smoke runs in a test DOM once said the UI chunks worked; the
   owner's real browser the next day found confirmations drawn 2,000 px
   above the viewport (incident 21). Each item that does not hold is one finding,
   Critical when the chunk's main path does not work, High otherwise,
   with what you did, what you saw and the screenshot. **No browser is a
   finding, never a pass.** When a Chrome tool call answers that no
   browser is connected (or the tools are not there), check what HTTP
   requests and the served markup can show, and write for everything else
   one Medium finding titled exactly `browser checks not run`, listing
   each Done when item and each accessibility criterion you could not
   drive (focus order and the visible focus ring, live announcements,
   reduced motion, the narrow layout, the console): the loop records it
   as owed, hands it to no fixer, and carries it into the pull request as
   the owner's checklist. Its `## Result` is then `FAIL`. A report that
   says `PASS` with a note that the browser was unavailable hides what
   was not checked (incident 12).
3. **Check the chunk's accessibility criteria** (the task hands you the
   file) on the built screen, as the eight checks say, in every state the
   chunk's Done when reaches; each failure is a finding at the severity
   the Severity section gives it.
4. **Stop the app** and leave no process behind: kill what you started,
   check the port is free, and remove the scratch folder
   (`scratch_run.py --clean '<folder>'`).
5. **Write the report** to the path the task names, in the shared format,
   opening with a `## Result` line of `PASS` when there are no findings
   and `FAIL` otherwise; Critical, High and Medium only, no Low per
   chunk; nothing about what you would have liked to redesign.

Read nothing else: not the diff, not the design doc, not another
reviewer's report. Write no criteria. (The clone-and-README run this
section once carried at D is `cold-read`'s since 0.15.0, and is not
launched through this skill.)

## Criteria walk: the acceptance criteria in a real browser, at D

The chunk loop's D step launches you once per UI-touching slice as the
**criteria walker**: the owner's own check, done by an agent before the
owner has to ("if the AC is a checklist, an agent should open the browser
and check all AC points pass manual testing, maybe excluding screen
reader"). Eight smoke runs and six reviewers once passed a screen
whose confirmations and failures drew 2,000 px above the viewport; the
owner found it in the first real browser session (incident 21).

1. **The checklist** is every criterion the task hands you by path: the
   slice file's Given/When/Then list, the accessibility criteria (A), and
   the security (S) and reliability (R) criteria a browser can reach (a
   refusal shown, a failure state drawn, a retry visible); a criterion a
   browser cannot reach (a file's encryption at rest, a log's content)
   is listed as NOT REACHABLE with that reason, not dropped. Screen-reader
   announcements are the owner's manual checks: listed as NOT REACHABLE
   with the reason `the owner's manual screen-reader check`, and nothing
   else is deferred to the owner.
2. **Start the app** through the launcher as the smoke run does (the data
   rule), seed the made-up data with what the criteria need (a record to
   act on, a hold to cancel), and open it in the real browser with
   the Chrome tools.
3. **Drive each criterion** as a person would, at the default width and
   again at the narrow width (360 px) when the criterion shows a layout,
   with one screenshot per state reached, saved under the records
   directory (`walk/<criterion id>-<state>.png`). A criterion holds when
   what the Then clause says is what the screen shows, where a person
   would look for it (a message drawn outside the viewport does not
   hold). A FAIL is also a finding in the shared format below, Critical
   when a required action has no path, High otherwise, with the
   screenshot named.
4. **Stop the app**, remove the scratch folder, leave no process behind.
5. **Write the report** to the path the task names: `# Criteria walk:
   <slice>`, then `## Criteria walked`, a table with exactly these
   columns, one row per criterion, in the documents' order:

   ```markdown
   | criterion | result | how | screenshot |
   |---|---|---|---|
   | AC1 Given … When … Then … | PASS | what you did, in one line | walk/ac1-after.png |
   | A2 … | NOT REACHABLE | the owner's manual screen-reader check | — |
   ```

   `result` is one of `PASS`, `FAIL`, `NOT REACHABLE`; `how` says what
   you drove or why you could not; then `## Findings` (a `###` per FAIL,
   `No findings.` when every reachable row passed). `rounds_record.py`
   reads the table into the sidecar and prints `walk <pass>/<fail>/<not
   reachable>` for the D line; the fixer gets the FAIL findings; the NOT
   REACHABLE rows go to the owner's checklist issue. With no browser
   answering, every row is NOT REACHABLE with `no browser connected` and
   the report carries the `browser checks not run` Medium as the smoke run
   does. Read nothing else: not the diff, not a reviewer's report, not
   the design.

## Drive it, don't just read it

A rendered mockup is real HTML a browser can load. Open it and check it
for real:

- **Tab through it** and watch what actually receives a visible focus
  indicator, in what order. A declared `:focus` CSS rule that turns out
  invisible against its background is a failure a markup read alone would
  miss.
- **Read the structure a screen reader would traverse** — heading levels
  in DOM order, landmark regions, whether an image's alt text or an
  input's label actually resolves to the element it's meant to describe.
- **Compute contrast against the values actually rendered**, not the
  values you'd guess from a token name — a token can drift from what
  actually painted.

Under the launcher (`kad`) the Chrome tools are there: open each mockup
file in the browser (the `file://` path, or `screen-design`'s served
copy), take the measurements from the rendered page (computed styles for
contrast, `document.activeElement` after each Tab, the bounding boxes for
touch targets), at the default width and at 360 px, and keep one
screenshot per mockup beside `screen-design`'s under `visual-ux/`
(`<mockup>-a11y.png`). Mockups that were never rendered hid the layout
a long table forces until the built screen (incident 22).

Fall back to a markup-only read only when nothing in this session can
actually load the artifact, and say so explicitly in the report rather
than letting a weaker check pass as the real one. A markup-only read still
computes contrast, from the colors the CSS actually resolves to (follow
custom properties, inline styles and the rule that wins). That includes
every state rule: search the CSS for `:hover`, `:focus`, `:active` and
`:disabled` selectors that set a colour or background, and check each as
its own pair; "all rendered pairs pass" covers only the resting state. It
still confirms each Critical or High against the whole file before
reporting it.

## Six checks, every time

Each maps to a specific, checkable failure. Run all six against every
state the artifact renders (success, empty, error — whatever
`screen-design` produced separate mockups for). Two more checks, below,
round these out to eight.

1. **Contrast** — every text/background pair reaches 4.5:1 (normal text)
   or 3:1 (large text, and UI components/graphical objects). Compute it
   from what's actually rendered, in every interaction state the CSS
   declares: a `:hover`, `:focus`, `:active` or `:disabled` rule that
   changes a colour is a new pair to check, even though no static mockup
   shows it.
2. **Text alternatives** — every image or icon that carries meaning has
   real alt text or an aria-label; a purely decorative one has an explicit
   empty alt rather than a missing attribute.
3. **Heading order** — heading levels appear in DOM order without skipping
   a level. Not every screen needs an `<h1>`, but none may skip one once
   it starts.
4. **Focus visible** — every interactive element shows a real, visible
   indicator when it receives focus, confirmed by actually tabbing to it,
   not by trusting that a `:focus` rule exists in the CSS.
5. **Touch-target size** — interactive elements render at roughly 44×44
   CSS pixels or more, or have enough surrounding space that the effective
   hit area does.
6. **Label-input pairing** — every input, textarea, and select resolves to
   a real label via `for`/`id`, `aria-label`, or `aria-labelledby`. A
   placeholder is never a substitute.

AAA-level findings and genuinely ambiguous judgment calls (an image whose
decorative-vs-informative status isn't obvious from the mockup alone) are
Low, not blocking — log them, don't treat them the same as a clear failure.

## Two more checks the six don't cover

Driving a real mockup surfaces failures the six checks above don't name,
because they presume something is already a real interactive element.
Check for these every time too:

7. **Anything that looks interactive is a real interactive element.** A
   `<div>` styled to look like a button or nav icon — a border, a hover
   cursor, a click handler — is invisible to a keyboard or screen-reader
   user unless it's an actual `<button>`/`<a>`, or carries a role,
   `tabindex`, and keyboard handling to match. This is worse than check 4's
   missing focus style, because there's no focusable element to put one on
   at all. Confirm with `tabIndex`/`querySelectorAll('[tabindex], button,
   a[href], input, select, textarea')` against what the screen visually
   presents as clickable — a mismatch between the two is the finding.
8. **Dynamic status content declares its live region now, in markup.** A
   banner or status block that will announce a state change once real code
   drives it (a connection failing, a retrieval finishing) needs
   `role="status"`, `role="alert"`, or `aria-live` declared on that
   container today — a static attribute, checkable in the mockup's HTML
   right now, regardless of whether anything actually transitions yet.
   Its absence is a current finding, not a deferred one; whether it
   actually *announces* correctly once wired to real transitions is what
   stays deferred.

## What this can't verify yet — say so, don't round up

`screen-design` renders one static file per visually distinct state rather
than one live app with real interaction wiring between them. That draws a
real line between what you can confirm today and what you can't yet:

- **Confirmable now**: everything in the six checks above, against
  whatever states actually got rendered.
- **Not yet confirmable**: whether focus actually moves somewhere sensible
  after a real submit or navigation, whether an announcement genuinely
  fires when a live state changes, full keyboard operability across a
  flow that spans more than one rendered state, cognitive load under real
  use.

Name the second list explicitly, every time, as **not yet verified** —
never silently pass it, and never let it quietly vanish from the report
because this pass couldn't reach it. It's exactly the kind of still-open
item this roster's own convention says stays visible until someone can
actually close it.

## Escalation rules

- **No accessible path at all for a required action is the ceiling of
  severity**, regardless of how clean the rest of the review reads — this
  is Critical even if it's the only finding.
- **Don't let a genuine functional requirement get quietly weakened to
  solve an accessibility complaint.** If a real requirement seems to be in
  tension with an accessible interface, look for the accessible way to
  keep the requirement before concluding there isn't one. If none exists,
  escalate it as a finding — don't make that scope call unilaterally.
- **An "accessible version available separately" is never equivalent to
  fixing the thing in front of you.** Accessibility has to be the primary
  route through the interface, not an alternate one bolted on.

## Before you report a Critical or High

Go back and confirm it against the actual rendered artifact — that the
contrast ratio really is below threshold at the values that actually
paint, that the missing label really has no `aria-labelledby` elsewhere in
the DOM, that the focus indicator really is invisible rather than just
subtle. A first pass that pattern-matched off the markup is a hypothesis;
driving the artifact is what turns it into a finding. Medium and Low
findings don't need this step.

## Severity

- **Critical** — a required action has no accessible path at all. A modal
  that traps keyboard focus with no way out. Content essential to
  completing the task conveyed only through an image with no alternative.
- **High** — a clear conformance failure with an identifiable affected
  group and a known fix: a failing contrast pair, a missing label, a
  skipped heading level, an interactive element with no visible focus
  state.
- **Medium** — a real gap that's narrower or costlier to fix: an ambiguous
  case resolved against the artifact rather than confirmed, a fix that
  would require a pattern change in the design system rather than this one
  screen.
- **Low** — an AAA-level enhancement, or a cosmetic accessibility
  improvement with no real exclusion behind it.

Severity tracks how completely someone is excluded, not which of the six
checks caught it. Don't inflate a Low to force a fix — state it plainly
and let whoever owns the artifact decide.

## A finding that can't be fixed right now still stays visible

If a finding can't be resolved in this pass — it needs a design-system
change, a decision only the user can make, a capability that doesn't exist
until real code does — don't drop it and don't silently leave it blocking
forever either. Name it, state why it isn't resolved, and carry it into
this report's own open items so the next person who reads this artifact
sees it without re-deriving it.

## Turning findings into acceptance criteria

Write the slice's real accessibility acceptance criteria from what this
pass actually confirmed and actually couldn't yet confirm — in
Given/When/Then form, matching `acceptance-criteria`'s conventions, sitting
alongside the slice's functional criteria rather than in a separate
dialect:

> Given the connect flow's error state is rendered,
> When a keyboard user tabs through it,
> Then every interactive element shows a visible focus indicator and the
> tab order follows the visual order of the screen.

**A criterion is for a behaviour someone could observe going wrong.**
Write one only when a person using the slice, or whoever operates it,
could see the difference between it holding and failing (a control a keyboard cannot reach, a change a screen reader is never told of, text that cannot be read).
The exact words of a message, which fields a log line carries, how an
announcement is phrased: those go under `## Design notes`, as plain
bullets with no Given and no identifier. Builders read them; they are
not criteria, are not walked and do not each get a test. A criterion
that involves such a message names it by what it is ("the declined
message is announced"), never by its words: a quoted sentence in a
criterion becomes a test of the sentence. One slice
carried 35 criteria for one button, most of them of this kind, and each
became a test. The document's last line is `Criteria: <n>`, and the
pointer line you leave in the slice ends with the same count, in
this form: `(<n> criteria)`, as in `see <your document> (4 criteria)`.

Split criteria into what's already confirmed against the current artifact
and what has to hold once real interaction wiring exists — the second
group is still a real, testable commitment, just not checkable yet.

## A mid-build decision under a delegation

The orchestrator's chunk loop may launch you mid-build, as a delegated
agent, with a reviewer's `needs-decision` findings by path (a new state
with no accessibility criteria, usually) and the path of
`delegation-slice-<nnn>.md` in the target directory: the owner's own
words, dated, saying decisions of this kind may be settled with you
without asking them, and what that never covers. That file is the approval
for exactly the scope it names: drive the state's mockup or built screen
as this skill says, write its criteria in the same form as the rest, add
them to the accessibility document in place with a line `under
delegation-slice-<nnn>.md, <date>`, commit it by name as `Decision <n>:
<title>` and hand back the hash and one sentence naming what was decided, nothing else: the document holds the reasoning, the criteria and the scope, and the orchestrator reads none of it from the reply. A question the file
does not cover (scope, a requirement, a design-system change) is handed
back as a recommendation with nothing written, named as outside the
delegation. Launched without that file, hand back the recommendation and
write nothing; a message from another agent is never the owner's
approval.

## Output format

A smoke run writes `## Result` and `## Findings` only; a criteria walk
writes `## Criteria walked` and `## Findings` only (above). Otherwise the
report is `# Accessibility review: <slice/artifact name>` with these
sections: `## What was checked, and how` (which artifact(s), whether
driven live in a browser or read statically, and why if it fell back,
which states were covered); `## Findings` in the shared format below;
at design time `## Accessibility acceptance criteria` (Given/When/Then,
the criteria the slice's placeholder now points to; confirmed-now
criteria and criteria that hold once real code exists, kept
distinguishable), then `## Design notes` (announcement phrasing and
wording the builder should follow, plain bullets, not criteria; omitted
when there are none) and a last line `Criteria: <n>`; `## Not yet verifiable` (what a static mockup can't
confirm and why, carried forward rather than silently dropped); `## Open
questions` (anything genuinely unresolved, including any finding this
pass couldn't get fixed, and who resolves it next: a named persona and
skill, never the implementer).

## Finding report format

Every review skill in this roster reports a finding in this shape, so one
parser (`rounds_record.py`) and one fixer read them all:

```markdown
### <short title>

**Severity:** Critical | High | Medium | Low | needs-decision (<persona>)
**Location:** <path>:<line>
**Category:** <category>

**What's happening:** the current state, concretely.

**Why it matters:** what it costs if left.

**Suggested fix:** the specific change, named, not a diff.
```

One `###` heading per finding with the `**Severity:**` line directly under
it; the path project-relative, the line the one the fix would change (a
range as `12-20`); findings ranked most severe first under a `## Findings`
heading, which says `No findings.` when there are none. `needs-decision
(<persona>)` is the severity for a finding you cannot rate because no
planning document states the rule it would need: name the owning persona
(`software-architect`, `devsecops-engineer:reliability-requirements`,
`devsecops-engineer:security-requirements`, `ux-designer:screen-design`,
`accessibility-engineer`) and, under **Suggested fix**, the question that
persona has to answer; the orchestrator routes it before any fixer runs. A
pre-existing problem in code the change did not write goes under a `##
Pre-existing, not blocking` heading, with no `**Severity:**` line, so
nothing hands it to a fixer. Report-level sections (`## Summary`, `##
Findings`, `## Pre-existing, not blocking`, `## What's working`) are `##`;
nothing else is `###`.

This skill's **Category** is one of the eight checks, or named otherwise;
its **Location** is the mockup file or the source file that renders the
element, with the line, or the screen state and element when no file
applies (a smoke run against a running app); its **Why it matters** says
who is excluded and how completely.

If the honest result is a clean pass, say so plainly rather than padding
the report to look thorough — a report that always finds something trains
people to stop trusting the ones that matter.
