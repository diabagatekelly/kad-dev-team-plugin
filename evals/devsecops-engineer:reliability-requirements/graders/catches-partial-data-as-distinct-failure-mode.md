---
type: llm
criteria: |
  The provider is described as sometimes returning only some of the
  transactions on a call — the skill's own "a dependency lies" failure
  mode (succeeds with wrong, partial, or stale data), distinct from the
  provider being slow or being down entirely. PASS requires the output to
  name partial/incomplete retrieval as its own failure mode, separate from
  "provider unreachable" and "provider slow." Score 0 if partial data is
  merged into a generic "provider fails" bucket with no distinct
  treatment, or isn't named as a failure mode at all; 1 if it's identified
  as its own case.
focus: last_message
---

Checks the skill's own enumerated failure-mode list actually gets applied
against a fixture built to trigger the specific mode ("a dependency
lies") that's easiest to fold into a generic "it broke" bucket.
