# architecture-cartographer:map-update — eval summary

**Result: PASS — 6/6 graders passed**

| Grader | Result |
|---|---|
| skill-invoked | PASS |
| extracts-real-edges-and-exports | PASS |
| carries-forward-and-assigns-tiers-without-inventing | PASS |
| flags-duplication-without-adjudicating | PASS |
| flags-wrong-direction-without-adjudicating | PASS |
| no-ask-user-question | PASS |
| no-severity-anywhere | PASS |

## Notes

First-ever run for this case, written from `AGENT.md`/`map-update/SKILL.md`
text before any real dogfood output existed, per this plugin's established
order. Clean 6/6 on the first pass — no skill-text fixes needed.

The fixture's three deliberate traps all worked as intended. Tier
carry-forward vs. fresh assignment vs. honest `untiered`: `order-directory`/
`mongo-order-directory` kept their prior-map tiers unchanged, the four new
modules picked up exactly the design doc's stated ordering, and
`util/currency-format.ts` — named in neither source — was reported
explicitly `untiered` rather than guessed or silently dropped, with the
run naming *why* (inferring from the import graph would be circular). The
duplication trap (`RefundLedger`/`CreditLedger` — same import target,
same constructor shape, same two-method shape under different literal
names) was flagged as a candidate with the specific shared facts named,
and the run explicitly declined to render either a merge-them or
leave-them-separate verdict. The wrong-direction trap
(`AssignRefundUseCase`, tier 1, importing `MongoRefundStore`, tier 3) was
flagged by tier comparison alone, reported as a candidate rather than an
adjudicated violation, and never turned into a question — satisfying
`no-ask-user-question` and `no-severity-anywhere` at once, since the run
had every opportunity to hedge into a live question or a severity label
on either trap and did neither.

Combined with `map-query`'s own clean first-pass run (`eval-score/summary.md`
in that case's own directory), both of this persona's skills now have a
passing eval case, neither needing a skill-text fix — the strongest
first-pass result of any two-skill persona built in this roster so far,
plausibly because the mandate is mechanical rather than a judgment call:
there's less room for the kind of interpretive drift that produced real
fixes in `tdd-implementation`'s and `test-quality-review`'s six- and
three-run sequences.
