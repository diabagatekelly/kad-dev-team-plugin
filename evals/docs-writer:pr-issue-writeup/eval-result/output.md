Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/pr-issue-writeup/SKILL.md

Filing destination confirmed: GitHub. Here's the issue content, ready to file as-is.

---

**Title:** Import and auto-categorize transactions from CSV (Slice 1)

**Body:**

## Summary
A user uploads a CSV export of transactions. Each transaction is auto-categorized by matching against previously-categorized sample data. The user then views the imported, categorized transactions in a list.

## Scope
- [ ] Upload a CSV export of transactions
- [ ] Auto-categorize each transaction by matching against previously-categorized sample data
- [ ] Display the imported, categorized transactions in a list

## Open questions
- How should a transaction be categorized when no sample data matches it (e.g. left uncategorized, flagged, or something else)?
- What CSV columns/format are supported, and what happens on a malformed or unrecognized row?

---

Note on the two open questions: I flagged them rather than answering them — resolving them means deciding matching/error-handling behavior, which is a design call, not a documentation call. Whoever picks this up should settle them before or during implementation.
