# Dogfood run — graded against the eval cases' own graders

A live end-to-end run of the roster against one real problem, producing the
eleven artifacts in this directory. Unlike an eval case, there is no fixture
here — this is the personas working a problem the user actually has.

**This run is the first one taken after the five ordering fixes** (see
`PERSONAS.md`). The previous run is what exposed them: a security pass
discovered slice 1 needed a login nobody had scoped, offered the user three
ways out including "grow the slice," and the slice that resulted never got a
requirements pass. Everything below is the same roster after those fixes.

## How this was graded

Each artifact was graded against the graders belonging to its owning skill's
eval case. Two caveats on method:

- **`skill-invoked` and phase-1 graders don't apply.** These are finished
  documents, not captured harness output — there's no "Skills consulted"
  line and no recorded clarifying question to grade.
- **Some graders are fixture-bound and were adapted or skipped**, noted per
  row below. Adapted means the *property* was graded against different
  content; skipped means the grader asserts specifics of a fixture that
  doesn't exist here.

## Results — 16 graders, 16 PASS

| Artifact | Grader | Result |
|---|---|---|
| `problem.md` | no-solution-designed | PASS |
| `scope-map-001.md` | has-required-sections (regex) | PASS |
| `scope-map-001.md` | **cross-cutting-constraints-routed-not-deferred** | PASS |
| `scope-map-001.md` | no-slicing-or-design | PASS |
| `scope-map-001.md` | steps-cover-full-problem | PASS |
| `requirements-001.md` | has-required-sections (regex) | PASS |
| `requirements-001.md` | **reconciles-constraints-with-consequences** | PASS |
| `requirements-001.md` | captures-priority-reasoning *(adapted)* | PASS |
| `requirements-001.md` | no-thin-path-or-ac | PASS |
| `slice-001.md` | **scenario-a-names-slice-set** | PASS |
| `slice-001.md` | **scenario-c-owns-scope-change-without-growing** *(adapted)* | PASS |
| `slice-001.md` | scenario-a-final-slice-is-complete *(adapted)* | PASS |
| `user-story-001.md` | final-writeup-is-complete *(adapted)* | PASS |
| `technology-bootstrap-001.md` | **asks-only-what-the-first-test-forces** | PASS |
| `technology-bootstrap-001.md` | **defers-persistence-with-the-in-memory-reason** | PASS |
| `technology-bootstrap-001.md` | **recommends-rather-than-decides** | PASS |
| `technology-bootstrap-001.md` | **records-non-choices-and-open-categories** | PASS |
| `technology-bootstrap-001.md` | **pinning-posture-treated-as-a-choice** | PASS |

Bold rows are graders written this session, most of them for rules added
because the *previous* run failed. Every one of them passes here.

Plus a mechanical check not covered by any grader: all 15 cross-references
between artifacts resolve — no artifact points at a document that doesn't
exist.

## The result that matters

The failure this session's fixes were written for **did not recur, and the
mechanism visibly worked.**

`requirements-001.md`'s Constraints-in-force table carries the hosting
constraint through to its consequence — *"Something on a network will
display this account's transactions, so 'who is allowed to see this' must be
answered inside this step, not after it"* — and then routes it onward under
a heading reading **"Finding for product-slicer."** That is the constraint
surfacing at requirements time, handed to the persona that owns scope,
rather than being discovered by a security pass three stages downstream.

`slice-001.md` then absorbed it correctly. Its narrowing — run locally, so
there is nobody to exclude — is ranked option 2, chosen with reasoning, and
the slice states plainly that *"if this slice ever becomes network-reachable,
the narrowing is void and the access-control work comes back into it."*

A **second** scope change arrived later in the same run, from
`reliability-requirements`: the provider prepares transaction history
asynchronously and returns an empty result until it's done, so the original
criteria would have told the user "no transactions found" when the truth was
"not yet." `product-slicer` worked the ranked order explicitly, rejected
growth with a concrete reason (webhooks would need a public endpoint, which
would void the local-only narrowing), and recorded what the choice did and
did not invalidate.

Growth was rejected on the merits both times, by the persona that owns
scope, with the reasoning written down.

## What this run does *not* tell us

- **Four artifacts are ungraded** because no eval case exists for their
  skill: `adr-001.md`, `adr-002.md`, `security-requirements-001.md`, and
  `reliability-requirements-001.md`. The last two are the most significant
  gap — `devsecops-engineer` produced two findings that drove this entire
  run, and nothing checks the quality of either.
- **`design-001.md` is ungraded.** Its case's graders are bound to a
  CSV-export fixture (a synchronous-vs-async decision, a premature generic
  formatter interface) with no counterpart here. Grading it would need
  portable graders, which is a real gap in that case.
- **Passing here is not passing the eval cases.** These graders were run
  against real artifacts, not against the fixtures the cases define. The
  cases themselves still need running — see `evals/README.md`.
- **One run, one problem.** A personal-finance problem with a hosted-app
  constraint is exactly the shape that exercises these rules. It is not
  evidence they generalize.

## Update — two of the gaps above have since closed, and this run has grown

This table and its "ungraded" list describe this directory's state as of
the run it documents, not today. Since then: `security-requirements-001.md`
and `reliability-requirements-001.md` were independently audited against
their skills' text (not against this table) once those skills got eval
cases — the audit found a real gap (monitoring/telemetry never addressed
as a data-exit route) and produced the `addresses-all-five-exits` grader,
recorded in `devsecops-engineer:security-requirements/eval-score/`, not
here. `design-001.md`'s "no portable graders" gap closed when
`architecture-design`'s case was reworked into `portable-*`/`fixture-*`
graders (see that case's `NOTES.md`). And this directory has since grown
two more artifacts this table predates entirely — `design-system-001.md`
and `screen-design-001.md`/`visual-ux/`, produced by later `ux-designer`
dogfood runs and graded separately (9/9 and 9/9; see
`ux-designer:design-system/eval-score/` and
`ux-designer:screen-design/eval-score/`).

Not re-deriving a new combined table here — see `PERSONAS.md` and each
case's own `eval-score/summary.md` for current status instead of treating
this file's table as live.

## `accessibility-review-001.md` — graded against its case's own graders

Unlike `design-system-001.md`/`screen-design-001.md` above, this one gets
the full table treatment (not just a narrative pointer), since grading it
is exactly what was asked for. `accessibility-review-001.md` is a real
dogfood run — `accessibility-engineer` actually driving all seven of this
directory's real rendered mockups in a browser (not the synthetic
reorder-accounts fixture `accessibility-engineer:accessibility-review`'s
own case uses) — graded against that case's `graders/*.md`.

`skill-invoked` doesn't apply, same rule as everywhere else in this file:
this is a finished document, not captured harness output. Two graders
assume fixture specifics this real slice's findings don't contain and are
skipped rather than force-fit; two more are adapted to test the same
underlying property against different real content.

| Grader | Result |
|---|---|
| `skill-invoked` | N/A — finished document |
| `catches-no-keyboard-path-on-required-interaction-critical` *(adapted)* | PASS |
| `rejects-accessible-version-elsewhere-as-resolution` | **skipped** |
| `preserves-requirement-instead-of-removing-it` | **skipped** |
| `catches-non-semantic-interactive-div` | PASS |
| `catches-missing-heading-on-status-title` | PASS |
| `catches-missing-live-region-on-status-block` | PASS |
| `no-false-positive-on-correct-focus-style` *(adapted)* | PASS |
| `produces-given-when-then-acceptance-criteria-not-just-findings` | PASS |

**Result: 6/6 graded PASS, 2 skipped, 1 not applicable.**

**Why the two skips are real skips, not force-fits.**
`rejects-accessible-version-elsewhere-as-resolution` and
`preserves-requirement-instead-of-removing-it` both test what the review
does when a defect it finds is tempting to wave off or a fix is tempting
to solve by weakening a requirement — neither situation exists anywhere
in this artifact's eight findings. Nothing in slice 1's connect flow
claims an accessible alternative exists elsewhere, and none of the
findings involve a functional requirement in tension with accessibility.
Grading these against content that doesn't contain the scenario they test
would produce a vacuous PASS, which is worse than an honest skip — the
same reasoning `evals/example/summary.md`'s own method section already
states for fixture-bound graders generally.

**What the two adaptations tested instead.**
`catches-no-keyboard-path-on-required-interaction-critical`'s literal
premise (a required action with zero accessible path, rated Critical)
doesn't hold here either — the nav-rail/quick-action controls have zero
accessible path but aren't *required* by slice 1's own acceptance
criteria, so the review correctly rates them High, not Critical. Adapted
to test the more general property the Critical-bar rule actually depends
on: does the finding reason explicitly about *why* Critical doesn't apply
yet (nothing currently requires using these controls) and *what would
change that* (a later slice making one of them load-bearing)? It does,
naming both halves — which is a stronger signal than a bare severity
label would have been, since it shows the rule was applied as a live
test against this artifact's facts rather than pattern-matched from a
label. `no-false-positive-on-correct-focus-style`'s literal premise (an
already-correct focus style that shouldn't be falsely flagged) also
doesn't hold — no screen in this real artifact has a correct focus style
anywhere, unlike the synthetic fixture's `.btn-primary`. Adapted to test
the same underlying discipline (don't collapse two different defects into
one over-broad finding) against what's actually here: the review keeps
"a control with no focusable target at all" (finding 1, the nav icons)
and "a focusable control with no focus style" (finding 2, the one real
button) as two separate findings with two different fixes, rather than
reporting one generic "focus is broken" finding across both.

**Independent of any grader:** finding 8 (every interactive control below
the 44×44 baseline) traced its root cause to `design-system-001.md`'s own
declared token values and routed the fix back to `ux-designer:design-system`
rather than proposing a per-screen patch — the seam this roster's own
`AGENT.md` boundary rule exists to hold, applied correctly on the first
real artifact that actually presented the choice.
