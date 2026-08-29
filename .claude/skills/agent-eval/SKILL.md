---
name: agent-eval
description: Run one eval case (an evals/<agent>:<skill>/ directory containing prompt.md + graders/*.md) by emulating the target persona, capturing its output, and grading it with one judge agent per grader. Use when asked to run, test, or validate an eval case for a persona/skill in this plugin — a stand-in for `claude plugin eval`, which is early-access-gated in this environment.
---

# Agent Eval Runner

Runs a single eval case end to end without the real `claude plugin eval`
CLI. Emulates the target persona rather than genuinely invoking it as an
installed plugin agent — see "Known limitations" below before trusting a
result too far.

## Usage

Invoke with the eval case directory as the argument, e.g.:
`/agent-eval /path/to/kad-developer-suite/evals/docs-writer:problem-framing-doc`

## Procedure

1. **Resolve paths.**
   - `case_dir` = the given argument. Verify `case_dir/prompt.md` exists —
     if not, stop and report the path is wrong.
   - `plugin_root` = the parent of the `evals/` directory containing
     `case_dir`.
   - `case_name` = `case_dir`'s basename (e.g. `docs-writer:problem-framing-doc`).
   - `agent_slug` = everything before the first `:` in `case_name` (the
     whole name if there's no `:`).
   - `agent_file` = `plugin_root/agents/<agent_slug>/AGENT.md`. Stop and
     report if it doesn't exist.

2. **Read the case and the persona.**
   - Read `case_dir/prompt.md` in full (frontmatter + body).
   - Read `agent_file` in full. Note its system-prompt body and its
     frontmatter `skills:` list (strip any `<plugin-name>:` prefix to get
     each bare skill slug).
   - Each skill slug's file is `plugin_root/skills/<slug>/SKILL.md`.

3. **Run the persona against the prompt — a dry run, no side effects.**
   Spawn a fresh agent (general-purpose, no inherited context) with a
   prompt built like this:

   ```
   You are role-playing this Claude Code agent persona for an internal eval:

   --- AGENT DEFINITION ---
   <the AGENT.md system-prompt body, verbatim>
   --- END AGENT DEFINITION ---

   Your backing skills aren't pre-loaded. They live at the paths below —
   read whichever one(s) are genuinely relevant to the task before
   responding, the same way you'd invoke a Skill tool. Don't read ones
   that aren't relevant.

   Available skills:
   - <slug>: <path>
   (one line per skill)

   This is a dry run for evaluation. Do not write or edit any files, even
   if the persona definition above says to — produce your final artifact
   directly as your response text instead.

   HARD REQUIREMENT, checked automatically — not optional, not a
   suggestion: the very first line of your response, before anything
   else (including any preamble, headers, or the artifact itself), MUST
   be exactly:

   Skills consulted: <path>, <path>

   or, if none were relevant:

   Skills consulted: none

   Do not skip this line. Do not move it. Do not paraphrase it. If you
   forget it, the eval treats your response as if you consulted nothing.

   --- TASK ---
   <prompt.md body, verbatim>
   ```

   Grant this agent only `Read`, `Grep`, `Glob` — never `Write`/`Edit`/
   `Bash`, regardless of what the real persona's own `tools:` list says.
   That's what makes this a safe dry run.

   Capture its final response text as `output`.

4. **Save the result.**
   - Create `case_dir/eval-result/` if it doesn't exist.
   - Write `output` to `case_dir/eval-result/output.md`.

5. **Grade each grader file** in `case_dir/graders/*.md`, per its type.
   Read each grader's frontmatter (`type` + type-specific fields) and body
   first — but only `llm` graders need a judge agent; the other two are
   fully deterministic, and spinning an agent for them wastes a call to
   get an answer you can compute directly:
   - **`type: regex`** — resolve it yourself: run the `pattern` against
     `output` (e.g. Python `re.search` with the pattern as-is — macOS's
     `grep` lacks `-P`/PCRE support, so plain `grep` will silently
     misbehave on `[\s\S]`-style patterns; don't reach for it here).
   - **`type: tool_used`** (adapted, since this doesn't run inside a real
     installed plugin) — resolve it yourself: check the "Skills
     consulted:" line the persona agent self-reported in step 3 against
     the expected skill, via `input_match`/the skill name.
   - **`type: llm`** — this one needs judgment. Spawn a fresh judge agent
     with the `criteria` text and `output`; it must open its response with
     exactly `PASS` or `FAIL` on the first line, then a one-line reason.

   Write each verdict to `case_dir/eval-score/<grader-filename>.md` (same
   filename as its grader): `PASS`/`FAIL` on the first line, then how it
   was resolved (direct check, or the judge agent's reasoning).

6. **Summarize.**
   Write `case_dir/eval-score/summary.md`: pass count / total graders, and
   the overall result (PASS only if every grader passed). Report this
   summary back directly — don't make the user go read the file.

## Known limitations

This is a stand-in, not a replacement, for `claude plugin eval`:

- **Not a real plugin invocation.** The persona is emulated (system prompt
  + told where its skills live), not genuinely running as an installed
  plugin agent — packaging bugs (bad frontmatter, broken `skills:`
  references) won't be caught the way the real CLI would catch them.
- **`tool_used` is self-reported, not independently verified.** Nothing
  cross-checks the persona agent's claim against an actual tool-call log.
- **One run, not N averaged.** The real CLI runs each case `runs` times
  (default 3) and scores across them; this runs once per invocation.

Once `claude plugin eval` is enabled for real, re-verify these cases
against it rather than treating this runner as the final word.
