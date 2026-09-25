# architecture-cartographer:map-query — eval summary

**Result: PASS — 6/6 graders passed**

| Grader | Result |
|---|---|
| skill-invoked | PASS |
| structural-query-surfaces-real-candidate-as-fact | PASS |
| implementation-query-matches-by-shape-not-literal-name | PASS |
| honest-empty-result | PASS |
| never-renders-reuse-or-duplicate-verdict | PASS |
| flags-map-staleness | PASS |

## Notes

First-ever run for this case, written from `AGENT.md`/`map-query/SKILL.md`
text before any real dogfood output existed, per this plugin's established
order. Clean 6/6 on the first pass — no skill-text fixes needed.

The fixture's deliberate trap (matching an `OrderRepository` query against
a differently-named `CaseDirectory` purely by shape — find-by-id,
list-by-status) worked exactly as intended: the emulated run surfaced the
candidate by its recorded exports rather than missing it on a literal-name
mismatch, and reported it as a fact ("shares: ...") rather than a verdict.
The staleness trap (a teammate mentioning an unincorporated branch) also
worked as intended — the run caveated all three answers rather than
silently trusting the given map as complete, and was explicit that
checking the live codebase is `map-update`'s job, not `map-query`'s own.
