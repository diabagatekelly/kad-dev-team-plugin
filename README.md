# kad-dev-team

A personal Claude Code plugin. It bundles a roster of narrow-focus developer
personas (agents), each backed by one or more skills, encoding the principles
I believe are essential for clean, robust, option-enabling, maintainable,
well-tested, expandable software.

The personas span the roles a well-rounded engineering team needs to cover —
architecture, TDD, code review, security, reliability/infra, accessibility,
and more — each grounded in established engineering practice. See
[PERSONAS.md](./PERSONAS.md) for the full roster and build status.

## Structure

```
.claude-plugin/
  plugin.json        # plugin manifest
  marketplace.json    # self-hosting marketplace entry, for local install/testing
agents/
  <persona>/AGENT.md  # persona definition: frontmatter + system prompt
skills/
  <skill>/SKILL.md    # backing knowledge a persona (or you, directly) can invoke
examples/
  <name>/              # one running example, dogfooded persona-by-persona
```

## Local development

Load this plugin directly from disk without installing it, so changes take
effect on the next restart:

```bash
claude --plugin-dir /Users/kellydiabagate/Documents/kad-developer-suite
```

You can combine this with other `--plugin-dir` flags to load alongside other
plugins you're iterating on.

## Installing for real (once pushed to a repo)

```bash
/plugin marketplace add <your-repo-url>
/plugin
```
Then browse to `kad-dev-team-marketplace` → `kad-dev-team` and install at
user scope.

## Adding a new persona

1. Pick the next row from the roster table in [PERSONAS.md](./PERSONAS.md).
2. Write its backing skill(s) first: `skills/<slug>/SKILL.md`.
3. Write the persona: `agents/<slug>/AGENT.md`, referencing the skill(s) it
   uses in its frontmatter `skills:` list.
4. Test with `--plugin-dir` (above).
5. Flip its Status to Done in PERSONAS.md.
