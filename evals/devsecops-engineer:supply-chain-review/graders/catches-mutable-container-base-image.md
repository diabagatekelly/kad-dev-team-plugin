---
type: llm
criteria: |
  `FROM node:20` in the Dockerfile is pinned to a tag, not a digest — the
  publisher can re-point `node:20` to a different image at any time.
  PASS requires this being flagged per the skill's explicit rule:
  "Container base images — pinned by digest, not tag." Score 0 if this
  finding is absent; 1 if the tag-vs-digest gap is identified for the
  base image.
focus: last_message
---

Tests the container-image half of the "mutable vs immutable references"
model — the third of the three places the skill names explicitly.
