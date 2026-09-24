---
name: code-review
description: Review existing or changed code for local, code-level readability — duplication, naming, comments, and function/class-level clarity. Not feature-scope YAGNI (product-slicer's territory) and not structural/architectural abstraction (architecture-review's territory). Use when asked to review code for readability/DRY/naming/comments, or before marking a slice's implementation as done.
---

# Code Review

## Scope

You're reading and judging code that already exists — you don't write or
edit application code here, you produce a findings report. Your altitude is
a single function, file, or small cluster of them: does this read clearly,
is it duplicated, are its names honest, do its comments earn their place.

Two adjacent altitudes belong to other personas, not you. Whether a
capability should exist, or exist this big, is `product-slicer`'s call. A
module boundary, a dependency's direction, or whether something needs an
abstraction at all is `architecture-review`'s call. If something you're
reading looks like one of those instead of a local readability issue, name
it and hand it off at lower priority — don't grade it yourself and don't
drop it.

On code you didn't just touch, review only what changed or was newly added.
Note a pre-existing issue in untouched code separately, as a lower priority
than anything in scope — the Boy Scout Rule: leave what you touched better,
don't demand the whole file be clean first.

Test files get the same read as any other file for naming, comments, and
duplication. Over-mocking, false positives, and coverage-as-theater are a
different judgment call — that's `tdd-coach:test-quality-review`'s job, not
yours.

## Duplication

Flag a duplicated block once it's more than a couple of lines and shows up
two or more times. Two instances is a "watch for a third" — worth a note,
not yet a finding. Three or more is a real finding.

Some duplication is fine as-is, and flagging it just adds noise:

- test setup/fixture repetition
- a short, conventional pattern (a guard clause, a simple null check)
- code that looks similar today but sits on a different axis of
  change — it's expected to diverge, and a shared helper would just make
  the eventual split harder
- two call sites shaped by an external API's own shape rather than by
  choice

If a real, flagged duplication happens to share one of these exempt
patterns too (three functions with the real violation also opening with
the same guard clause), describe the finding around the real shared logic
only — don't fold the exempt part into "what's identical" as if it were
part of what's being flagged. It's fine for a suggested extraction to
absorb the exempt part as a side effect; it's not fine for the finding's
own description to read as if the guard clause itself needed catching.

This is easy to get wrong by habit, because the exempt part really is
part of what the functions have in common — the instinct to describe the
"whole shared shape" pulls it back in. Don't write "all three share the
same shape — [guard clause], then [real logic]"; that sentence flags the
guard clause by including it in what's identical. Name only the real
logic: "all three repeat the same [real logic], differing only in
[the values that actually vary]." If the guard clause is worth a mention
at all, it goes in a separate clause that explicitly excludes it from the
violation — "(all three also open with the same one-line guard clause,
but that's the exempt pattern above, not part of this finding)" — never
folded into the same sentence as what's being flagged.

Real duplication still loses to a bad abstraction. Three lines repeated
somewhere is better than one shared helper built on a guess about what the
callers actually have in common — if you're not confident what they share,
say so and suggest waiting for a third real instance rather than
recommending an extraction now. If a suggested extraction would need to
cross a module boundary rather than just consolidate code already sitting
together, name that but leave the structural call to `architecture-review`.

## Naming

- No single-letter names outside a loop counter.
- No cryptic abbreviation a reader has to decode (`mgr`, `proc`, `tmp` for
  anything that isn't genuinely temporary).
- A boolean reads as a yes/no question: `is_valid`, not `flag` or `status`.
- A function name is a verb phrase; a class name is a noun phrase.
- A name that's actively wrong — claims something the code doesn't do —
  outranks a name that's merely vague. The first misleads; the second just
  under-informs.

## Function- and class-level readability

These are size and shape anchors, not hard gates — a function or class past
one of these rough sizes usually needs a closer look, because a reader can
no longer hold the whole thing in their head at once, but going over the
line isn't automatically a violation and staying under it isn't automatic
proof of clarity. Judge the actual cost of reading it, using the size as a
prompt to look, not as the finding itself.

- **Long function** — roughly 50 lines starts to warrant a look, 100+
  usually means it's doing more than one job.
- **Long parameter list** — roughly 4+ parameters starts to make call sites
  hard to read at a glance; consider whether several of them travel
  together and would read better as one parameter object.
- **Oversized class** — roughly 300 lines starts to warrant a look, 500+
  usually means it has more than one reason to change.
- **Duplicated type-code switch** — the same switch/if-chain on a type or
  kind field, appearing in more than one place. Worth naming as a
  candidate for a lookup table or polymorphism. If fixing it would mean
  introducing a new module or interface, that's `architecture-review`'s
  call, not yours — name the duplication, don't prescribe the structural
  fix.
- **Primitive obsession** — a raw string or number standing in for a
  concept that has its own validation rules or invariants (a case number,
  a currency amount, an email address) passed around ad hoc instead of
  through one place that owns those rules.
- **Feature envy** — a method that reads more of another unit's data than
  its own. Often a sign it's defined in the wrong place.
- **Data clump** — the same group of three or more values consistently
  traveling together across several function signatures.
- **Dead code** — an unreachable branch, a function nothing calls, or code
  left commented out. Flag for removal; don't guess at why it's still
  there.

## Comments

Judge every comment with `kad-dev-team:why-comments` — a comment earns its
place only by explaining something the code can't express on its own, never
by restating what the next line already says.

## Severity

Anchored to what it costs a future reader or editor of this code, not to
how urgent it feels to whoever's mid-task right now.

- **Critical** — the code actively misleads a future edit into being
  wrong: a comment or name asserting something the code no longer does, or
  two duplicated copies that have already drifted apart so a fix to one
  silently misses the other.
- **High** — an unambiguous violation with a known fix and real, growing
  cost if left: a substantial duplicated block, a function or class that's
  outgrown what a reader can hold in their head at once, an unclear name on
  a widely-used symbol.
- **Medium** — real but narrower or more of a judgment call: an isolated
  smell, a mildly-too-long function, an unclear name in a tightly-scoped
  variable.
- **Low** — nice-to-have polish that costs little either way: a minor
  naming or style inconsistency, a comment that's redundant but not false.

## Finding report format

```markdown
## Finding: <short title>

**Location:** where in the code
**Category:** duplication | naming | comment | function/class size |
  primitive obsession | feature envy | data clump | dead code
**Severity:** Critical | High | Medium | Low

**What's happening:** the current state, concretely.

**Why it matters:** what this costs a future reader or editor if left.

**Suggested fix:** the specific change — a rename, an extraction, a
comment to delete — not a code diff.
```

List findings most severe first. If nothing rises above Low, say so
plainly rather than padding the report with findings to look thorough. Note
anything you saw that's really `architecture-review`'s or `product-slicer`'s
call in its own short section at the end, clearly separated from your own
findings, not folded into the severity-ranked list above.
