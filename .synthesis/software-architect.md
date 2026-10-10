# Synthesis: software-architect

Internal only — never referenced from `agents/software-architect/AGENT.md` or
any of its backing skills. Delete once the full roster is built.

Output split into two skills from the start (not split later, unlike
product-slicer): `architecture-design` (pre-implementation — turn a
product-slicer slice into module/dependency-direction decisions before code
exists) and `architecture-review` (post-hoc — check existing/changed code
against the same rules). Distinct triggers, same underlying rule set; the
rule definitions themselves live in the agent's system prompt so neither
skill duplicates them. *(Superseded: each skill now carries its own copy,
because `claude plugin eval`, a direct `/skill` invocation and an inline
consult all load the skill without the agent; `AGENT.md` points at the
skills instead.)*

## Sources consulted

1. **Flexion plugin** —
   `flexion-ai-architecture-principles/skills/architecture-principles/SKILL.md`;
   `flexion-engineer-base/agents/software-architect-impl/AGENT.md` and
   `software-architect-review/AGENT.md`;
   `flexion-engineer-base/skills/option-enabling-architecture/SKILL.md`;
   `flexion-ai-oea-coaching/skills/oea-dependency-rule/SKILL.md` +
   `references/default-importance.md`;
   `flexion-ai-oea-coaching/skills/oea-evaluator/SKILL.md` +
   `references/yagni.md` + `references/screaming-architecture.md`;
   `flexion-oea-coder/references/dependency-rule.md` +
   `screaming-architecture-rules.md` (reference files only, not the
   surrounding grow-split-merge process).
2. **Personal skills** — checked global `~/.claude/skills` and every
   project-level `.claude/skills` under `~/Documents/*` — **none cover
   architecture/dependency review**; no personal material to draw on here,
   noted rather than fabricated (same finding shape as product-slicer's
   synthesis for its own area).
3. **CAMS** — `skills/cams-architecture/SKILL.md` (all 9 procedures);
   `agents/software-architect-impl/AGENT.md` and
   `software-architect-review/AGENT.md`; `skills/cams-new-feature/SKILL.md`
   Phase 2; skimmed `cams-vertical-slicing` and `cams-adr` only for
   hand-off points.

## Principle table

| Principle | Source(s) | Status |
|---|---|---|
| Importance = business risk of a defect in that module, not a fixed layer list | oea-dependency-rule | gap → added, adopted as the foundational framing over a fixed layer taxonomy |
| Dependency Rule: dependencies point from less-important → more-important; strategic/business code never imports tactical/infra code | cams-architecture Procedure 4; option-enabling-architecture; architecture-principles | baseline (roster's "dependency direction") |
| Strategic vs. tactical classification test — "if I change the database/framework/external system, does this code change?" | cams-architecture Procedure 4 | gap → added |
| Interfaces are owned by the strategic/importing side ("interfaces live with their callers"), implemented by the tactical/adapter side | software-architect-impl (engineer-base); cams-architecture Procedure 4 | gap → added |
| Two-direction dependency check: verify not just what a file imports (forward) but what *that* file imports (backward) — a types file can look clean going forward yet be contaminated by its own imports | software-architect-review, both CAMS and engineer-base independently | gap → added — the standout mechanic in the whole corpus |
| Composition-root exception: a factory/wiring function returning concrete adapters typed as the interface is not a Dependency Rule violation, provided the caller only ever sees the interface type | software-architect-review, both sources | gap → added |
| Dependencies take four forms, not just imports: file/folder placement, a boundary-crossing param/return/field type, design influence (module's shape distorted to match a lower concern, no code reference at all), translation responsibility | oea-dependency-rule | gap → added — "design influence" appears nowhere else and catches import-invisible violations |
| Violation severity scales with entanglement (how hard to remove without rewriting the important code), not just violation category | oea-dependency-rule | gap → added, more principled than a static severity-by-category table |
| Good Fences: only plain data (primitives/POJOs/arrays of those) crosses a boundary; framework/ORM types get translated to a DTO at the edge | cams-architecture Procedure 5; architecture-principles | baseline (roster's "module boundaries") |
| Invasive Species: third-party libraries risk-tiered by lock-in cost (HIGH: ORMs/HTTP clients/cloud SDKs/auth — isolate behind an interface+adapter; MEDIUM: UI/date/validation libs — consider it; LOW: single-purpose utilities — use directly) | cams-architecture Procedure 6 | gap → added |
| Screaming Architecture: name modules for business concepts, not technical layers; concrete test — strip the technical suffix, does a business concept remain? | cams-architecture Procedure 3; screaming-architecture-rules.md (oea-coder) | baseline (roster's "screaming architecture"), mechanism adopted from oea-coder |
| Anti-pattern catalogue: CLEAR_VIOLATION names (handler/controller/service/repository/utils/manager) vs. near-miss/context-dependent names (factory/helper/base/orchestrator/processor/worker) | screaming-architecture-rules.md (oea-coder) | gap → added |
| Bootstrap exception: framework entry/wiring files may keep canonical names since they contain no business logic | screaming-architecture-rules.md (oea-coder) | gap → added |
| Anti-fabrication guard: don't invent a business name to force a pass — if no real business concept exists yet, that's a signal the code has no clear axis of change yet, not a naming problem | screaming-architecture-rules.md (oea-coder) | gap → added, matches this plugin's existing don't-fabricate ethos |
| YAGNI applied to architecture is two-directional: check for over-engineering (abstraction before a 2nd real use case) *and* under-engineering (a real axis of change with no boundary yet) | software-architect-review, both sources | baseline, but the two-directional framing itself was a gap → added |
| YAGNI never argues against an interface required by the Dependency Rule, even with one implementation today | cams-architecture Procedure 8 | gap → added |
| Abstraction test: warranted when there are 2+ concrete implementations right now, not hypothetically | oea-evaluator yagni.md | gap → added |
| Design smells distinct from the four rules: missing / premature / wrong-level / leaky / inconsistent abstraction | software-architect-review, both sources | baseline, direct match for the "premature and missing abstraction" mandate |
| "Mixing what and how" smell — a business decision and a technical detail interleaved in the same method body | architecture-principles (flexion) | gap → added, catches what import-scanning misses |
| Broader OOP anti-patterns worth flagging in review: god object, circular dependency, shotgun surgery, feature envy, primitive obsession, inappropriate intimacy | software-architect-review, both sources | gap → added |
| Refactoring procedure for a found violation: locate it → find the real boundary → extract an interface on the more-important side → build an adapter on the less-important side → wire at the composition root → verify with a test that the important side is swappable/testable in isolation | option-enabling-architecture (flexion) | gap → added |
| Context-dependent importance: state the assumed importance ordering explicitly rather than asserting one universal ranking | oea-dependency-rule | gap → added — resolves a source contradiction, see below |
| Balanced/pragmatic review stance: distinguish "must fix" from "could improve"; a documented deviation can be an acceptable tradeoff, not everything is a violation to eliminate | software-architect-review, both sources | gap → added |
| Legacy code: review only changed/new code for compliance, note pre-existing violations separately (Boy Scout Rule) rather than blocking on full-codebase compliance | software-architect-impl and -review, both sources | gap → added |
| Severity taxonomy for findings: Critical/High/Medium/Low, tied to business-risk impact | software-architect-review, both sources | gap → added |
| Design-doc output stays conceptual — no file paths, function signatures, or code | cams-new-feature Phase 2 | gap → added, keeps the design skill's scope from creeping into pseudo-code |
| ADRs are a separate artifact for cross-cutting/costly-to-reverse decisions, owned by `docs-writer`, not authored by this persona | this plugin's own `adr` skill + PERSONAS.md roster row 1 | internal boundary decision, not from external sources |

## Contradictions — flagged and resolved

**1. Terminology: OeSA vs. OEA vs. "Option-Enabling/Clean Architecture."**
`flexion-engineer-base` says "OeSA" in prose; `flexion-ai-oea-coaching` says
"OEA"; PERSONAS.md's own roster row says "Option-Enabling/Clean
Architecture." Resolved in favor of **"Option-Enabling Architecture
(OEA)"** — every relevant directory across both Flexion plugins
(`oea-coaching`, `option-enabling-architecture`, `oea-dependency-evaluator`,
`oea-refactorings`, `oea-dependency-rule`, `oea-evaluator`) is spelled
"oea," despite the inconsistent prose inside a couple of files; this repo
has never used either acronym before, so there's no existing convention to
conflict with.

**2. Security's rank relative to domain rules.** The Mount Fuji model
(`option-enabling-architecture`) ranks security/privacy as the single most
important layer, above domain rules. `default-importance.md`'s 12-level
list ranks security #3, below core domain model and domain rules. Resolved
by not picking a side: both sit at the top tier, and which one wins in a
specific conflict is domain-dependent (an auth bypass and a broken
transaction-integrity rule are both catastrophic, in different domains one
outweighs the other). Adopted `oea-dependency-rule`'s own meta-principle
instead — state the assumed importance ordering explicitly for the case at
hand, don't assert a universal ranking.

**3. Naming the rule-taxonomy in output vs. staying in pure risk-language.**
`oea-dependency-rule` explicitly forbids naming patterns like "hexagonal
architecture" in review output, staying in plain importance/risk terms.
`software-architect-review` (engineer-base) names "Dependency Rule,"
"Good-Fences Rule," etc. constantly. Resolved against the pure
pattern-agnostic stance: kad-dev-team is personal, single-user tooling, and
its existing personas already teach and reuse named vocabulary session to
session (Given/When/Then, vertical slice). This persona's own named rules
(Dependency Rule, Good Fences, Invasive Species, Screaming Architecture)
become that same kind of shared vocabulary. What's rejected is dropping in
*unrelated* academic jargon the skill doesn't itself define (e.g.
"hexagonal architecture," "ports and adapters") as if naming a pattern adds
information — name only the vocabulary this skill defines and explains.

**4. YAGNI directionality.** `software-architect-review` treats it as
two-directional (over- *and* under-engineering); `oea-evaluator`'s
`yagni.md` and its scoring model are one-directional (over-engineering
only). Resolved in favor of two-directional — it's the direct match for
this persona's stated mandate ("catching both premature *and* missing
abstraction," PERSONAS.md roster row 4).

**5. Screaming-architecture mechanism.** `oea-evaluator` buckets directory
names by word-list membership into a ratio score; `oea-coder`'s
`screaming-architecture-rules.md` uses a decision procedure (strip the
technical suffix, does a business concept remain?) plus a two-tier
violation catalogue. Resolved in favor of the decision-procedure version —
more directly actionable for giving concrete rename feedback, and avoids
numeric scoring (next point).

**6. Whether to adopt numeric/percentage scoring at all**
(`oea-evaluator`'s parallel-subagent scored health-check, banded
Excellent/Good/Fair/Poor). Resolved: no. No other persona in this roster
scores anything numerically, PERSONAS.md's own "Orchestrator v2"
parallel-review-synthesis idea is explicitly deferred until more personas
exist, and a periodic whole-codebase scored audit is a different, larger
tool than either of this persona's two triggers (per-slice design,
single-file/PR review).

**7. Impl/review split.** Both Flexion and CAMS already split this exact
persona into `-impl` (writes code, runs a TDD loop) and `-review`
(read-only, findings report). Resolved against adopting the split for
kad-dev-team. Every existing persona here (`docs-writer`, `product-manager`,
`product-slicer`) produces planning documents, never application code —
there is no code-writing agent in this plugin yet, and introducing one
solely for architecture would be a bigger structural change than this
persona's scope justifies. Instead: **one agent, two skills** —
`architecture-design` (pre-implementation, produces a design doc, may ask
clarifying questions) and `architecture-review` (post-hoc, produces a
findings report, read-heavy) — mirroring how `product-slicer` already
carries two related-but-distinct skills (`vertical-slicing` +
`acceptance-criteria`) in one agent rather than two. Neither skill writes
or edits application code — `Write`/`Edit` in this agent's tool list means
the design-doc/findings-report artifact, not source files, matching this
plugin's existing planning-persona tool convention. If a future
`tdd-coach` persona wants its own design/implementation split, that's a
separate decision when it's built, not inherited from this one.

**8. Where a decision becomes an ADR vs. stays inside a per-slice design
doc.** Not a source contradiction — an internal boundary this plugin had
already half-decided: PERSONAS.md roster row 1 lists ADRs under
`docs-writer`, and `skills/adr/SKILL.md` already exists, unowned by any
built persona except `docs-writer`. Resolved: `architecture-design`
recognizes when a decision clears the ADR bar (architectural, significant,
non-obvious) but does not write the ADR itself — it flags the decision and
hands off to `docs-writer`, keeping the boundary `docs-writer` already
owns.

## Top gaps folded into skills

1. `skills/architecture-design/SKILL.md` (new) — per-slice strategic
   design before code exists: importance-as-risk framing, the four rules
   applied prospectively, the refactoring procedure for a violation hit
   while designing, conceptual-only output discipline, ADR hand-off
   recognition, ask-vs-defer convention (reusing this plugin's existing
   planning-persona pattern).
2. `skills/architecture-review/SKILL.md` (new) — post-hoc review of
   existing/changed code: two-direction dependency check, composition-root
   reasoning, design-smell + anti-pattern catalogue, severity taxonomy +
   finding-report format, legacy-code Boy Scout stance, balanced/pragmatic
   stance.
3. Cross-cutting content shared by both skills (the four rule definitions,
   the importance-as-risk framing, the context-dependent-importance
   caveat) lives in `agents/software-architect/AGENT.md`'s system prompt
   rather than duplicated in both skill files.
