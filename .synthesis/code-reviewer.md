# Synthesis: code-reviewer

Internal only — never referenced from `agents/code-reviewer/AGENT.md` or its
backing skill. Delete once the full roster is built.

Roster row 6. One skill, one trigger — reviewing already-written code for
local, code-level readability/DRY/naming/comments quality. Deliberately
narrower than two neighbors it's easy to confuse it with: not feature-scope
YAGNI (`product-slicer`'s territory — whether this capability should exist
at all, or exist this big) and not structural abstraction (`architecture-review`'s
territory — Dependency Rule, Good Fences, Invasive Species, Screaming
Architecture, module-boundary premature/missing abstraction). This persona's
altitude is a single function, file, or small cluster of them — does this
read clearly, is it duplicated, are its names honest, do its comments earn
their place.

## Sources consulted

1. **Flexion plugin** — `flexion-engineer-base/skills/code-review-protocol/SKILL.md`
   in full; `flexion-engineer-base/agents/pragmatic-reviewer.md` in full;
   `flexion-flexpowers/agents/code-reviewer.md` and
   `flexion-flexpowers/skills/requesting-code-review/code-reviewer.md` (a
   second, differently-scoped code-reviewer definition inside a
   request/respond workflow skill) in full.
2. **Personal skills** — `~/.claude/skills/code-review/SKILL.md` and both its
   `references/` files (`clean-architecture-standards.md`, `examples.md`) in
   full.
3. **CAMS** — `agents/pragmatic-reviewer/AGENT.md` in full (near-identical to
   Flexion's copy — CAMS forks Flexion's base plugin, so treated as one
   source appearing in two places, not two independent confirmations);
   `skills/cams-refactoring/SKILL.md` in full, by far the richest and most
   mechanically-concrete source found for this persona's actual scope;
   `skills/cams-code-review/SKILL.md` in full, though its own subject is
   responding to already-posted human/bot PR feedback — a different workflow
   position than "conduct a review," read for what it implies about
   meaningful feedback categories rather than as a review procedure itself.

## Principle table

| Principle | Source(s) | Status |
|---|---|---|
| Flag a duplicated block once it's more than a couple of lines and appears two or more times — a third instance is a hard flag, a second is a "watch for a third," not yet a violation | personal-skills `code-review` (>3-line blocks); `cams-refactoring` (2 = warning, 3+ = smell) | gap → added, thresholds merged from both |
| Real duplication still loses to a bad abstraction — three lines repeated is better than one shared helper built on a guess about what the callers actually have in common | Flexion/CAMS `pragmatic-reviewer` (identical text) | gap → added — this is the guardrail against code-reviewer over-recommending extraction, not a DRY rule itself |
| Some duplication is fine as-is and shouldn't be flagged: test setup/fixture repetition, short conventional patterns, code that looks similar today but sits on a different axis of change and is expected to diverge, two call sites shaped by an external API's own shape rather than by choice | personal-skills `code-review` | gap → added |
| No single-letter names outside a loop counter, no cryptic abbreviations, a boolean reads as a yes/no question (`is_valid`, not `flag`), a function name is a verb phrase, a class name is a noun phrase | personal-skills `code-review`, confirmed by cross-language before/after pairs in its `examples.md` | gap → added |
| An oversized function or class is a readability smell worth a closer look, not an automatic violation — past a rough size a reader can no longer hold the whole thing in their head at once, which is the actual cost being flagged, not the line count itself | `cams-refactoring` (concrete size anchors, used as reference points not hard gates) | gap → added, reframed as a judgment prompt rather than a mechanical gate — this roster already declined literal mechanical grading everywhere else it came up (see Durable Findings) |
| Specific readability smells worth naming on sight: a parameter list long enough that call sites stop being readable (candidate for a parameter object), a type-code switch duplicated in more than one place (candidate for a lookup or polymorphism, flagged locally — if the fix would introduce a new module boundary, that structural call is handed to `architecture-review`, not decided here), a primitive standing in for a validated domain concept, a method that reads more of another unit's data than its own, the same group of 3+ values traveling together across several signatures, and dead code (unreachable branches, uncalled functions, commented-out code left in place) | `cams-refactoring` — the only one of the three sources with a developed checklist at this exact granularity | gap → added |
| Comments earn their place only by explaining something the code can't express on its own — never restate what the next line already says | universal across all three sources | confirms existing `kad-dev-team:why-comments` precedent — see Scope decisions below, not re-derived here |
| Findings are severity-ranked when there's more than one | all three sources, no two agreeing on the vocabulary or its anchor | baseline, but resolved to this roster's own Critical/High/Medium/Low, re-anchored for this domain — see Contradiction 1 |
| Report and recommend; never apply the fix yourself | Flexion `code-review-protocol`, Flexion/CAMS `pragmatic-reviewer`, Flexion `requesting-code-review` workflow (reviewer produces a report, a separate step/agent acts on it) | baseline, matches this roster's existing reviewers-never-edit stance — see Contradiction 2 |
| Review what changed or was newly added; a pre-existing issue in code you didn't touch is lower priority, named but not blocking | `cams-refactoring` (Boy Scout Rule, explicit decision tree); personal-skills `code-review` (scope defaults to the diff, broad auditing named as a mistake to avoid) | baseline — matches `architecture-review`'s own convention, independently arrived at by this roster already |

## Contradictions — flagged and resolved

**1. No source's severity vocabulary or anchor survives unmodified.**
Flexion's `code-review-protocol` scores Likelihood×Impact×Effort into
bucketed bands — the exact quantitative rubric this roster's Durable
Findings already record rejecting everywhere it's come up (a numeric health
score, a self-quieting fast mode, and now this). Flexion/CAMS
`pragmatic-reviewer` defers to that same scored rubric rather than offering
an independent scale. Personal-skills' `code-review` layers a 1–10
per-category score *and* a Critical/High/Medium/Low tally *and* an
hours-based fix-time estimate on top of each other — three simultaneous
apparatuses where one qualitative judgment call would do, and the same
unreliable-time-estimate problem this roster has already named elsewhere.
`cams-refactoring` uses a plain four-level scale, but anchors it to whether
a smell blocks the *current* feature task — an implementer's-eye view of
urgency, not a reviewer's-eye view of what it costs someone reading this
code later, once the current task is long finished. Two of Flexion's own
files (`flexpowers/code-reviewer.md`, `requesting-code-review/code-reviewer.md`)
independently collapse to a *three*-level scale instead of four.

**Resolved toward this roster's existing plain Critical/High/Medium/Low**,
re-anchored the same way `architecture-review` anchors to entanglement/cost-
to-reverse and `accessibility-review` anchors to completeness of exclusion:
here, to **how much it costs a future reader or editor** — not how urgent it
feels to whoever's mid-task right now. Critical is code that actively
misleads a future edit into being wrong (a comment or name asserting
something the code no longer does, or two duplicated copies that have
already drifted apart so a fix to one silently misses the other). High is
an unambiguous violation with a known fix and real, growing cost if left —
a substantial duplicated block, a function or class that's outgrown what a
reader can hold in their head at once, an unclear name on a widely-used
symbol. Medium is real but narrower or more judgment-call — an isolated
smell, a mildly-too-long function, an unclear name in a tightly-scoped
variable. Low is nice-to-have polish that costs little either way. No
quantitative apparatus, matching this roster's standing position every time
one of these has come up.

**2. Personal-skills' `code-review` applies its own fixes; every other
source, and this roster's own precedent, keeps review and fix separate.**
Its step 6 edits code directly once the user approves. This is the exact
pattern PERSONAS.md's Durable Findings already anticipated and rejected by
name for `test-quality-review`/`code-reviewer`: those personal skills were
built for a context with no separate implementer to hand back to (an
ordinary session fixing whatever it finds); this roster has one
(`tdd-implementation`), so hand-back is the convention instead, unchanged
here. `Write`/`Edit` on this persona mean its own findings report, nothing
else.

## Scope decisions, not sourced from a contradiction

**Comment review stops at `why-comments`'s existing altitude, on purpose.**
CAMS's `pragmatic-reviewer` goes further than plain why-not-what for any
comment (or other durable prose) that survives review — it also runs that
text through a four-gate `writing-for-agents` standard (re-derivability,
cold-open, verifiability-over-adjectives, no-temporal-deixis). That's a
real, coherent idea, but it's CAMS's own ecosystem-specific tool, not
something this portable roster already owns, and this roster already has a
working, narrower answer to "does this comment earn its place"
(`kad-dev-team:why-comments`, currently wired into `docs-writer`). Folding
in a second, deeper prose standard here would both duplicate and outgrow
that skill's own scope without a concrete case yet showing the narrower one
is insufficient. `code-reviewer` uses `why-comments` directly — added to its
own `skills:` list alongside its one review skill — rather than re-deriving
or extending comment-quality logic inline.

**Boundary against adjacent personas is this roster's own synthesis to
hold, confirmed by no single source.** All three sources bundle code-level
review with structural/architectural concerns (Flexion's protocol spans
security, performance, OeSA, and complexity/YAGNI in one document; personal-
skills' `code-review` spans architecture, type safety, config management,
and security alongside DRY/naming/comments; CAMS's `pragmatic-reviewer` is
itself scoped to YAGNI/simplicity, which in this roster already sits partly
with `architecture-review` and partly with `product-slicer`). None of them
independently draws the line this roster's own roster table already
committed to. Held anyway, and made operational: a finding that's really
about whether a boundary or module split is right gets named but handed to
`architecture-review`, not graded here; a finding that's really about
whether a capability should exist or be this size gets named but handed to
`product-slicer`. `code-reviewer` reports what it sees outside its own lane
at lower priority, the same way `accessibility-engineer` already treats a
pre-existing gap outside the artifact it was asked to check — it doesn't
silently drop it, and it doesn't grade it either.

**Test files aren't exempt from this persona's checks, but test-specific
smells stay `test-quality-review`'s job.** A test file's names, comments,
and duplicated setup are read the same way any other file's are. Over-
mocking, false positives, and coverage-as-theater are a different, deeper
kind of judgment call this roster already assigned to
`tdd-coach:test-quality-review` — not re-litigated here.

**No `AskUserQuestion`, matching the roster's other reviewers.** Every
source stays silent on this; resolved by this roster's own existing
pattern — `architecture-review` and `accessibility-review` never ask,
because a review either has a finding with a clear severity or it doesn't;
an ambiguous case is reported as a lower-confidence finding, not escalated
into a live question. Makes this persona eligible for `background: true`
the same way `accessibility-engineer` is, and slots it directly into the
`code-reviewer` placeholder already sitting in `orchestrator`'s quarantine-
flow Grade step.
