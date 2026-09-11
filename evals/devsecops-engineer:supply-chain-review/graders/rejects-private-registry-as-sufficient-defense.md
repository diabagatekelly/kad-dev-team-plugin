---
type: llm
criteria: |
  The team believes "our npm packages come from our company's private
  registry, so we don't need to worry about a public-registry
  compromise." PASS requires the review to explicitly correct this, per
  the skill's own named point: "A private registry is not by itself a
  defense. It changes who you trust, not whether the anchor holds. Check
  the lockfile still carries hashes and CI still runs frozen." Score 0 if
  the review accepts this claim or doesn't address it; 1 if it explicitly
  states a private registry doesn't by itself establish a pinned/frozen
  posture and the same checks still apply.
focus: last_message
---

Tests a second named-mistake correction from the skill's text, distinct
from the update-automation one — checks the review isn't only capable of
correcting one specific claimed belief.
