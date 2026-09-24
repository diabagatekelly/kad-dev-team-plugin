PASS

The three-fee-function finding names the real shared logic (weight-based
surcharge + zone branch, differing only in the per-zone constants) and
explicitly carves out the guard clause: "(All three also open with the
same one-line `if (!order) return 0` guard, but that's the exempt
guard-clause pattern, not part of this finding.)"

This grader failed twice before landing here — a genuinely recurring gap,
not a fluke. First fix (an abstract instruction not to fold the guard
clause into "what's identical") held on the original small fixture but
regressed on this case's larger, busier fixture: the finding again
described "the same shape — null guard, weight-based cost... then a
domestic/international flat add-on" as one shared description, refolding
the guard clause into the violation. Second fix added a concrete
before/after phrasing template to `skills/code-review/SKILL.md`'s
Duplication section (what not to write, what to write instead, and how to
mention the exempt part if at all) — re-verified clean on a fresh run,
independently re-judged.
