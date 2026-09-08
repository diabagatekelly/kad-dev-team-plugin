Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/orchestrator/SKILL.md

Eight independent routing decisions. In each case with a target parameter, I took it as given (step 1), ran only the cheap mechanical checks of step 2, and checked for backward-routing signals before matching a row. No backward-routing signals (handed-back sections, supersession claims, self-declared skipped stages) were present in any of the eight.

## Directory A — `examples/newsletter-app/`

1. **Detected:** Target given, so no asking needed. Directory empty — no file with a `# Problem: ...` top heading, no scope maps, no requirements, no slices.
2. **Next:** `docs-writer:problem-framing-doc`, writing into `examples/newsletter-app/`.
3. **Why:** First row of the table. Nothing downstream can be inspected or routed against until a stable problem statement exists to refer back to.

## Directory B — `examples/recipe-app/`

1. **Detected:** Problem doc present (`# Problem: Recipe Bookmark Sprawl`). No `scope-map-*.md`, no `requirements-*.md`, no slices — so the "no scope map, no requirements, no slice anywhere yet" row matches exactly.
2. **Next:** `docs-writer`, to make the scope-map judgment call — reading `problem-framing.md` and applying `scope-map`'s own trigger criteria to decide whether this problem needs a scope map or is small enough to treat as a single unit.
3. **Why:** That decision belongs to the persona, from the problem doc's content — not to me, and not to a default question at the user. I'd hand it the target directory and let it ask the user only if genuinely torn.

## Directory C — `examples/budgeting-app/`

1. **Detected:** Problem doc present. One scope map, `scope-map-001.md`, `Status: Active` — so it's the current one by default. Four steps. No `requirements-*.md` anywhere, so the current unit is the lowest-numbered Active step with no requirements doc: **step 1, "Transaction retrieval."**
2. **Next:** `product-manager:requirements-refinement` for scope-map-001 step 1 only, saved to `examples/budgeting-app/`.
3. **Why:** The unit of work is a single scope-map step, not the whole problem. Steps 2–4 are deliberately out of frame — refining requirements for categorization or rebalancing now would decide things before anything's been built and learned from.

## Directory D — `examples/travel-planner/`

1. **Detected:** Problem doc present. No scope map, which per the table is a legitimate state — the unit is then the problem itself. `requirements-001.md` is Active and its heading scopes it to the problem (`problem: Ad Hoc Group Trip Planning`), which matches that unit. No slice files.
2. **Next:** `product-slicer` (`vertical-slicing` + `acceptance-criteria`) for the problem as a whole, saved to `examples/travel-planner/`.
3. **Why:** Requirements row is satisfied for the current unit; the next unsatisfied row is the missing slice. I'd tell the slicer that `requirements-001.md` is the primary input for WHAT to slice — its job is choosing the thinnest end-to-end path through those requirements, not re-deciding them.

## Directory E — `examples/inventory-app/`

1. **Detected:** Problem doc, Active `scope-map-001`, Active `requirements-001` scoped to step 1, and `slice-1.md` whose title names its source step (`scope-map-001 step 1`) — so it was cut from the scope map, not directly from the problem doc, and it belongs to the current unit. No user-story artifact locally and no user statement that filing happened, so that row is unsatisfied.
2. **Next:** `docs-writer:user-story-writeup` for slice 1, saved to `examples/inventory-app/`.
3. **Why:** Everything above that row is satisfied for step 1. Note the filing check is one I take the user's word on when the project doesn't track user stories locally — here there's neither an artifact nor a claim, so I treat it as not done.

## Directory F — `examples/inventory-app/` (story filed, design doc exists)

1. **Detected:** Same spine as E, plus a filed user story (user's word, which the skill accepts) and `design-1.md` for slice 1. The remaining step-2 check that matters is whether the slice's acceptance criteria still carry unfilled placeholders naming `devsecops-engineer` (or the older `security-engineer`/`reliability-engineer` names). Since nothing has run since the architect and no devsecops pass has touched this slice, those placeholders are unfilled — I'd confirm by grepping `slice-1.md`/`design-1.md` for the placeholder rather than reading the prose.
2. **Next:** `devsecops-engineer:security-requirements` for slice 1, saved to `examples/inventory-app/`.
3. **Why:** This is the first unsatisfied row. Two things I'm deliberately *not* doing: (a) not routing to `technology-bootstrap` even though no code exists — that row sits below the runtime-safety rows, because a structural design needs no stack and security/reliability criteria are technology-agnostic, so the stack choices should be made against a fully specified slice; (b) not touching `security-review`/`supply-chain-review`/`operational-readiness` — those are event-triggered against code that already exists here, and this spine hasn't reached code.

## Directory G — household bills, no target parameter

1. **Detected:** Nothing, and deliberately so. Step 1 was not satisfied: no artifacts directory was given. I did not inspect anything and did not search the project for a plausible location.
2. **Next:** Ask, once, before doing anything else, via `AskUserQuestion`: **"Where do this problem's artifacts already exist, or where should they be created if we're starting from scratch?"** Whatever the user answers becomes the target for every persona on this problem, in this session and future ones.
3. **Why:** Guessing a location or scanning for one is explicitly out of bounds. Also worth flagging: the user saying "start scoping this out" is *not* an instruction to run `scope-map` — the scope-map-versus-single-unit decision is `docs-writer`'s call from the problem doc, and there's no problem doc yet. Once the directory is known I'd re-enter at step 2; if it's empty, that's the `problem-framing-doc` row.

## Directory H — `examples/inventory-app/` (story filed, no design)

1. **Detected:** Same as E, but the user-story row is now satisfied by the user's word. No design artifact for slice 1.
2. **Next:** `software-architect:architecture-design` for slice 1, saved to `examples/inventory-app/`.
3. **Why:** Design is the next unsatisfied row, and it must precede the devsecops requirements passes — what data slice 1 actually handles depends on how it's built, so security and reliability criteria written before the structural decision would describe a system nobody is building.

## Cross-cutting notes

- **A, C, F, H are the ones where getting it wrong is easy.** C tempts you to run requirements for the whole scope map; F tempts you to bootstrap the stack because the repo is empty; H tempts you to jump straight to security criteria.
- **Every one of these stops after a single routed step.** Per step 5 I'd report what was detected and what was produced, then name the *next* row and ask whether to continue — except at a terminal state, where I'd say plainly that the roster stops there and `tdd-coach` doesn't exist yet. None of the eight is at that terminal row: F is two rows away (reliability-requirements, then technology-bootstrap, since this project has no stack).
- **No files were written or edited** — this was the routing decision only, as instructed.
