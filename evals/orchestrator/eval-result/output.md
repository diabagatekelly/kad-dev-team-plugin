Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/orchestrator/SKILL.md

## Directory A — `examples/newsletter-app/`

**Detected:** Directory is empty. No problem framing doc, no scope map, no requirements doc, no slice.

**Next step:** Route to `docs-writer:problem-framing-doc`.

**Why:** Step 2's first check — a problem framing doc (top heading `# Problem: ...`) — comes back negative, and that's the first row of the step 3 routing table, checked before anything else. Nothing else in the directory needs inspecting once this row matches.

---

## Directory B — `examples/recipe-app/`

**Detected:** `problem-framing.md` exists (`# Problem: Recipe Bookmark Sprawl`). No scope-map, requirements, or slice files anywhere.

**Next step:** Route to `docs-writer`, to make the judgment call (per `scope-map`'s own trigger criteria, reading the problem doc) of whether this problem needs a scope map or is small enough to treat as one unit.

**Why:** This matches row 2 exactly — problem doc present, and none of scope-map/requirements/slice exist yet. Per the routing table, this decision belongs to `docs-writer` reading the problem doc's actual content, not to the orchestrator guessing or defaulting to asking the user. (It may still ask the user if genuinely torn, but that's `docs-writer`'s call to make, not mine to make on its behalf.)

---

## Directory C — `examples/budgeting-app/`

**Detected:** Problem doc exists. `scope-map-001.md` exists with `## Status: Active` and four steps (1. Transaction retrieval, 2. Transaction categorization, 3. Budget & spending view, 4. Checking/savings rebalancing). No `requirements-*.md` file exists anywhere, so none of the four steps has requirements yet.

**Next step:** Route to `product-manager:requirements-refinement` for **scope-map-001 step 1 — Transaction retrieval**.

**Why:** Row 3 applies once a problem doc and (optionally) a scope map exist. The current unit is defined as "the lowest-numbered Active scope-map step with no requirements doc yet." Since no requirements doc exists for any step, step 1 is the lowest-numbered one lacking requirements, so it's the current unit, and it has no requirements-refinement doc — matching row 3.

---

## Directory D — `examples/travel-planner/`

**Detected:** Problem doc exists. No scope-map file (problem judged small enough to skip one). `requirements-001.md` exists, titled against "problem: Ad Hoc Group Trip Planning" (not a scope-map step), `## Status: Active`. No slice files yet.

**Next step:** Route to `product-slicer` (`vertical-slicing` + `acceptance-criteria`), using `requirements-001.md` as the primary input for what to slice.

**Why:** With no scope map, the current unit is "the problem" itself per the row-3 definition, and that unit already has an Active requirements-refinement doc — so row 3 is satisfied and we move down to row 4: requirements doc present, no slice yet.

---

## Directory E — `examples/inventory-app/`

**Detected:** Problem doc exists. `scope-map-001.md` Active, includes step 1 "Stock count entry." `requirements-001.md` exists for scope-map-001 step 1, Active. `slice-1.md` exists, titled "Slice 1 (scope-map-001 step 1): Record a manual stock count for one item" — its title names the source scope-map step, so it belongs to the current unit. No user-story/write-up artifact exists, and the user hasn't said it was filed.

**Next step:** Route to `docs-writer:user-story-writeup` for slice 1.

**Why:** Current unit (scope-map-001 step 1) has requirements and now has a slice, satisfying rows 3 and 4. Row 5 checks whether that slice has been written up as a user story yet — no matching artifact exists and filing wasn't asserted by the user, so it hasn't. Row 5 is the match.

---

## Directory F — `examples/inventory-app/` (same as E, but user states slice 1 is already written up and filed)

**Detected:** Same artifacts as Directory E, plus the user's statement that slice 1 has been written up and filed. No architect design exists yet; no slice 2 exists.

**Next step:** Stop. No further routing for this unit.

**Why:** Step 2 explicitly says to take the user's word for whether filing happened when no local artifact tracks it — so the current unit's slice counts as written up, which is the terminal row of the table. Per step 5 of the skill, this is as far as the roster currently reaches: `software-architect` would design this slice next but doesn't exist in the roster yet. I would say so plainly and explicitly not advance to scope-map-001 step 2's requirements refinement — doing that now would be deciding the next step's scope before this step's slice has been designed or built, which is exactly what the "don't chain past the terminal row" rule is guarding against. If the user wants to start step 2 anyway, that has to be their explicit call, not something this routing offers on its own.

---

## Directory G — no artifacts directory given

**Detected:** No directory parameter was passed, and the user didn't mention where this problem's artifacts should live. The request itself ("split shared household bills fairly... start scoping this out") sounds like a fresh problem, but per the skill I'm not permitted to guess a location or search the project for one.

**Next step:** Before doing anything else — including any inspection — ask the user exactly:

> "Where do this problem's artifacts already exist, or where should they be created if we're starting from scratch?"

**Why:** Step 1 is unambiguous: when no target directory is given, that question must be asked first, before step 2's inspection or any routing decision. Whatever the user answers becomes the target for this problem going forward. I would not infer a folder name (e.g., from "household bills") or default to any existing example directory — the skill explicitly rules that out ("never guess a location yourself and never search the project for one instead of asking").
