# accessibility-engineer:accessibility-review — eval summary

**8/9 PASS.** One mechanical FAIL (`skill-invoked`), all eight substantive
`llm` graders PASS.

| Grader | Result |
|---|---|
| `skill-invoked` | FAIL |
| `catches-no-keyboard-path-on-required-interaction-critical` | PASS |
| `rejects-accessible-version-elsewhere-as-resolution` | PASS |
| `preserves-requirement-instead-of-removing-it` | PASS |
| `catches-non-semantic-interactive-div` | PASS |
| `catches-missing-heading-on-status-title` | PASS |
| `catches-missing-live-region-on-status-block` | PASS |
| `no-false-positive-on-correct-focus-style` | PASS |
| `produces-given-when-then-acceptance-criteria-not-just-findings` | PASS |

## The one failure, and why it isn't scored as a wash

The emulated persona never wrote the harness's required first line
("Skills consulted: <path>"). Per this harness's own rule, that's treated
as if nothing was consulted, so `skill-invoked` is graded FAIL on the
letter of that mechanical check — not overridden, since (unlike the
`ux-designer:screen-design` precedent where a harness limitation produced
a false failure) this is a real omission by the run, not an artifact of
the stand-in harness.

Worth recording as a genuine emulation-fidelity gap rather than smoothing
over: this run's spawned agent didn't stay inside the intended
Read/Grep/Glob-only dry-run grant. `general-purpose` subagents have full
tool access in this environment, and the harness has no mechanism to
actually enforce the restriction described in `agent-eval`'s own
procedure — so the agent opened a real Chrome tab and drove the mockup
live (real `Tab` keypresses, `getComputedStyle`/contrast math via the
WCAG relative-luminance formula, `getBoundingClientRect` for touch
targets, the real accessibility tree) rather than reasoning over the HTML
text alone. It never wrote or edited a repo file, so it stayed side-
effect-free in that sense, but it is not the purely-textual dry run the
procedure assumes, and the missing self-report line may be a symptom of
the same distraction — it was busy actually executing checks instead of
following the literal formatting instruction.

Two things are true at once here, and both are worth keeping: the
mechanical check genuinely failed and is scored that way, *and* the
substantive output is unusually strong independent evidence that
`skills/accessibility-review/SKILL.md` was actually read and applied —
the eight-check structure (including both checks added after this
project's own dogfood run), the Critical/High/Medium/Low scale, the
confirmed-now/deferred acceptance-criteria split, and the "Not yet
verifiable"/"Open questions" sections all match that file's specific
structure and don't appear from general accessibility knowledge alone.
If this case is re-run, worth spawning the emulation agent with an
explicitly tool-restricted subagent definition if this environment gains
one, to get a cleaner test of the self-report instruction in isolation.

## What the output actually caught, worth noting past the grading table

The fixture was built with one deliberate escalation trap (an "accessible
version available elsewhere" link meant to tempt an under-flag) and the
run didn't take it — it named the link as insufficient in the same
sentence as flagging the primary interface at full severity. It also
independently found and correctly triaged a defect the fixture wasn't
explicitly built to test: `.status-dot`'s `color` and `background-color`
computed to the exact same value (1.00:1 contrast against itself),
correctly reasoned as Medium rather than High since the adjacent text
carries the same information redundantly — the kind of judgment call this
skill's severity section exists to produce, applied to something outside
the grader list entirely.
