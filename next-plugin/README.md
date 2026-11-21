# next-plugin: the work towards the plugin after kad

Everything for the next plugin lives in this folder, apart from kad,
which is frozen at 0.19.0 in the rest of this repository (the owner,
2026-11-20: "a new folder here for now, so there's clear separation").
Whether it later moves to a repository of its own is the owner's call
at V9.

**Start here:** `../.synthesis/handoff-next-plugin.md` (the whole
context and the prompt for a session), then
`design/planning-phase.md` and the top section of `../TODO.md` (steps
V0 to V9).

## Rules of this folder

- Nothing here is part of kad. kad's `skills/`, `agents/`, `hooks/`,
  `evals/` and scripts are not edited from here, and nothing here is
  named by kad's eval suite or its gate.
- Nothing here is a plugin yet: no `.claude-plugin/plugin.json`, no
  `skills/` or `agents/` folder, until the owner has decided the
  design's open points and a step has passed its test (the owner,
  2026-11-21, brought the planning phase's design forward of V8). Claude Code loads only the plugin at the
  repository's root, so this folder is inert when kad is installed.
- This repository is public. What goes here: methods, prompts, scripts
  and their tests, and results as summaries (counts, scores, costs).
  Anything that quotes a project (its code, plan text, tables, cold
  reads, probes, data) goes to the private audit repository, under
  `take-4-comparison/` or a folder beside it, and is linked from here by
  path.

## Layout

- `design/planning-phase.md`: the design of the planning phase, for the
  owner's review; nothing in it is built.
- `validation/V<n>-<name>/` and `validation/E<n>-<name>/`: one folder
  per step of the list and per experiment, each with its question, the
  bar set before it ran, what was run (prompts frozen with their hash,
  scripts with their tests) and a `RESULT.md`. A folder is not added to
  after its result is read, except to correct it. See
  `validation/README.md` for what each holds.
- The table method frozen on 2026-11-19 stays where the handoff's
  history names it, `../.synthesis/frozen-table-method.md`.
