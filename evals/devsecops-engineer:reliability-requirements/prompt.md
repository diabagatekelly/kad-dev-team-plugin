---
name: devsecops-engineer:reliability-requirements
tags: [devsecops-engineer, reliability-requirements]
runs: 3
---

A slice has been cut and designed. Its acceptance criteria carry an unfilled
reliability placeholder:

# Slice 1 (scope-map-001 step 1): Connect one account and see its transactions

## Thin path
The user connects one financial account, selects it, and sees that account's
transactions listed, pulled live from a third-party bank-data provider.

## Acceptance criteria (functional, already settled)
- Given the user connects an account and the connection succeeds, that
  account shows as connected.
- Given a connected account, when the user opens the transaction list, they
  see its transactions.
- Given the connection attempt fails, no account shows as connected and the
  user is told.
- [RELIABILITY — placeholder, to be authored by devsecops-engineer]

The engineer about to build this adds: "The provider's API can be flaky —
sometimes it only returns some of the transactions on the first call. If
that happens, I'll just show whatever came back so the user isn't stuck
looking at nothing, and we can quietly re-fetch the rest in the
background."

Fill in the reliability placeholder for this slice.

## Scripted answers

- What happens if this is unavailable for an hour: "Nothing bad — I just
  try again later. It's my own data, there's no deadline."
- Is there a target worth stating: "Not really a hard number. I'm willing
  to wait a couple minutes for it to load, but if it's going to fail I'd
  rather know than sit there wondering."
- Who notices when it breaks, and how: "Just me, whenever I happen to open
  it next. I'd like it to actually tell me what went wrong instead of just
  looking broken or empty."
- What already exists to build on: "Nothing — greenfield, no existing
  error-handling pattern anywhere yet."
- If asked to approve failing loudly on partial retrieval instead of the
  engineer's show-what-came-back-and-quietly-refetch proposal: "Yes, fail
  loudly — I'd rather know something's wrong than trust a list that might
  be missing entries without me knowing it."
