# Synthesis: accessibility-engineer

Internal only — never referenced from `agents/accessibility-engineer/AGENT.md`
or its backing skill. Delete once the full roster is built.

Roster row 8. One skill, not two — the mandate ("WCAG-minded UI review") is a
single trigger, unlike `ux-designer`'s establish-once/apply-per-slice split.
`ux-designer` already owns the pre-code half of accessibility (design tokens
and patterns that make conformance *possible* — a declared focus pattern,
contrast-conformant palette, touch-target minimums, a heading-capable type
scale); this persona owns confirming whether a specific rendered artifact
*actually* achieved that, which only becomes checkable once `screen-design`
has produced something real to check. `evals/example/slice-001.md`'s
accessibility-criteria placeholder, and the real HTML mockups
`design-system`/`screen-design` already produced for it, are the first real
target — see PERSONAS.md "Next to build."

## Sources consulted

1. **Flexion plugin** —
   `flexion-oea-coder/skills/flexion-frontend-design/references/built-in-wcag-subset.md`
   in full (the file `ux-designer`'s own synthesis explicitly deferred here);
   `flexion-scorm-package/agents/accessibility-inclusive-reviewer.md` in
   full, plus its cross-referenced `tests/design-cases/authentic-timing.md`
   for the one escalation example it names. The SCORM plugin is a different
   domain (e-learning modules, not general web UI) but this specific agent
   is the corpus's only source that reviews *built, drivable* interactive
   content rather than static markup, which is closer to what this persona
   actually inspects (a real rendered mockup) than either of the other two
   sources.
2. **Personal skills** — searched global `~/.claude/skills` and every
   project-level `.claude/skills` under `~/Documents/*` for accessibility,
   WCAG, keyboard-navigation, or screen-reader material: **nothing**. Same
   finding shape as `ux-designer`'s and `software-architect`'s syntheses for
   their own areas — noted, not fabricated.
3. **CAMS** — `skills/cams-testing-a11y/SKILL.md` in full. Heavily
   Playwright/axe-core-procedural (test file templates, npm commands, a
   specific repo's directory layout) — read for the principles underneath
   the procedure, not the procedure itself, per this plugin's own
   portability rule. What survives the framework-specific wrapping: the
   automated/manual layering, the severity taxonomy, and the
   disable-with-accountability pattern (Contradiction 2, below).

## Principle table

| Principle | Source(s) | Status |
|---|---|---|
| Six criteria are checkable from an artifact's declared markup/CSS alone, with no runtime needed: contrast (4.5:1 normal text / 3:1 large text and UI components), text alternatives (alt/aria-label, or explicit empty alt for decorative images), heading order (no skipped levels), focus-visible styling on every interactive element, touch-target sizing (~44×44), and label-input pairing | built-in-wcag-subset | gap → added — this is the persona's baseline check, run first, every time |
| A markup-only check must say so, explicitly, every time — never claim conformance for what wasn't actually verified. Runtime-only criteria (real keyboard operability, actual focus order across interaction, screen-reader announcement timing, status-message announcement) get named as *not yet checked*, not silently passed | built-in-wcag-subset ("honesty in details"); accessibility-inclusive-reviewer (evidence typing); cams-testing-a11y (axe catches "~30-40% of issues", manual testing still needed) | three-way convergence, differently framed by each source — resolved toward one explicit finding attribute (see below), not three separate disclaimers |
| A rendered mockup (real HTML/CSS a browser can actually load) is not the same evidence tier as a text description of an intended interaction — drive it for real: tab through it, look at what receives visible focus, read the DOM order a screen reader would hit — rather than inferring purely from reading markup | accessibility-inclusive-reviewer ("do not infer accessibility from reading markup alone when running it is available") | gap → added — the reason this persona uses browser automation instead of only reading files |
| AAA-level findings and genuinely ambiguous judgment calls are logged as non-blocking preferences, not treated the same as an AA-level failure | built-in-wcag-subset | gap → added — keeps this persona from inflating a nice-to-have into a blocker |
| An interaction with *no* accessible path at all for a required action is the ceiling of severity, regardless of how minor the rest of the review reads | accessibility-inclusive-reviewer | gap → added |
| A genuine functional requirement doesn't get quietly weakened or deleted to resolve an accessibility complaint — find the accessible way to preserve it; if none exists, that's a finding to escalate, not a scope change to make unilaterally | accessibility-inclusive-reviewer (generalized past its own timed-assessment framing) | gap → added |
| Never accept a separate "accessible version" as equivalent to fixing the actual thing — accessibility has to be the primary route, not an alternate one bolted on | accessibility-inclusive-reviewer | gap → added |
| Findings are severity-ranked and prioritized in that order when there's more than one | cams-testing-a11y (critical/serious/moderate/minor); accessibility-inclusive-reviewer (blocking/non-blocking) | baseline, but this plugin's own Critical/High/Medium/Low scale is used instead of either source's native one — see Contradiction 1 |
| A check that can't be fixed immediately doesn't get silently dropped *or* silently left blocking forever — it gets named, with why, and stays visible until someone actually closes it | cams-testing-a11y (disable-with-documentation-and-fix-plan) | gap → added, reframed — see Contradiction 2 |
| Review what the artifact in front of you actually is; a pre-existing gap in a screen this review wasn't asked to touch is lower priority, not a blocker | derived from this roster's own `devsecops-engineer` convention, applied here | baseline — internal consistency with the rest of the roster, not sourced from the accessibility corpus itself |

## Contradictions — flagged and resolved

**1. Three incompatible severity vocabularies.** `cams-testing-a11y` uses
axe-core's native critical/serious/moderate/minor. `built-in-wcag-subset`
uses a binary clear_problem/preference split. `accessibility-inclusive-reviewer`
uses blocking/non-blocking plus a separate evidence-type tag
(automated_test/expert_review/design_inference). None of the three agree,
and none of them is the vocabulary the rest of this roster already uses.

**Resolved toward this plugin's existing Critical/High/Medium/Low scale** —
the same one `devsecops-engineer` and `architecture-review` share, adopted
there for exactly this reason: findings from different personas need to
stay comparable without a reader learning a new scale per persona. Mapped
onto accessibility findings by completeness of exclusion rather than by
category: Critical is a required action with no accessible path at all;
High is a clear WCAG A/AA failure with an identifiable affected group and a
specific fix; Medium is a real but narrower gap (a judgment-call criterion,
or a fix that needs a larger change than this one artifact); Low is an
AAA-level or cosmetic enhancement. This is the same principle
`devsecops-engineer`'s own synthesis already states for its domain —
severity tracks the real consequence, not which checklist item it came
from — applied here instead of importing any one source's native scale.

**2. Is disabling/suppressing a failing check ever legitimate?**
`built-in-wcag-subset` and `accessibility-inclusive-reviewer` both treat a
clear_problem/blocking finding as something to fix or escalate — neither
names a "known, accepted, tracked" state as a fourth option.
`cams-testing-a11y` explicitly provides one (`DISABLED_A11Y_RULES` +
`KNOWN_ISSUES.md`, with a required reason, fix plan, target date, and
tracking link), while simultaneously calling it rare and warning against
overuse.

These read as opposed at first — permissive vs. strict — but the CAMS
mechanism, read closely, isn't actually a suppression path; it's an
accountability path. A silently-passing check is what this roster's own
`devsecops-engineer` synthesis already calls a control that "gets quieter
the longer it finds nothing" and treats as a failure mode in itself. CAMS's
pattern is the opposite of that: it makes the exception *louder*, not
quieter — visible, dated, justified, and owned. **Resolved toward adopting
the underlying accountability discipline, not the specific file mechanism**
(a CAMS-specific `KNOWN_ISSUES.md`/Playwright-config convention would fail
this plugin's own portability rule). A finding this persona can't get fixed
in the pass it's found doesn't disappear and doesn't block forever either —
it's named as accepted-for-now with a stated reason, in the same "Open
questions, carried forward" place every other unresolved item in this
roster already lives, per the Durable Finding already on record in
PERSONAS.md ("an unresolved item that isn't this skill's job to fix is
still this skill's job to keep visible").

## Scope decisions, not sourced from a contradiction

**This persona reviews; it does not design.** All three sources blend
design and verification to some degree (`built-in-wcag-subset` is invoked
*by* a design-generation orchestrator; CAMS's skill sits inside a
development workflow, fixing violations as it finds them by editing
component code). Resolved toward the split this roster already committed
to in `ux-designer`'s own synthesis and its `AGENT.md`: `ux-designer`
designs for accessibility by construction and does not verify it;
`accessibility-engineer` verifies and does not redesign. A finding routes
back to whichever persona owns the artifact (`ux-designer` for a mockup,
later a code-writing persona once one exists) — this persona reports,
recommends a fix, and never edits someone else's rendered artifact or
component itself, the same non-negotiable `devsecops-engineer` already
holds for application code.

**No AskUserQuestion.** Every planning persona in this roster asks before
guessing at something load-bearing. This persona doesn't need to: an
ambiguous or AAA-level finding is logged as a Low/preference item rather
than escalated into a live question, matching how `devsecops-engineer`'s
own review/posture skills (as opposed to its requirements skills) never
ask either. That makes this the first persona in the roster with nothing
that blocks on a human mid-run — see the `background: true` decision in
`AGENT.md`, and PERSONAS.md's "Orchestrator v2" note, which has been
waiting on a second reviewer like this to exist before that per-skill-vs-
per-agent parallelizability question was even answerable with a real case.

**Scope of what gets driven, given today's roster.** `screen-design`
renders one static HTML file per visually distinct state (success, empty,
error, etc.) rather than one live app with real interaction wiring between
them. A within-page keyboard tab-through, computed focus-visibility, and
computed contrast are all real checks against that artifact today. A
check that depends on wiring between states — does focus move to a
confirmation message after a real submit, does an aria-live region
actually fire on a real transition — has nothing to run against yet until
a later, code-writing persona exists; those get named as deferred, not
skipped silently, the same as the accessibility-criteria placeholder
itself has been handled since slice-001 was first cut.
