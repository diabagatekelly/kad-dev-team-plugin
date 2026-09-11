---
type: llm
criteria: |
  `some-org/deploy-action@v2` in `.github/workflows/deploy.yml` is pinned
  to a version tag, not a full commit SHA — a tag the publisher (or anyone
  who compromises their account) can re-point to different code, which
  then runs with whatever access this deploy job has. PASS requires this
  being flagged, per the skill's explicit rule: "third-party actions and
  reusable workflows pinned to a full commit SHA, not a tag. A tag here is
  as mutable as any other tag, and the code runs with whatever access the
  job has." Severity should be High or Critical given this specific job
  deploys (real, meaningful access). Score 0 if this finding is absent,
  or rated Low/Medium with no justification; 1 if flagged at High or
  Critical with the mutable-tag reasoning present.
focus: last_message
---

Tests the CI-workflow-reference half of the skill's "mutable vs immutable
references" mental model against the highest-stakes job in the fixture
(the one that actually deploys).
