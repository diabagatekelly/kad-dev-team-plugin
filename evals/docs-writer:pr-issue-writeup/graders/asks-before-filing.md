---
type: llm
target: phase1
criteria: |
  No ticket system was specified in the task. The agent must ask whether
  this should be filed as a tracked issue at all, and if so, which system
  (e.g. GitHub, Jira, Linear) — before producing a finished, system-specific
  write-up. It must NOT silently assume a system (e.g. writing GitHub-flavored
  markdown with labels/assignees, or Jira-style fields) and proceed straight
  to a finished write-up. Score FAIL if it guesses a system without asking;
  PASS if it asks first.
focus: last_message
---

Regression test for the "ask before assuming a filing mechanism" rule added
to agents/docs-writer/AGENT.md and skills/pr-issue-writeup/SKILL.md.
