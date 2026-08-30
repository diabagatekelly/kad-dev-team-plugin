9/9 graders passed — overall PASS

- skill-invoked: PASS (self-reported "Skills consulted:" line, direct check)
- directory-a-no-problem-doc: PASS (llm judge)
- directory-b-scope-map-decided-not-asked: PASS (llm judge)
- directory-c-routes-to-requirements-refinement: PASS (llm judge)
- directory-d-routes-to-product-slicer: PASS (llm judge)
- directory-e-routes-to-user-story-writeup: PASS (llm judge)
- directory-f-terminal-stop-no-cascade: PASS (llm judge)
- directory-g-asks-where-to-save: PASS (llm judge)
- single-step-not-chained: PASS (llm judge)

Full rewrite after a real dogfooding session surfaced two structural
issues: (1) scope-map-or-not was being asked of the user instead of
decided by docs-writer from the problem doc's own content, and (2) after
cutting a slice, the routing table would check for the next unsliced
scope-map step instead of routing to filing first — and even after
filing, nothing stopped it from cascading to the next step, which
skips the design/implementation work each unit needs before the next
one's shape should be decided. Both fixed; product-manager also newly
wired in between scope-map and slicing. All 9 graders passed on this
rewrite's first run.
