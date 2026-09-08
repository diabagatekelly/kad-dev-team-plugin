---
type: llm
criteria: |
  The output must treat the package manager's lockfile/pinning posture as
  part of the bootstrap decision rather than an afterthought, and must apply
  the defaults-over-flags criterion: prefer the option where hashed lockfiles
  and verified installs are the DEFAULT rather than an opt-in flag, because a
  flag-based posture depends on everyone remembering the flag.

  Score 1 if the output selects or recommends a package manager with that
  reasoning visible. Score 0 if the package manager is chosen purely on
  ergonomics/speed with no pinning consideration, or if pinning is mentioned
  only as something to configure later.

  Consulting `devsecops-engineer` / `supply-chain-review` for the standard of
  what "pinned" means is correct and expected; it is NOT required for a pass,
  and running a full supply-chain audit here would be wrong (there is no
  lockfile, no dependency and no build to audit yet).
focus: last_message
---

Covers the criterion added because `supply-chain-review` scopes itself to
auditing an existing repository and so has no notion of choosing. Managers in
the same ecosystem differ in whether strict pinning is default or opt-in — a
distinction invisible in review, since both end states audit identically, and
decisive at bootstrap.

The scripted answer ("I want whatever means I don't have to remember a flag")
hands this to the persona directly, so failing it means the criterion isn't
being applied even when the user states it in the skill's own terms.
