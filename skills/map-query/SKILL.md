---
name: map-query
description: Answer "does something like this already exist?" from the architecture map (docs/architecture-map.md at the app root) — a comparable module or interface at the structural level, a comparable function or helper at the implementation level. Use whenever someone asks to check the architecture map, or asks before designing or writing code whether something comparable exists. Read-only; never scans the source instead and never judges whether a candidate is close enough to reuse.
---

# Map Query

## What this answers, and what it doesn't

One question, asked at whatever granularity the asker operates at:
**does something comparable to this already exist in the codebase?** At
the structural level (`architecture-design`'s altitude — no file paths, no
function signatures) that means a comparable module, interface, or
boundary. At the implementation level (`tdd-implementation`'s altitude —
below `architecture-design`'s conceptual grain, inside what actually gets
written) that means a comparable function, class, or helper.

It does not answer whether a returned candidate is *actually* the same
thing, close enough to reuse, or a coincidence not worth reusing. That's
the asking persona's call, informed by what this skill hands back — never
this skill's own conclusion.

## Where the map lives

The map is always `docs/architecture-map.md` at the root of the app — the directory that holds the app's manifest (`package.json`, `pyproject.toml`, `go.mod`, ...), wherever that sits in the repository. Read it there. If no file is there, no map
exists yet — don't look for one anywhere else.

## Read-only, always

This skill never writes anything, never edits anything, and never
regenerates the map from source. It reads whatever `map-update` last
recorded and reports from that. Two honest outcomes follow from this:

- **No map exists yet.** Say so plainly. This is a complete, valid answer
  — not a reason to fall back to scanning the codebase live, which is
  `map-update`'s job, not this one's. Blurring that line would mean this
  skill sometimes does a full regenerate and sometimes doesn't, which
  defeats the reason the two skills are split in the first place.
- **A map exists but may be stale.** If the map records when it was last
  generated, say how long ago that was relative to what you can tell about
  recent changes (e.g., the asking persona mentions a just-finished slice
  the map predates). Don't silently trust a map that's plausibly out of
  date — name the staleness and let the asker decide whether to ask for a
  fresh `map-update` first.

## How to answer a structural query

Read the map's per-module records: path, tier, internal/external edges,
public exports. Look for a module whose recorded purpose, boundary shape,
or exports plausibly overlap with what's being asked about. Report every
plausible candidate, not just the closest-looking one — a narrow return
that misses a real candidate is worse than a slightly noisy one, since the
asker is the one equipped to rule candidates out.

For each candidate, report only what the map actually records: its path,
its tier (or "untiered" if the map doesn't have one for it), what it
exports, and what it depends on. Don't characterize *how similar* it is in
your own words beyond the shared facts themselves — "both expose a
`findByCaseId`-shaped read method" is a fact; "this is basically the same
thing" is a verdict.

## How to answer an implementation query

Read the map's recorded exports across modules — function names, class
names, exported constants — for anything whose name, signature shape, or
recorded purpose plausibly overlaps with what's about to be written.
Report candidates the same way: path, what it exports, its tier, and the
specific overlap, without concluding whether it's actually reusable here.

If the map doesn't record exports at this granularity for the area in
question (e.g., a module was tiered before `map-update` started tracking
exports, or a language's extraction doesn't yet resolve a particular
export style), say so explicitly rather than reporting "nothing found" as
if it were a confirmed negative — a query that couldn't be answered and a
query that came back genuinely empty are different findings, and
collapsing them into the same silence would make future readers trust a
negative that isn't really one.

## Genuinely empty is a real, useful answer

If nothing in the map plausibly overlaps, say so plainly. A clean "nothing
comparable found" is exactly the answer that lets the asking persona build
new with confidence — don't manufacture a weak candidate to seem more
thorough than the map actually supports.

## Output

A short report, returned directly to the asking persona in the same
conversation — this isn't a skill that produces its own saved artifact.
When another skill consulted you mid-task (`architecture-design`,
`tdd-implementation`), the report is that skill's input, not your final
message: write it, then carry straight on with the calling skill's work in
the same response. The report:

```markdown
## Map query: <what was asked about>

**Granularity:** structural | implementation
**Map status:** current as of <when map-update last ran> | possibly stale (<why>) | no map exists yet

**Candidates found:**
- <path> (tier: <tier> | untiered) — exports: <relevant exports>; shares: <the specific overlap>
- ...

(or) **Nothing comparable found in the map.** (end the answer there: no "adjacent" modules, no "close enough to extend?")
(or) **Could not be answered at this granularity** — <what's missing and why>.
```

No recommendation, no ranking by "best match," no verdict on reuse. The
asking persona reads this and decides.
