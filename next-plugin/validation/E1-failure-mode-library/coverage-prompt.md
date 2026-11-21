# The coverage judge: which defects is the library about?

You are a strict, independent judge. Your folder holds two files and you read nothing else: no other file on this machine, no web page.

- `library.json`: a library of the ways software commonly fails, by kind of action. Each entry has an `id`, an `action`, a `failure` (a condition, in general words) and a `question` (what a plan must decide because of it). It was written from public sources by people who had never seen the defects below.
- `bugs.json`: defects found in built products. Each has a `plan` (which product and slice it came from), an `id`, a `title`, a `trigger` (when it appears), a `build_behaviour` (what the built thing does) and a `harm` (what the person meets).

For every defect, look through the whole library for the entries this defect is a case of, then give the defect exactly one class.

## Classes

- **F, full.** The defect is plainly a case of one entry's `failure`: the entry's condition, read in this product's terms, is this defect's trigger, and a plan that had answered that entry's `question` for the action involved would have had to settle what happens here.
- **P, part.** An entry is about the right kind of action and a neighbouring condition, but a plan could answer its question fully and still leave this defect's case open; or the entry covers one part of a defect that has several.
- **X, none.** No entry's condition is this defect's trigger. This includes defects that come from a rule of the product itself being wrong, which no general library can hold.

## Rules

1. When two classes are both arguable, give the one less favourable to the library: P before F, X before P.
2. An entry counts only for what its `failure` and `question` say. That its action type would cover the defect "in principle" is not enough.
3. Judge each defect on its own, from the two files only.
4. Every defect in `bugs.json` gets exactly one entry in your output, in the same order, with its `plan` and `id` copied unchanged.

## Output

Write `out.json` in your folder: a JSON array, one object per defect:

```json
{"plan": "<plan>", "id": "<id>", "class": "F|P|X", "entries": ["<entry id>"], "reason": "<one sentence: which condition it is a case of, or for P what is left open>"}
```

`entries` holds at most two ids and is empty for X. Then reply with one line: the count of each class.
