Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/orchestrator/SKILL.md, /Users/kellydiabagate/Documents/kad-developer-suite/agents/docs-writer/AGENT.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/problem-framing-doc/SKILL.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/scope-map/SKILL.md, /Users/kellydiabagate/Documents/kad-developer-suite/agents/product-manager/AGENT.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/requirements-refinement/SKILL.md, /Users/kellydiabagate/Documents/kad-developer-suite/agents/product-slicer/AGENT.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/vertical-slicing/SKILL.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/acceptance-criteria/SKILL.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/user-story-writeup/SKILL.md, /Users/kellydiabagate/Documents/kad-developer-suite/agents/software-architect/AGENT.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/architecture-design/SKILL.md, /Users/kellydiabagate/Documents/kad-developer-suite/agents/devsecops-engineer/AGENT.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/security-requirements/SKILL.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/reliability-requirements/SKILL.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/technology-bootstrap/SKILL.md

Note: `examples/*` paths named in the scenarios don't exist in this repo (confirmed) — per the orchestrator's own "stay inside your lane" rule, that's expected and not something to search for; the directory contents were taken as given in each scenario.

## Directory A — examples/newsletter-app/
1. **Detected:** Target given directly (`examples/newsletter-app/`); directory is empty — no problem framing doc, nothing else.
2. **Route to:** `docs-writer:problem-framing-doc`.
3. **Why:** Table row 1 — no problem framing doc is the first and most basic gate; nothing downstream can exist without it.

## Directory B — examples/recipe-app/
1. **Detected:** `problem-framing.md` exists (`# Problem: Recipe Bookmark Sprawl`); no scope-map, requirements, or slice files anywhere.
2. **Route to:** `docs-writer`, to decide — using `scope-map`'s own trigger criteria against the problem doc's actual content — whether this problem needs a scope map or is small enough to slice directly.
3. **Why:** Table row 2. This is explicitly not an orchestrator-level judgment call; `scope-map`'s trigger says to skip the map "if the problem framing doc already reads as one thing a single slice could plausibly start on." Only `docs-writer`, reading the doc's actual prose, can apply that test — I don't decide it here, and it may still ask the user if genuinely torn.

## Directory C — examples/budgeting-app/
1. **Detected:** Problem doc + `scope-map-001` (Active, 4 steps); no `requirements-*.md` anywhere, so the current unit is the lowest-numbered Active step with no requirements doc — step 1, "Transaction retrieval."
2. **Route to:** `product-manager:requirements-refinement` for scope-map-001 step 1.
3. **Why:** Table row 3. A scope-map step names a rough capability, not a decided WHAT; nothing has asked the user what they specifically want for transaction retrieval yet.

## Directory D — examples/travel-planner/
1. **Detected:** Problem doc, no scope map (problem judged small enough to skip one), `requirements-001` (Active, scoped to "problem: Ad Hoc Group Trip Planning" — the whole problem is the unit since there's no scope map), no slice yet.
2. **Route to:** `product-slicer` (`vertical-slicing` + `acceptance-criteria`), using requirements-001 as the confirmed WHAT.
3. **Why:** Table row 4 — the unit has a requirements doc but no slice; product-slicer cuts the smallest end-to-end slice from what product-manager already confirmed, not re-deciding WHAT.

## Directory E — examples/inventory-app/
1. **Detected:** Full spine through slice-1 (scope-map-001 step 1 → requirements-001 → slice-1, titled "Slice 1 (scope-map-001 step 1): Record a manual stock count for one item"); no user-story artifact and the user hasn't said filing happened.
2. **Route to:** `docs-writer:user-story-writeup` for slice 1.
3. **Why:** Table row 5 — a slice exists for the current unit but hasn't been written up as trackable work yet.

## Directory F — same as E + user-story filed + design-1.md exists, security placeholder still unfilled
1. **Detected:** Slice 1 is written up and filed (per user), designed (`design-1.md`), but `slice-1.md` still carries the literal placeholder `[SECURITY — placeholder, to be authored by devsecops-engineer]`.
2. **Route to:** `devsecops-engineer:security-requirements` for slice 1.
3. **Why:** Table row 6 — design doc exists, security criteria are still an unfilled placeholder. This row deliberately sits after design (per the skill's own rationale: what data a slice handles depends on how it's structured).

## Directory G — household bills, no directory given
1. **Detected:** No artifacts directory parameter, and nothing said about where this should live.
2. **What I'd do:** Stop and ask, before anything else: "Where do this problem's artifacts already exist, or where should they be created if we're starting from scratch?"
3. **Why:** Step 1's explicit rule — never guess a location and never search the project for one; whatever the user answers becomes the target for every persona invoked on this problem going forward.

## Directory H — same as E, but user story already filed, no design yet
1. **Detected:** Slice 1 written up and filed (per user); no architect design doc exists; no slice 2.
2. **Route to:** `software-architect:architecture-design` for slice 1.
3. **Why:** Table row 7 — slice has been written up as a user story but has no design doc yet.

## Directory I — same as F + security-001.md filled, no reliability artifact, repo confirmed stackless
1. **Detected:** Security criteria now concrete (security-001.md, pointer replacing the placeholder); no reliability artifact exists and nothing states failure behavior; user confirms the repo has no language/test runner/package manager yet.
2. **Route to:** `devsecops-engineer:reliability-requirements` for slice 1.
3. **Why:** Table row 7 (reliability) — security is filled but reliability behavior has never been made concrete. This still outranks the "no stack yet" bootstrap row, since bootstrap only applies once runtime-safety criteria (security *and* reliability) are both filled — the empty repo doesn't jump the queue.

## Directory J — same as I + reliability-001.md filled, repo still confirmed empty
1. **Detected:** Both security-001.md and reliability-001.md exist with concrete criteria; user reconfirms the repo is empty — no stack, nothing ever run.
2. **Route to:** `software-architect:technology-bootstrap` for slice 1.
3. **Why:** Table's second-to-last row — the slice's runtime-safety criteria are fully filled and the project genuinely has no stack. This is the one thing bootstrap is deliberately sequenced after: choices get made against a slice that's now fully specified.

## Directory K — same as J, but existing codebase with a working stack for months
1. **Detected:** Same slice state as J, but the user says this is going into a codebase that's had a language, test runner, package manager, lockfile, and passing test suite for months; no technology-bootstrap artifact exists and the user explicitly doesn't want one written retroactively.
2. **What I'd do:** Stop — terminal row. Don't route to `technology-bootstrap` and don't advance to a next scope-map step. Report that this is as far as the roster currently reaches: `tdd-coach` would implement this design next, and doesn't exist in this roster yet (confirmed — only docs-writer, product-manager, product-slicer, software-architect, and devsecops-engineer exist under `agents/`).
3. **Why:** Step 2's project-level check says explicitly to take the user's word that an established repo has already settled its stack without an artifact — "asking it to produce one retroactively is busywork." With no-stack-yet false, the bootstrap row doesn't apply, landing on the table's final row (designed, runtime-safety filled, project has a stack) — the defined stopping point.

## Directory L — examples/budget-tracker/
1. **Detected:** Complete spine through design for step 1, and `security-001.md` has concrete criteria *plus* a section headed "Handed back — not mine to absorb," stating that hosting slice 1 behind authentication is a scope change and belongs to `product-slicer`, not something devsecops should fold in.
2. **Route to:** `product-slicer` (`vertical-slicing`), to resolve the scope question about adding authentication to slice 1.
3. **Why:** Backward routing takes precedence over the whole table. This is exactly the named signal — a section headed "Handed back," naming another persona — and per the skill's rule, the finder (devsecops-engineer) reports, but the persona that owns scope (`product-slicer`) decides what happens to the slice (new slice ahead of it, narrow it, or grow it, in that ranked order). I'm not stating what re-inspection would find afterward — just the single routed destination, per the skill's own instruction not to narrate the round trip.

## Directory M — examples/expense-app/
1. **Detected:** `scope-map-002` (Active) with two slices. `slice-000.md`'s "Still open" section states, in its own text, that a requirements-refinement pass never ran for its step — it was cut mid-flight from an ADR-decided WHAT instead. `requirements-001.md` exists but is scoped to a *different* step (scope-map-002 step 2), not the step slice-000 belongs to. Slice-000 has no user-story writeup and no design doc yet.
2. **Route to:** `product-manager:requirements-refinement`, for the scope-map-002 step that slice-000 belongs to.
3. **Why:** Backward routing takes precedence — slice-000's own text says a stage was skipped for it, one of the explicit signals. The invalidated stage (requirements-refinement) is owned by `product-manager`, not by whoever finds the gap, so that's who it routes to — not straight ahead to user-story-writeup or architecture-design, which would silently skip the missing requirements pass forward-table order might otherwise suggest reaching next.
</content>
