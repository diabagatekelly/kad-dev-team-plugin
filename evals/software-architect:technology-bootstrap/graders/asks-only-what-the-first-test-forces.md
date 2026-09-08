---
type: llm
criteria: |
  This is a NEGATIVE grader — what the output declines to decide matters more
  than what it decides.

  The output must NOT ask the user to choose, or itself choose, any of:
  a CI/CD pipeline or build automation; a hosting, deployment or cloud
  target; a container runtime; a database or persistence technology; an
  observability/monitoring stack; an auth provider. None of these is forced
  by writing slice 1's first failing test.

  Score 0 if the output solicits a decision on, or settles, ANY of the above
  as part of the bootstrap set. Merely listing one as deliberately-not-decided
  (with an owner) is correct and does not count as deciding it.

  Score 1 if the categories it treats as forced stay within: language and
  runtime, test runner, package manager (with its lockfile/pinning posture),
  and — if the first test drives a UI or crosses HTTP — a UI or HTTP
  framework. A brief mention that some other category will be needed
  eventually is fine; asking the user to settle it now is not.
focus: last_message
---

The single most important grader for this skill, and the reason it exists.
An empty repo makes deciding the whole stack feel like the responsible move,
and CI/CD is the specific trap: it is not project-specific, which makes it
feel like safe common ground, but slice 1 ships without a pipeline. The
demand test — "can this slice's first failing test be written without
deciding this?" — is the only filter, and this grader checks it was actually
applied rather than quoted.
