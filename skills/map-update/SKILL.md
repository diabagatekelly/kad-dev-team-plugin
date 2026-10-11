---
name: map-update
description: Regenerate the architecture map from the real codebase — actual import edges, public exports, external packages — and diff it against whatever was recorded before, mechanically flagging duplication candidates and wrong-direction dependency edges. The only skill that writes the map (docs/architecture-map.md at the app root). Use when asked to update the architecture map, after code changes, once per implementation candidate (throwaway, worktree-scoped) inside a graded build, and once for real after a slice is finalized.
---

# Map Update

## What this does

Two things, always together: regenerate the map from what's actually in
the codebase right now, and diff that fresh extraction against the map's
previous version. The diff is what makes this useful to a reviewer — a
list of what changed, plus two kinds of mechanically-flagged candidate,
rather than a reviewer having to re-derive the whole graph from scratch on
every pass.

This is the only skill in this persona that ever writes anything to the
map. `map-query` only ever reads what this skill most recently produced.

The map is the only file this skill writes. Never edit application code,
even to fix an edge or a duplicate you just flagged: name it in the
report and leave the fix to whoever owns that call.

## Extraction: mechanical, from real source, no installed tooling required

Walk the project's source files by extension, and for each recognized
language, extract:

- **Internal import edges** — parse each file's actual import/require
  statements and resolve them to other files in the project (not external
  packages). Use each language's real import syntax: `import`/`export
  ... from`/`require` for JS/TS, `import`/`from ... import` for Python
  (including the `from <package> import <member>` idiom — resolve each
  imported member name against the project's own file index too, since a
  plain module-path regex misses this form), and the equivalent statement
  form for any other language the project uses. A specifier that doesn't
  resolve to a file inside the project is an external reference, not an
  internal edge.
- **External package references** — the same import statements, where the
  target doesn't resolve inside the project. Record the package name, not
  every individual symbol pulled from it.
- **Public exports** — each file's actual exported names: functions,
  classes, types, constants exported from the module's own top level. Not
  every symbol defined in the file, only what's actually exported and
  therefore reachable from elsewhere.

A file in a language with no recognized import/export syntax yet still
appears in the map's module list (present, not silently dropped) but
renders with no edges and no exports rather than a guessed-at set — the
same "visible and honest, never guessed" handling untiered modules get.

This is grep/parse-level work against real file text — no compiler, no
language server, no project-specific build step, and no dependency on any
tool not already part of this skill's own reasoning. That's what keeps the
map portable across whatever language or stack a given project uses.

## Tiers: carried forward, never invented here

Tiers come from `architecture-design`'s own decisions, not from anything
this skill derives. When updating the map:

- If a module already carries a tier from a prior map version, keep it
  unless something explicitly tells you it changed.
- If a module is newly touched by a slice whose design doc states an
  importance ordering, apply that ordering to the modules it names.
- If a module has no tier from either source, record it as **untiered** —
  explicitly, not omitted and not inferred from its imports. Inferring a
  tier from the import graph is circular: a module that already violates
  the Dependency Rule would corrupt the very inference meant to catch that
  violation.

## Diffing against the prior map

Compare the fresh extraction to whatever the map's previous version
recorded, and report, in plain terms:

- **New modules** and **removed modules**.
- **New edges** and **removed edges** (internal and external, separately).
- **New exports** and **removed exports**, per module.

## Two mechanical candidate flags — facts, never verdicts

**Duplication candidates.** Two modules whose exported names/signatures
overlap substantially, or whose internal import targets overlap
substantially, get flagged as a candidate pair. Check mechanically, not by eye:
compare every new or changed module's exported names against every other
module's, and flag any name exported by two modules. State exactly what's
shared (the overlapping exports or import targets) and where each side
lives. Do not characterize whether the overlap is a real duplicate or a
coincidence — a shared shape between two modules serving genuinely
different, independently-evolving concerns is expected and not a defect;
telling the two apart is downstream judgment (`architecture-review` for an
already-built pair, `architecture-design` for a pre-write query), never
this skill's call.

**Wrong-direction edges.** A new internal edge where the importing
module's recorded tier is more important (numerically lower, if tiers are
ordered that way) than the imported module's tier is flagged as a
candidate wrong-direction edge — checked purely against tiers already on
record, never adjudicated here. An edge where either side is untiered is
reported as untiered-direction-unknown, not silently skipped and not
guessed toward either verdict.

## Output: structured table plus short narrative

```markdown
# Architecture map — updated <date>

## Modules
| Path | Tier | Internal edges (imports) | External packages | Public exports |
|---|---|---|---|---|
| ... | tier N \| untiered | ... | ... | ... |

## Changes since the prior map
New/removed modules, edges, and exports, stated plainly.

## Duplication candidates
- `<path A>` and `<path B>` share <the overlapping exports or import targets>. Real duplicate or coincidence: not decided here.
(or) None found.

## Wrong-direction candidates
- `<importer>` (tier N) → `<imported>` (tier M) — new | carried forward
(or) None found.

Untiered, direction unknown:
- `<importer>` (<tier or untiered>) → `<imported>` (<tier or untiered>)
```

Each candidate line states the shared facts and stops. No "looks like", no
"probably intentional", no history read from comments to argue either way:
any sentence about *why* the overlap exists is a verdict.

No severity on anything in this output, no ranking, no recommendation.
Whoever reads this diff — a reviewer, `architecture-design` on the next
slice, `architecture-review` — decides what any of it means.

## Two invocation modes

**Throwaway, inside a graded build.** When run against one candidate's own
isolated worktree, diff against the real project's last persisted map (not
against the other candidate's worktree), and hand the result to that
candidate's reviewers as precomputed context. This run never overwrites
the real persisted map — it exists only to inform that candidate's grading
pass, and is discarded once grading is done.

**Real, after a slice is finalized.** Run once against the actual working
tree once the slice's real implementation lands. This run's output
replaces the persisted map — it becomes the map the next slice's
`map-query` reads and the next `map-update` diffs against.

## Where the map lives

The map is project-level infrastructure, not a per-slice artifact, and
it always lives at `docs/architecture-map.md` at the root of the app — the directory that holds the app's manifest (`package.json`, `pyproject.toml`, `go.mod`, ...), wherever that sits in the repository. A real run reads the prior map there and
overwrites it, creating `docs/` if it doesn't exist; with no prior map,
everything is new. A throwaway run reads the real project's map from that
path and writes nothing.

## No AskUserQuestion

Nothing here ever depends on information only a human can supply in the
moment; the map's location is fixed (see above). Tiers are read from what's already decided; a module or edge this
skill can't resolve renders as an explicit, honest unknown rather than a
question. This skill runs to completion every time, including inside a
worktree-isolated candidate build where no one is available to answer
anything mid-run.
