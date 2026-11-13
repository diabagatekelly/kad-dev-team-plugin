# How others evaluate skills, prompts and agents (survey, 2026-11-12)

Asked by the owner while phase A's gate ran (TODO.md, "The eval suite
itself", E3). Researched by a subagent from GitHub tree listings, READMEs
and the pages linked below, read 2026-11-12; none of these suites was run.
"Unverified" marks what could not be confirmed at a primary source. Nothing
here has been checked a second time: treat each claim as a lead to open,
not a finding.

## Part 1: comparable tools

| Tool | Evals of agent behaviour? | What kind |
|---|---|---|
| Gas Town (https://github.com/gastownhall/gastown) | Yes, narrow | `gt-model-eval/`: a promptfoo suite of about 80 single-decision cases for patrol roles, built to compare models, with `--repeat 3`. No CI workflow references it, so it looks manually run. Go integration and e2e tests cover the tooling, not the agents. |
| Superset (https://superset.sh/agent-orchestration) | None found | Only app unit and e2e tests. |
| `agent-orchestrator` skill (https://skills.sh/mrclrchtr/skills/agent-orchestrator) | None found | No path with that name in `mrclrchtr/skills` today (unverified whether it moved). |
| obra/superpowers (https://github.com/obra/superpowers) | Yes, closest to ours | `tests/claude-code/`: bash tests that run `claude -p` and assert contains, not-contains, count and order. One 10 to 30 minute integration test runs a two-task plan end to end. One test is an explicit RED (rule removed) / GREEN / PRESSURE triple. `writing-skills` asks for a no-skill baseline, pressure scenarios and "5+ reps per variant. Single samples lie". |
| BMAD-METHOD (https://github.com/bmad-code-org/BMAD-METHOD) | Yes | `skills/toolsmith/bmad-eval`: baseline against the bare model; a variant mode ("Does a section earn its place, or does a stripped version do as well?"); rubric quality; trigger accuracy. CI runs only structural validators. |
| GitHub spec-kit (https://github.com/github/spec-kit) | None found | Contract and unit tests of the CLI only. |
| claude-flow / ruflo (https://github.com/ruvnet/ruflo) | None found | Smoke and integration workflows; performance micro-benchmarks. |
| SuperClaude (https://github.com/SuperClaude-Org/SuperClaude_Framework) | None found | Unit tests of helpers; a script comparing token use between variants. |
| Aider (https://github.com/Aider-AI/aider) | Yes, benchmark | Exercism polyglot benchmark graded by unit tests on the end state. Measures model plus edit format, not rules. Old (last push 2026-05-22). |
| OpenHands (https://github.com/OpenHands/OpenHands) | Yes | Task benchmarks in `OpenHands/benchmarks`; the main repo has mock-LLM e2e tests (a scripted model server) and an affected-tests selector. |
| SWE-agent (https://github.com/SWE-agent/SWE-agent) | Yes | SWE-bench configs; pytest with predetermined test models and trajectory replay. |

## Part 2: practice outside these tools

**Anthropic.**
- "Demystifying evals for AI agents" (2026-01-09, https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents): grade what the agent produced rather than the path; capability evals (start at a low pass rate) apart from regression evals (near 100%); saturation named as a problem; pass@k and pass^k (75% per trial is about 42% over 3); a reference solution per task; an "Unknown" option for judges; judges calibrated against humans; transcript reading. Silent on multi-agent evaluation and on mocking.
- The multi-agent research post (2025-06-13, old; https://www.anthropic.com/engineering/multi-agent-research-system): end-state evaluation plus discrete checkpoints for long workflows.
- "Adding Error Bars to Evals" (2024, old; https://arxiv.org/abs/2411.00640): paired differences, clustered standard errors.
- `claude plugin eval` docs (https://code.claude.com/docs/en/plugin-evals): 3 runs per case by default; `llm` graders pass on 2 of 3 votes and see the first 12 and last 12 trace messages; regex for long output, judges for short; `context.history_file` resumes a saved transcript; mocks for MCP tools only; cost controls `--tag`, `--case`, `--ablation none`, `--max-cost-usd`. Nothing on how sub-agents run inside an eval.

**OpenAI** (https://developers.openai.com/api/docs/guides/agent-evals/, https://developers.openai.com/api/docs/guides/trace-grading): the unit is the trace. Stopped reporting SWE-bench Verified on 2026-02-23 after finding flawed tests and contamination (https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/).

**Inspect (UK AISI)** (https://inspect.aisi.org.uk): end state in a sandbox and transcript both gradeable; epochs with reducers; several model graders reduced by majority; limits, caching, early stopping; transcript scanners for misconfigured environments.

**promptfoo**: deterministic assertions plus trajectory assertions over traces (https://www.promptfoo.dev/docs/guides/evaluate-openai-agents-python/). **Braintrust**: per-case trial counts; production traces scored online and low scorers promoted into datasets (https://www.braintrust.dev/docs/observe/score-online). **LangSmith / agentevals**: trajectory match against a reference, or a trajectory judge (https://docs.langchain.com/langsmith/trajectory-evals). **DeepEval**: judge-based trace and span metrics.

**Task benchmarks.** Terminal-Bench 2.0: every task has an oracle solution that must pass, plus human review (https://arxiv.org/abs/2601.11868). tau-bench: simulated user, database end state, pass^k (https://arxiv.org/abs/2406.12045). METR: tasks sized by human completion time (https://metr.org/blog/2026-01-29-time-horizon-1-1/).

**Judge calibration.** Label a human set and measure the judge's true-positive and true-negative rates separately (https://arxiv.org/abs/2511.21140); LLM validators often show a high true-positive rate with a true-negative rate under 25% (https://arxiv.org/abs/2510.11822).

## Part 3: against our five weaknesses

**(a) Cases at 1.00 with unknown sensitivity.** Prior art for rule mutation is thin: BMAD's variant mode, Superpowers' RED/GREEN test, a practitioner post defining deletion, negation, dilution and displacement mutants (https://tianpan.co/blog/2026-05-05-prompt-mutation-testing-system-prompt-compliance). Keep E1 and E2. Add what the benchmarks do, inverted: every case gets a known-bad reference (a skill with the rule deleted, or a recorded bad transcript) that must fail. Tag cases as regression (expected 1.00) or capability (starts low).

**(b) The eval runs launches synchronously.** Nobody surveyed tests asynchronous sub-agent results directly. Nearest: MAS-FIRE's fault injection (https://arxiv.org/abs/2602.19843), OpenHands' scripted mock model, SWE-agent's trajectory replay. Inside our harness: `context.history_file` with a real session's transcript captured where the background agent is launched and has not returned; the case prompt is the next turn; fault variants (hand-back missing, empty, late, contradicting). Whether the Agent tool can be stubbed is unverified. (This session judged a hand-forged history too fragile; a captured one is the route.)

**(c) One-step cases.** Keep step cases for the gate; add two or three whole-loop runs on the fixture graded on end state and checkpoint files, per release; treat audited real runs as the long-horizon eval and promote each miss to a replay case.

**(d) Judge noise.** Label 30 to 50 judged excerpts by hand, half known fails, and report both rates per rubric; point judges at a file or the final message; add "Unknown"; pin the judge model.

**(e) Cost and size.** A judge-free tagged smoke tier for every diff, the full suite per release; compare versions by paired per-case differences; retire cases that have never failed and that no mutant kills.

## The five changes it would make first

1. Replay cases built from real background-run transcripts, with hand-back fault variants: the only item that covers the failure that already escaped.
2. A known-bad reference per case, beside the deletion mutants (E2) and the fail history (E1); then the regression or capability tag.
3. Suite tiers and the retirement of never-killed cases.
4. A judge calibration set, a pinned judge model, long-trace judgements moved to regex or files.
5. Two or three end-to-end fixture runs graded on end state, per release.
