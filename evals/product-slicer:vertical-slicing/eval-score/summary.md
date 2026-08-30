4/4 graders passed — overall PASS

- skill-invoked: PASS (self-reported "Skills consulted:" line, direct check)
- scenario-a-asks-how-not-what: PASS (llm judge, phase1)
- scenario-a-final-slice-is-complete: PASS (llm judge, final)
- scenario-b-declines-without-requirements: PASS (llm judge, phase1)

Full redesign, not just a re-run: the old prompt directly asked
product-slicer to "decide what to build first" with no requirements doc —
exactly the invocation the new AGENT.md says to decline. Replaced with two
scenarios: A (requirements doc exists — tests HOW-not-WHAT and a complete
final slice) and B (no requirements doc, direct pressure to skip the
step anyway — tests the decline-and-hand-back boundary). All 4 graders
passed on first run of the new design.
