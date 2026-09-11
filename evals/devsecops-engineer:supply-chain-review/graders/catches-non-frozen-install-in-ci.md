---
type: llm
criteria: |
  A `package-lock.json` is committed and current, but the CI workflow
  runs `npm install` (and the Dockerfile runs `npm install --production`)
  rather than `npm ci` — meaning a build can silently resolve and use
  different versions than what's in the committed lockfile instead of
  failing on drift. PASS requires this being flagged per the skill's own
  mental model: "Frozen-mode installs stop the build from silently moving
  off it," and "a lockfile nobody installs from in frozen mode is
  decoration." Score 0 if this is missing, or if the finding stops at
  "you have a lockfile" without noting the install command doesn't
  actually enforce it; 1 if the gap between having a lockfile and
  installing from it in frozen mode is identified.
focus: last_message
---

Tests whether the review checks that all four things the skill names
(pinning, frozen installs, verification, update automation) are present
together — a lockfile alone, without an install command that respects
it, is "decoration" per the skill's own phrase.
