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
   - Read `case_dir/prompt.md` in full. Frontmatter is metadata. The body
     splits into two parts if it contains a `## Scripted answers` heading:
     everything above that heading is the `task` shown to the persona;
     everything below it is `scripted_answers` — **never shown to the
     persona in step 3**, only used by you in step 3b if it asks instead
     of finishing. If there's no such heading, the whole body is `task`
     and there are no scripted answers.
   - Read `agent_file` in full. Note its system-prompt body, its
     frontmatter `skills:` list (strip any `<plugin-name>:` prefix to get
     each bare skill slug), and its frontmatter `background:` field.
     **If `background: false` is present, this persona blocks on
     `AskUserQuestion` and must not be launched via an async Agent/Workflow
     call — run steps 3 and 3b inline in the main conversation instead
     (the "Inline path" below), never as a spawned subagent.** If
     `background:` is absent or `true`, use the normal spawned-agent path.
   - Each skill slug's file is `plugin_root/skills/<slug>/SKILL.md`.

3. **Run the persona against the prompt — a dry run, no side effects.**

   **Spawned-agent path** (default — `background:` absent or `true`).
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
   <task, verbatim>
   ```

   Grant this agent only `Read`, `Grep`, `Glob` — never `Write`/`Edit`/
   `Bash`, regardless of what the real persona's own `tools:` list says.
   That's what makes this a safe dry run.

   Capture its final response text as `phase1_output`.

   **Inline path** (`background: false`). Do not spawn a subagent for
   this persona — role-play it yourself, directly in the main
   conversation, under the same constraints the spawned-agent prompt
   above would impose: adopt the `AGENT.md` system-prompt body verbatim
   as your instructions for this task, read only the skill files that are
   genuinely relevant (via your own `Read` tool calls — this is what
   grading checks, so actually read them, don't just cite the paths), and
   open your response with the same

   ```
   Skills consulted: <path>, <path>
   ```

   (or `Skills consulted: none`) line the spawned-agent path requires —
   graders check this line the same way regardless of which path
   produced it. Do not write or edit any files while producing this
   response (saving the captured text happens in step 4, by you, after
   the fact — that's bookkeeping, not the persona acting). If the persona
   would ask a clarifying question before finishing, let that genuinely
   be your response for this phase — in character, not resolved on your
   own authority. Capture your own response text as `phase1_output`.

3b. **If `phase1_output` is a clarifying question rather than a finished
    artifact, continue the interaction — don't grade a stopped-short
    response as the final answer.** A real invocation would ask via
    `AskUserQuestion`, get an answer in the same turn, and keep going;
    this step is what makes the emulation match that instead of stopping
    dead the moment a question gets asked, which is a gap in the harness,
    not correct persona behavior.

    - If `scripted_answers` has nothing that answers the question asked,
      stop and report this as a case-authoring gap — don't guess an
      answer yourself, that would contaminate the result.
    - Otherwise:
      - **Spawned-agent path:** spawn a second fresh agent (same AGENT
        DEFINITION, skills, and tool grant as step 3) with a prompt built
        like this:

        ```
        [... same preamble as step 3 ...]

        --- TASK ---
        <task, verbatim>

        --- YOUR EARLIER RESPONSE ---
        <phase1_output, verbatim>

        --- ANSWER TO YOUR QUESTION ---
        <the matching entry from scripted_answers>

        You now have the answer you asked for. Produce the finished
        artifact — don't ask again, and don't repeat the question back.
        ```

      - **Inline path:** no second agent — continue in character, in this
        same turn, exactly as a real `AskUserQuestion` call would resume
        after getting its answer. Treat the matching entry from
        `scripted_answers` as the answer you just received, and produce
        the finished artifact as your next response, still under step 3's
        inline constraints (no file writes, same self-report line). Don't
        ask again, and don't repeat the question back. This path is
        *more* faithful to the real persona than the spawned-agent path —
        there's no second context to hand off to, so nothing about the
        continuity is emulated.

    - Capture this response (however produced) as `final_output`. This is
      what gets graded as "the output" from here on — `phase1_output`
      still gets saved (step 4) so graders that specifically check the
      *asking* behavior have something to grade, but any grader checking
      artifact correctness should grade `final_output`.

4. **Save the result(s).**
   - Create `case_dir/eval-result/` if it doesn't exist.
   - If step 3b ran: write `phase1_output` to
     `case_dir/eval-result/phase1-question.md`, and `final_output` to
     `case_dir/eval-result/output.md`.
   - If step 3b didn't run (phase1 was already a finished artifact):
     write `phase1_output` to `case_dir/eval-result/output.md` only.

5. **Grade each grader file** in `case_dir/graders/*.md`, per its type.
   First decide which captured output the grader judges: if its
   frontmatter has `target: phase1`, that's `eval-result/phase1-question.md`
   (only meaningful for cases where step 3b ran — use it for graders that
   specifically check the *asking* behavior); otherwise it's
   `eval-result/output.md`, the final artifact. Read each grader's
   frontmatter (`type` + type-specific fields) and body first — but only
   `llm` graders need a judge agent; the other two are fully deterministic,
   and spinning an agent for them wastes a call to get an answer you can
   compute directly:
   - **`type: regex`** — resolve it yourself: run the `pattern` against
     the target output (e.g. Python `re.search` with the pattern as-is —
     macOS's `grep` lacks `-P`/PCRE support, so plain `grep` will silently
     misbehave on `[\s\S]`-style patterns; don't reach for it here).
   - **`type: tool_used`** (adapted, since this doesn't run inside a real
     installed plugin) — resolve it yourself: check the "Skills
     consulted:" line the persona agent self-reported in step 3 against
     the expected skill, via `input_match`/the skill name.
   - **`type: llm`** — this one needs judgment. Spawn a fresh judge agent
     with the `criteria` text and the target output; it must open its
     response with exactly `PASS` or `FAIL` on the first line, then a
     one-line reason. Judge agents are always spawned as background
     Agent calls, even for `background: false` personas — the `background:`
     restriction is about not launching the *interactive persona itself*
     asynchronously (it blocks on `AskUserQuestion`); a judge is a
     one-shot classifier with no such tool, so it's unaffected.

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
- **On the spawned-agent path, the ask-then-continue step (3b) isn't true
  conversational continuity.** A real `AskUserQuestion` call blocks and
  resumes the *same* turn; step 3b instead spawns a fresh agent and hands
  it the question + answer as text context. Usually equivalent, but a
  persona that would behave differently with genuine tool-call continuity
  (e.g. reasoning that depended on its own intermediate tool calls, not
  just the final question text) won't be caught by this. The inline path
  doesn't have this gap — there's no second context to hand off to, so
  phase 2 genuinely continues the same turn, matching how the real
  persona would resume after `AskUserQuestion` returns.
- **Forgetting to re-check `background:` before reusing cached persona
  text is a real failure mode, not a hypothetical one.** If `agent_file`
  or its skills changed since you last read them in this conversation
  (e.g. someone just hardened a rule, or added `background: false`),
  re-read them before spawning or role-playing — don't reuse text from
  earlier in the conversation just because no system reminder flagged a
  change. Absence of a reminder isn't proof nothing changed if you never
  issued a fresh `Read` to trigger one.

Once `claude plugin eval` is enabled for real, re-verify these cases
against it rather than treating this runner as the final word.
