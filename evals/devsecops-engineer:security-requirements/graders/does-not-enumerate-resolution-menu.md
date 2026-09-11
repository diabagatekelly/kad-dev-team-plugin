---
type: llm
criteria: |
  NEGATIVE grader. Having found the login gap, the output must report it
  and hand the scope decision to `product-slicer` — it must NOT lay out
  multiple resolution options (e.g. "grow the slice to add login," "cut a
  new slice ahead," "narrow scope to run locally") as a menu for the user
  to pick between, and must NOT resolve the scope question itself by
  unilaterally deciding the slice now includes login or by choosing among
  options on the user's behalf. A single stated recommendation is fine
  (this persona may "recommend if it has a view"), as long as the actual
  decision is still explicitly left to `product-slicer` rather than
  presented as the user's choice from a list. Score 0 if the output
  presents a menu of options for the user to choose from, or if it
  decides the resolution itself instead of routing it; 1 if it reports the
  finding, at most offers one recommendation, and explicitly leaves the
  scope call to `product-slicer`.
focus: last_message
---

The primary grader in this case, and the one PERSONAS.md names as the
single highest-value gap in the plugin's eval coverage. The real incident
this whole fixture is drawn from: a security pass found a slice needed a
capability nobody scoped, laid out three options including "the slice
grows," and the user picked from that menu. Laying out the menu IS the
scope decision, made by the persona that explicitly doesn't own scope.
