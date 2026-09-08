---
type: llm
criteria: |
  Scenario C hands product-slicer a scope change discovered by
  devsecops-engineer: slice 1 needs a login it wasn't scoped for. Grade the
  response on four things.

  (1) It must OWN the decision rather than deferring it back to the user as
  an open menu of options. Being handed the finding is being handed the
  call. Score 0 if it lists options and asks the user to pick without
  recommending and deciding.

  (2) It must NOT resolve this by growing slice 1 to include sign-in, unless
  it first works through and explicitly rejects the better-ranked options
  with concrete reasons. Growing is ranked last. Score 0 if growth is chosen
  casually, presented as the obvious answer, or offered as one neutral
  choice among equals.

  (3) The expected resolution is a NEW SLICE AHEAD of slice 1 delivering
  sign-in on its own (option 1 in the ranked order), or — if it makes a
  genuine, reasoned case — narrowing slice 1 so the constraint stops
  applying (option 2, e.g. running locally rather than exposed). Either is a
  pass on this element as long as the reasoning is real.

  (4) It must say what its choice INVALIDATES and needs repairing —
  specifically that a newly created slice needs its own
  product-manager:requirements-refinement pass, and/or that a changed step
  boundary supersedes the scope map rather than being edited in place. Score
  0 if the new slice is created with no mention that its WHAT is unconfirmed.

  Score 1 only if all four hold.
focus: last_message
---

The most important new grader in this case. It encodes the exact failure a
real dogfooding run produced: a downstream persona found a slice needed a
capability nobody scoped, presented three options — including "the slice
grows" — as co-equal, and the user picked from that menu. Two things went
wrong at once, and this grader tests both: the scope decision was made by
laying out the menu (element 1), and the slice created as a result never got
a requirements pass, which it then flagged about itself (element 4).

Element 3 deliberately accepts two answers. Narrowing is a legitimate
resolution, not a dodge, when the requirement comes from context the slice
doesn't need yet — the grader shouldn't force the new-slice answer when a
reasoned narrowing is on the table.
