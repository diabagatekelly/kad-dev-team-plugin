# Brief: fill part of a completeness grid for one slice

You are given, in the folder your task names: `plan/` (the planning documents of one slice of a product) and `cells.json` (part of a grid). You see no code and no account of how the product later behaved. Read nothing else on this machine. You may use the web only to read the public documentation of the systems the plan depends on.

Each cell of `cells.json` pairs one thing the slice does (`what`, with where the plan describes it) with one common way that kind of action fails (`failure`) and the question a plan must answer because of it (`question`). For every cell, read the plan and decide what it says about that failure for that thing, then fill in two fields:

- `tag`, exactly one of:
  - `DECIDED`: the plan settles what happens. Quote the words that settle it and give the document and line.
  - `PLAN SILENT`: the plan does not say.
  - `CONTRADICTS DOCS`: the plan decides it, but the public documentation of something the product depends on says otherwise. Cite both.
  - `IMPOSSIBLE`: it cannot happen for this thing. Say why in a few words.
- `says`: for `DECIDED`, the quoted words and where they are. For `PLAN SILENT` and `CONTRADICTS DOCS`, one or two sentences in this product's own terms: when exactly this would happen here, and what would then go wrong or what the person would meet. For `IMPOSSIBLE`, the reason.

Rules:

1. A general statement in the plan settles a cell only if it plainly covers this thing in this case; when unsure, the cell is `PLAN SILENT`.
2. Never guess a fact about a system the product depends on: cite its documentation with a URL, or say the documentation does not say.
3. Fill every cell. Change nothing but `tag` and `says`: keep each cell's `cell`, `item`, `entry` and its other fields as given.
4. Do not look ahead to how a build might behave; say what the plan says.

Output: the same array with `tag` and `says` filled, as valid JSON at the path your task gives. Then reply with one line: the count of each tag.
