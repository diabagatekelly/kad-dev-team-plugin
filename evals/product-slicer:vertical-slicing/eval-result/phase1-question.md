Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/vertical-slicing/SKILL.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/acceptance-criteria/SKILL.md

Before I can scope slice one, I need one answer from you.

The other open questions in the problem doc don't change the slice's shape, so I'm resolving or deferring them myself:

- **CSV vs. bank-aggregation API** — CSV import first. Bank-aggregation is the biggest unknown here (real credentials, third-party vendor, infrastructure nobody's built) — deferring it entirely from slice one.
- **AI/ML vs. rule-based categorization** — rule-based matching against the provided sample data. It satisfies "must stay free" outright and directly uses the constraint that categorization should reflect your existing categories. AI/ML becomes a later enhancement.
- **"Move money" trigger rule** — deferring the whole capability, not just the trigger detail. It depends on categorized spend and a budget comparison that don't exist yet.
- **Scope of "must stay free" (AI-only vs. whole hosting/infra stack)** — doesn't change what slice one does or who it's for; flagging it as a note for `software-architect` rather than resolving it myself.

One question I can't default on:

**Is this single-user only, or does "very secure" anticipate multi-device or shared access?**

This changes the actor and scope of slice one directly — single-user means no identity/access concept is needed at all; shared access means slice one needs at least a seam for "whose data is this" from day one. I don't want to guess this one.
