# Brief: list what one slice does, by kind of action

You are given the planning documents of one slice of a product, in the folder your task names. Read every document there. Read nothing else on this machine and do not use the web. You see no code and no account of how the product later behaved.

List every distinct thing the slice does, as the plan describes it, each under exactly one of these kinds of action:

- `call-external`: asking a system the product does not control to do or return something (one item per distinct request)
- `receive-external-data`: taking in the values such a request returns (one item per distinct reply)
- `sync`: repeatedly bringing a local copy in line with a source that keeps changing
- `limits`: a quota, rate limit, size or capacity that applies, the product's own or someone else's
- `durable-write`: saving to storage that must survive a restart (one item per distinct thing saved)
- `startup-read`: loading what was saved when the product starts
- `migration`: stored data or settings written by an older or newer version
- `concurrency`: two operations, two copies of the product, or two devices acting on the same thing
- `lifecycle`: a lasting thing being created, left half-made, expiring, being removed or orphaned (one item per lasting thing)
- `user-input`: a value a person types or chooses
- `user-action`: a person starting an operation (one item per distinct operation a person can start)
- `long-operation`: an operation long enough to be waited on, interrupted or abandoned
- `time`: a clock, date, duration, schedule or expiry the slice relies on
- `text`: storing, comparing, searching, sorting or showing text
- `presentation`: showing numbers, amounts, units, dates or an ordering to a person
- `corpus`: a fixed body of content or reference data the product ships or depends on
- `secrets`: keeping or using a credential or key (one item per secret)
- `authorization`: who may do or see what, and requests that claim to come from the product's own pages
- `configuration`: a setting, environment value, path or port
- `logging`: what is recorded when something happens or fails
- `accessibility`: a screen operated by keyboard, screen reader, zoom, or with reduced motion or contrast needs (one item per screen or distinct interaction)

Rules:

1. List what this slice adds or changes. Something the plan defers to a later slice is not listed.
2. One item per distinct thing: two requests to the same system are two items; the same request made at two moments is one.
3. A kind of action the slice does not perform gets no item. Do not invent one to fill a kind.
4. Say each item in the product's own terms, in one sentence, with the document and line where the plan describes it.

Output: a JSON array at the path your task gives. Each item is an object with exactly: `id` (`a` and two digits, numbered from `a01` in the order you list them), `action` (one of the keys above), `what` (the one sentence), `where` (document name and line, for example `design-slice-001.md:42`). Then reply with one line: the number of items per kind of action.
