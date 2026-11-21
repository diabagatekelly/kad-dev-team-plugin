# Brief: one part of a failure-mode library, from public sources

You are compiling part of a library of the ways software commonly fails, organised by the kind of action the software performs, for planners who must decide in advance what their product does in each case. The library must serve any product in any field (a money tracker, a scripture-memorisation app, a booking tool), so every entry is written in words that fit any of them.

Work only from public sources on the web. Do not read any file on this machine other than this brief, and write only the one output file named in your task.

## The action types you cover

Your task names them by key. All the keys, so you know what belongs to other parts and can leave it there:

- `call-external`: asking a system the product does not control to do or return something
- `receive-external-data`: taking in values that arrive from such a system
- `sync`: repeatedly bringing a local copy in line with a source that keeps changing
- `limits`: quotas, rate limits, sizes and capacity, the product's own or someone else's
- `durable-write`: saving to storage that must survive a restart
- `startup-read`: loading what was saved when the product starts
- `migration`: stored data or settings written by an older or newer version
- `concurrency`: two operations, two copies of the product, or two devices acting on the same thing
- `lifecycle`: a lasting thing being created, left half-made, expiring, being removed or orphaned
- `user-input`: values a person types or chooses
- `user-action`: a person starting an operation (repeating it, leaving, reloading, several windows)
- `long-operation`: an operation that takes long enough to be waited on, interrupted or abandoned
- `time`: clocks, dates, durations, schedules, expiry
- `text`: storing, comparing, searching, sorting and showing text in any language or script
- `presentation`: showing numbers, amounts, units, dates and ordering to a person
- `corpus`: a fixed body of content or reference data the product ships or depends on
- `secrets`: keeping and using credentials and keys
- `authorization`: who may do or see what, and requests that claim to come from the product's own pages
- `configuration`: settings, environment values, paths, ports
- `logging`: what is recorded when something happens or fails, and what must never be
- `accessibility`: operating a screen by keyboard, screen reader, zoom, or with reduced motion or contrast needs

## What an entry is

One way that kind of action goes wrong, that is common enough to appear in a recognised source. For each of your action types give the 8 to 12 entries a planner most needs, not everything you can find. Leave out anything that is only an implementation technique, anything specific to one vendor's product, and anything that duplicates another entry in other words.

Each entry is a JSON object with exactly these fields:

- `id`: `<action key>-<two digits>`, numbered from 01 within the action type.
- `action`: the action key.
- `failure`: one sentence stating the condition, concretely enough that a reader could tell whether a given defect is a case of it. For example: "The other system carried out the request, but its reply never arrived."
- `question`: one sentence a plan must answer because of it. For example: "What does the product do, and what exists on the other side, when a request may or may not have taken effect?"
- `source`: an object with `title`, `url`, and `evidence` (at most 20 words, quoted or closely paraphrased from that page, showing it describes this failure).

## Rules

1. Every entry rests on a page you fetched and read in this session. If you cannot open a source, do not cite it. Prefer primary and widely recognised sources: standards bodies, a platform's or database's own documentation, engineering publications of large operators, well-known books' official pages or their authors' own write-ups, long-standing community references.
2. `failure` and `question` name no vendor, product, protocol, file format, programming language or industry, and use no term from one field of business (no banking, medical, retail words). Source titles may name what they name.
3. Write for a person who plans a product, not for one who codes it: say what happens, not which function to call.
4. No two entries in your part state the same condition.
5. Output: a JSON array of entries, valid UTF-8 JSON, at the path your task gives. Then reply with one line per action type: its key, the number of entries, and the sources used.
