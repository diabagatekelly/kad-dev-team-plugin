# Validation steps and experiments

One folder per step of `../../TODO.md`'s list (`V<n>-<name>/`) and per
experiment that fed it (`E<n>-<name>/`). Each holds its question, the
bar set before it ran, what was run (prompts frozen with their hash,
scripts with their tests) and a `RESULT.md`. What quotes a project is
in the private audit repository, in a folder of the same name.

| Folder | In one line |
|---|---|
| `V0-where-a-session-runs` | A VM per session, set up by script; holds on the Mac, Windows open |
| `V1-benchmark-and-judge` | 65 known defects and the judge that scores a method against them |
| `E1-failure-mode-library` | 250 ways software commonly fails, by kind of action, from public sources |
| `E2-library-grid` | The library crossed with everything a slice does: too large, no better |
| `E3-library-triage` | Triage, a cited dossier, then answers: the shape the plan takes |
| `E4-rescore-and-second-plan` | The judge's second version; two plans; settings come from the build |
| `E5-cold-read-overlap` | How much independent cold readers overlap: three are worth running |

Start from `../../.synthesis/handoff-next-plugin.md`.
