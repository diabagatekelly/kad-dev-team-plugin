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
