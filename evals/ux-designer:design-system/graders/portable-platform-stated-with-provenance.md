---
type: llm
criteria: |
  PORTABLE — holds for any design system output, not just this case's
  fixture.

  The output must include a Platform section stating what the interface
  targets (native mobile, responsive web, desktop, etc.) and whether that
  was already established elsewhere (naming the artifact — e.g. a
  technology-bootstrap or a problem doc's hosting constraint) or decided
  fresh by this skill. Silence on platform, or a platform assumed without
  being stated, both fail — the skill must not leave this implicit.

  Score 0 if there's no Platform section, or if one exists but doesn't say
  whether the platform was already established or decided here; 1 if
  platform is stated with its provenance made explicit either way.
focus: last_message
---

Grounded in `skills/design-system/SKILL.md`'s "Establish the platform, if
nothing has yet" section and the Output format's "## Platform" line
("What this targets, and whether that was already established or decided
here"). Platform is exactly the kind of fact that's easy to leave implicit
because it usually resolves itself — this grader exists so an omission
never gets mistaken for a decision.
