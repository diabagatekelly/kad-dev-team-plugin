# next-plugin: the work towards the plugin after kad

Everything for the next plugin lives in this folder, apart from kad,
which is frozen at 0.19.0 in the rest of this repository (the owner,
2026-11-20: "a new folder here for now, so there's clear separation").
**Moved on 2026-11-21:** the owner gave the plugin a public repository
of its own, `kd-dev-team` (`github.com/diabagatekelly/kd-dev-team`).
What the plugin uses was copied there with its tests; this folder
stays as the record of how the earlier steps were validated and is no
longer added to.

**Start here:** `../.synthesis/handoff-next-plugin.md` (the whole
context and the prompt for a session), then
`design/planning-phase.md` and the top section of `../TODO.md` (steps
V0 to V9).

## Rules of this folder

- Nothing here is part of kad. kad's `skills/`, `agents/`, `hooks/`,
  `evals/` and scripts are not edited from here, and nothing here is
  named by kad's eval suite or its gate.
- Nothing here is a plugin yet: no `.claude-plugin/plugin.json`, no
  `skills/` or `agents/` folder. For the build, `../TODO.md`'s rule
  stands: no plugin code before V7. For the planning phase the owner
  brought the design forward on 2026-11-21: a stage's text becomes
  part of the plugin only when its test has been read and the owner
  says it holds. Claude Code loads only the plugin at the
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
  scripts with their tests) and a `RESULT.md`. Once a step is closed
  and its result read, its folder is not added to, except to correct
  it; a step still open (V0, until Windows is tried) is added to. See
  `validation/README.md` for what each holds.
- The table method frozen on 2026-11-19 stays where the handoff's
  history names it, `../.synthesis/frozen-table-method.md`.
