---
type: llm
criteria: |
  PORTABLE — holds for any screen design output, not just this case's
  fixture.

  The interaction flow must not include search, filtering, sorting,
  editing, deletion, or any other interaction the acceptance criteria
  don't mention, even if it would be a reasonable or expected feature for
  a screen like this in general. Wanting to add a "nice touch" beyond what
  the criteria call for is the same YAGNI mistake this skill's text names
  for structure, applied to behavior.

  Score 0 if the interaction flow includes any control or affordance not
  traceable to an explicit acceptance criterion; 1 if every interaction
  shown is one the criteria actually call for, with nothing extra added.
focus: last_message
---

Grounded in `skills/screen-design/SKILL.md`'s "Resolve from what's already
decided before asking": "If [the acceptance criteria] don't mention
search, filtering, or a refresh affordance, don't add one because it
seemed like a nice touch — that's the same YAGNI mistake as adding a
component nobody asked for, just aimed at behavior instead of structure."
