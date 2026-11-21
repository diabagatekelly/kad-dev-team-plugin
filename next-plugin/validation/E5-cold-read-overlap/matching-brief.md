# Brief: which findings of several readers are the same defect

Your folder holds several reports, `reader-A.md`, `reader-B.md` and so on. Each is one reader's independent assessment of the same build of the same product; no reader saw another's. Read only those files: nothing else on this machine, no web.

From each report take every defect it lists under "Suspected bugs" (confirmed or marked to verify). Where one numbered item bundles defects with different triggers, split it into its parts. Leave out what a report says only about tests, readability or developer experience unless it is listed as a bug.

Then decide which findings, across readers, are the same defect: the same trigger and the same faulty behaviour of the product. Two findings that share a cause in the code but need different triggers, or that share a trigger but describe different faulty behaviour, are different defects. When you are unsure, they are different.

Output: a JSON array at the path your task gives, one object per distinct defect:

- `id`: `d` and two digits, numbered from `d01`.
- `title`: one line, in your own words.
- `trigger`: when it happens, one sentence.
- `found_by`: the readers that list it, as letters, for example `["A", "C"]`.
- `where`: for each reader in `found_by`, the item number in its report, for example `{"A": "3", "C": "5b"}`.

Every defect of every report appears in exactly one object. Then reply with one line: the number of distinct defects, and how many were found by one, two, three and four readers.
