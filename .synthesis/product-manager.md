# Synthesis: product-manager

Internal only — never referenced from `agents/product-manager/AGENT.md` or
its backing skill. Delete once the full roster is built.

Fills a gap found by dogfooding: `docs-writer` (problem-framing-doc,
scope-map) deliberately never designs a solution, and `product-slicer`
picks the smallest end-to-end slice by technique (risk-avoidance,
size heuristics) — but nothing between them ever pins down, with the
actual user, *which* capability/approach they want built first and why.
`product-slicer` was unilaterally deciding that on the user's behalf.

## Sources consulted

1. **Flexion plugin** — `flexion-product-base/skills/user-story-writer/SKILL.md`,
   specifically "Step 1: Understand the User Need" and "Interactive
   Workflow → When User Provides a Feature Idea" (not previously mined for
   `product-slicer` — that synthesis pulled slicing *technique* from this
   file, not its up-front requirements-gathering step).
2. **Personal skills** — checked `~/.claude/skills` and project-level
   `.claude/skills` across `~/Documents/*` for anything requirements/PM/
   stakeholder-related. **None found** — no personal material to draw on,
   noted rather than fabricated (same result `docs-writer` and
   `product-slicer`'s own synthesis notes recorded for their weak spots).
3. **CAMS** — `cams-new-feature/SKILL.md` Phase 1 ("Feature Definition &
   Slice Identification"), specifically its Q&A activities and the
   explicit principle "Phase 1: WHAT ... Phase 2: HOW strategically ...
   Phase 3: HOW tactically."

## Principle table

| Principle | Source(s) | Status |
|---|---|---|
| A dedicated WHAT-pinning-down step exists, separate from both problem-framing (states the problem, no solution) and slicing (decides HOW to cut it thin) | CAMS `cams-new-feature` "Key Principles: Phase 1: WHAT ... Phase 2/3: HOW" | **adopted**, gives this persona's whole reason to exist |
| Core Q&A: what is the user trying to accomplish, what are the acceptance criteria/edge cases beyond what's already stated, what should happen when things go wrong | CAMS `cams-new-feature` Phase 1 Activities step 5 | **adopted**, adapted — see below |
| Understand-the-user-need questions: who is the user, what are they trying to accomplish, why do they need this, what's the simplest version that delivers value | Flexion user-story-writer "Step 1: Understand the User Need" | **adopted**, overlaps with CAMS's list; merged into one question set rather than kept as two |
| Must actually ask the user directly — this is a live conversation, not inference from the problem doc alone | both sources' entire framing (CAMS: "Conduct Q&A session... ALWAYS required"; Flexion: "Ask clarifying questions") | **adopted**, load-bearing — this persona's entire value is asking, not guessing |
| Output is a decided WHAT (who, what capability, why, what's confirmed in vs. out for this piece) — not yet a thin path, not yet formal Given/When/Then AC | own draft, boundary-drawn against `product-slicer`/`acceptance-criteria`'s existing mandate | **adopted**, original — see "Declined" below for why this isn't folded into an existing skill |

## Contradictions — flagged and resolved

**Once per feature (CAMS) vs. once per scope-map step (this roster).** CAMS's
Phase 1 happens once, up front, for the *entire* feature, and identifies
*all* vertical slices in the same pass (its Gherkin file has every slice
annotated from the start). This roster already has `scope-map` doing that
once-up-front chunking (naming, not designing, the rough steps) — CAMS's
Phase 1 is really two things bundled together: identify the rough shape
(→ `scope-map`'s job here) and pin down concrete requirements (→ this
persona's job here). Resolved by splitting: `scope-map` still runs once,
up front, naming rough steps without asking detailed questions about any
one of them; `product-manager` runs per step (or once, for a problem small
enough that `scope-map` was skipped entirely), pinning down that one
step's concrete requirements only when it's actually about to be worked —
closer to this roster's existing JIT bias (`scope-map`'s own skill already
warns against deciding too much too early) than CAMS's own once-up-front
model, which is a deliberate deviation, not an oversight.

## Declined

**Folding this into `product-slicer` instead of a new persona.** Considered,
since `product-slicer` already has an "ask when it matters" rule. Declined
because the two mandates are genuinely different in kind: this persona
asks about the user's actual priorities and the shape of what they want
(a product question, answerable only by the person who wants the thing
built); `product-slicer` decides how to cut whatever's already been
decided into the smallest safe first technical step (an engineering
question). Bundling them back together reintroduces exactly the failure
this persona exists to fix — an engineering-flavored heuristic
(risk-avoidance, size) silently standing in for a product decision nobody
was actually asked about. Matches this roster's own "overlap between
personas is a smell — sharpen the boundary" convention rather than merge.

## Top gaps folded into skills/requirements-refinement/SKILL.md

1. Merged CAMS's and Flexion's overlapping Q&A lists into one question set,
   original wording.
2. A requirements write-up format distinct from both the problem doc
   (states the whole problem) and the slice write-up (states the thin
   technical path) — who/what/why/confirmed-in/confirmed-out for one
   scope-map step (or one small problem), numbered and superseded like
   `scope-map` and `adr`, not edited in place.
3. Explicit boundary against writing thin paths, AC, or slicing technique —
   that content still belongs to `product-slicer`/`acceptance-criteria`
   once this persona hands off a decided WHAT.
