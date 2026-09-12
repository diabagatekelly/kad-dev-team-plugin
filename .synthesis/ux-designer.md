# Synthesis: ux-designer

Internal only — never referenced from `agents/ux-designer/AGENT.md` or any of
its backing skills. Delete once the full roster is built.

Output split into two skills from the start, mirroring the
establish-once/apply-per-slice shape `software-architect` already uses for
`technology-bootstrap`/`architecture-design`: `design-system` (establish, or
on request review/evolve, the project's UI design system once — the binding
constraint for every subsequent screen) and `screen-design` (per slice —
compose within that system for one slice's UI-touching parts). Working names;
final naming happens at actual skill-authoring time.

## Sources consulted

1. **Flexion plugin** —
   `flexion-oea-coder/skills/flexion-frontend-design/SKILL.md` (all three
   modes: Foundation, Constrained, Advisory);
   `flexion-oea-coder/skills/flexion-frontend-design/references/built-in-design-system-checklist.md`;
   `flexion-oea-coder/skills/flexion-frontend-design/references/built-in-critique-framework.md`;
   `flexion-oea-coder/skills/flexion-frontend-design/references/built-in-copy-checklist.md`;
   `flexion-oea-coder/skills/flexion-frontend-design/references/built-in-wcag-subset.md`
   (read for its system-vs-component framing of the accessibility boundary,
   not for its own content — that's `accessibility-engineer`'s source
   later); `flexion-ai-visual-qa/skills/visual-qa/SKILL.md` (skimmed only —
   a post-code review skill comparing rendered output against a spec via
   Playwright; informs what a design needs to be concrete enough to check
   against later, not a design-decision source itself).
2. **Personal skills** — checked global `~/.claude/skills` and every
   project-level `.claude/skills` under `~/Documents/*` — **none cover
   UX/visual/interaction design**; no personal material to draw on here,
   noted rather than fabricated (same finding shape as
   `software-architect`'s and `product-slicer`'s syntheses for their own
   areas).
3. **CAMS** — `skills/cams-ux-heuristics/SKILL.md` (Procedure 2, "UX Design
   Guidance," read in full as the primary source; Procedures 1 and 3 —
   heuristic evaluation of existing UI and PR review — skimmed only, since
   both are post-code review triggers this persona doesn't own);
   `skills/ui-component-catalog/SKILL.md`.

## Principle table

| Principle | Source(s) | Status |
|---|---|---|
| Read human-provided constraints (brand, platform, quality attributes) as the source of truth before drafting anything | flexion-frontend-design Step 1 | gap → added |
| Choose an intentional aesthetic direction (purpose, tone, differentiation) rather than a generic default; name the generic-AI-interface anti-pattern explicitly (predictable centered layouts, purple-gradient-on-white) as the thing to avoid | flexion-frontend-design Design Thinking + built-in-critique-framework's First Impression dimension | gap → added |
| Required design-token categories: color (one dominant brand, 1–3 accents, a neutral scale, semantic success/warning/danger/info colors), typography (family/scale/weight/line-height), spacing scale, border-radius scale, shadow/elevation, motion (easing + duration) — declaring a category "none" is fine, silent absence is not | built-in-design-system-checklist | gap → added |
| Component-pattern coverage scoped to what the project's actual scenarios need, not a rote checklist (buttons, form fields, selection controls, cards, navigation, modals, toasts, tables — each with its real states) | built-in-design-system-checklist | gap → added |
| Cross-pattern coherence: the same token values reused consistently everywhere a pattern recurs (one focus treatment, one spacing scale, matching radii) — a coherence failure is a defect regardless of which specific value is "right" | built-in-design-system-checklist | gap → added |
| Once established, the design system is the binding constraint for every subsequent screen — a slice composes within it (arrangement, layout composition, micro-interactions, information hierarchy) but does not re-decide tokens, patterns, or the layout shell | flexion-frontend-design Mode 2 ("what you control" / "what you do not override") | gap → added — the establish-once/apply-per-slice shape itself, parallel to this roster's own `technology-bootstrap`/`architecture-design` split |
| Propose before restructuring — a change to the established layout shell or an existing pattern gets described and confirmed before it's applied, not silently evolved per slice | flexion-frontend-design General Rules | gap → added, matches this roster's existing "get approval for every real decision" convention |
| Reuse an existing, catalogued component before creating a new one; when a genuinely new pattern is needed, add it to the living catalog in the same pass | ui-component-catalog | gap → added |
| If multiple legitimate UX directions exist (e.g. alternative navigation flows), present them to the user for a decision — never silently pick one | flexion-frontend-design Step 2.1 | baseline confirmation of this roster's existing "planning personas ask, don't guess" convention |
| Preferences vs. Problems: taste-driven choices (palette, font family, a specific radius value, sidebar-vs-top-nav, light/dark theme) are never something to second-guess; only genuine problems (concrete usability/technical-debt harm) get flagged | flexion-frontend-design Mode 3 (Advisory) | gap → added |
| 11 consolidated usability heuristics (Nielsen's 10 + Shneiderman's 8, deduplicated) as the core design-quality lens: consistency, system feedback, error prevention/recovery, user control/freedom, recognition over recall, flexibility for novice and expert alike, real-world language, minimalist/aesthetic design, dialog closure, universal accessibility (narrowed per Contradiction 2), help/documentation | cams-ux-heuristics H1–H11 | gap → added — the core per-screen design-quality checklist |
| When two heuristics tension against each other (flexibility's shortcuts vs. minimalism's restraint; showing more context vs. decluttering), document the trade-off explicitly: what was chosen and why | cams-ux-heuristics Procedure 2 Step 3 | gap → added — converges with Flexion's Preferences/Problems distinction; both exist to stop a legitimate judgment call from being silently re-litigated later |
| Validate a design by mentally walking through it as the user would: can they tell what to do first, complete the task without leaving the screen, know what happened after each action, recover from mistakes, and does it match their expectation from the rest of the product | cams-ux-heuristics Procedure 2 Step 4 | gap → added |
| Five-dimension self-critique before presenting a screen design: First Impression (one clear primary surface, matches the system's aesthetic direction), Usability (interactive elements look interactive, destructive vs. constructive are visually distinct), Visual Hierarchy (importance maps to visual weight, spacing reinforces grouping), Consistency (every value traces to a declared token), Accessibility (semantic HTML by default, color never the sole signifier) | built-in-critique-framework | gap → added |
| Baseline copy quality is this persona's job too — interaction flow includes what the system says, not just how it's arranged: verb-leading, outcome-specific CTAs (destructive ones name the destruction); errors in what-happened/why/fix-it order with no jargon and no blame; empty states explain what's-here/why-empty/how-to-fill rather than "No results"; confirmations are action-labeled, past tense, brief; field labels are noun-leading with one consistent required-indicator convention | built-in-copy-checklist | gap → added |
| Real-world language: labels use the domain's own terms — what a domain expert would actually say out loud — not internal field/schema names; information ordered by the user's mental model, not the data model | cams-ux-heuristics H7 | gap → added — converges with the copy checklist's terminology-consistency rule |
| Accessibility is designed for *by construction* at the system level (a declared focus-state pattern every interactive element inherits, contrast-conformant color pairs in the palette, touch-target minimums in control patterns, a type scale that supports real heading hierarchy) — verifying that a specific built screen actually conforms is a different persona's job | built-in-wcag-subset's system-vs-component framing | resolves Contradiction 2 below; internal boundary decision |

## Contradictions — flagged and resolved

**1. Design and implementation as one act, vs. this roster's decide-before-
code separation.** `flexion-frontend-design` writes real, production styled
component code directly into the project — for it, "design" and "code" are
the same act. This roster's own convention (already established across
`product-slicer` → `software-architect` → a future `tdd-coach`) separates
deciding WHAT/HOW-structure from writing the implementation, and this
persona's own roster-row definition says it decides "before code is
written." Resolved toward the roster's existing separation: `screen-design`
produces a concrete visual artifact — a rendered mockup, using Claude Code's
actual rendering capability rather than staying pure-prose the way
`architecture-design` does, since "does this look good" is inherently a
visual question a paragraph answers poorly — but stops short of writing the
final production component code. That stays a later persona's job, once one
exists to hand it to.

**2. Accessibility folded into the same pass vs. split into its own
review.** All three consulted design-quality sources
(`flexion-frontend-design`'s own accessibility check, `cams-ux-heuristics`'
H10, the built-in WCAG subset) treat accessibility as one check inside the
same design/critique pass. This roster had already committed, before this
synthesis, to a hard split — `ux-designer` designs, `accessibility-engineer`
reviews WCAG compliance, and `ux-designer` "doesn't verify compliance
itself" (`PERSONAS.md` roster row 9). Resolved toward the roster's existing
commitment, using the WCAG-subset source's own system-vs-component framing
to draw a clean version of the line: this persona designs tokens and
patterns so accessibility criteria are satisfiable *by construction* — it
does not itself audit whether a specific built screen actually conforms.
That verification is `accessibility-engineer`'s job, once it exists.

**3. Severity scale for findings.** `cams-ux-heuristics` uses its own 0–4
numeric scale (Not a problem → Catastrophic) for its review-type findings.
This doesn't actually apply here: that scale belongs to the review
procedures (evaluating existing/changed UI), which aren't this persona's
job — pre-code design has no findings to rate, the same reason
`architecture-design` carries no severity taxonomy at all (that lives in
`architecture-review` instead). If a future review-type UI persona needs
one, it should reuse this roster's existing Critical/High/Medium/Low scale
for cross-persona comparability, not CAMS's numeric one.

## Top gaps folded into skills

1. `skills/design-system/SKILL.md` (new) — establish, or on request
   review/evolve, the project's design system once: aesthetic-direction
   thinking, required token categories, component-pattern coverage scoped
   to what the project's scenarios actually need, cross-pattern coherence,
   the Preferences-vs-Problems framing for the review/evolve case, propose-
   before-restructuring for layout-shell changes.
2. `skills/screen-design/SKILL.md` (new) — per-slice composition within the
   established system: layout/component composition, catalog-check-before-
   invent, interaction flow via the 11 consolidated heuristics plus the
   user-walkthrough validation technique, baseline copy quality for CTAs/
   errors/empty-states/confirmations/labels, the five-dimension self-
   critique pass before presenting, ask-instead-of-silently-picking when
   multiple legitimate directions exist, trade-off documentation when
   heuristics tension against each other.
3. Cross-cutting content shared by both skills (the accessible-by-
   construction boundary with `accessibility-engineer`, the "binding
   constraint once established" framing, the rendered-mockup-not-
   production-code boundary with implementation) lives in
   `agents/ux-designer/AGENT.md`'s system prompt.

## Note for later, not this persona's to resolve now

`cams-ux-heuristics` Procedures 1 and 3 (heuristic evaluation of existing UI;
PR review for UX) reveal a roster gap: nothing currently reviews *existing or
changed* UI code for general usability (the 11 heuristics), as distinct from
`accessibility-engineer`'s WCAG-specific review. Not creating a persona for
this now — flagging it the same way other sessions have flagged emergent
gaps, for a future decision on whether it's worth its own trigger or folds
into `code-reviewer`'s eventual scope.
