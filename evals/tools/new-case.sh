#!/usr/bin/env bash
# Scaffolds a real `claude plugin eval` case that reviews the shared
# library-app fixture: a case.yaml with the prompt preamble, one example
# grader of each kind, and the scaffold.sh stub every library-app case
# needs. Edit the generated case.yaml; the graders are placeholders.
#
# Usage: evals/tools/new-case.sh <case-name> [skill-name]
#   case-name   directory under evals/, hyphenated, no colons
#   skill-name  skill whose invocation the display grader checks
#               (default: the part of case-name before "-review")
set -euo pipefail

name="${1:?usage: new-case.sh <case-name> [skill-name]}"
skill="${2:-${name%%-review*}}"
evals="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dir="$evals/$name"

[[ "$name" =~ ^[a-z0-9-]+$ ]] || { echo "case name must be lowercase, digits and hyphens: $name" >&2; exit 1; }
[ -e "$dir" ] && { echo "already exists: $dir" >&2; exit 1; }
mkdir -p "$dir"

printf '#!/usr/bin/env bash\nexec bash "$(dirname "${BASH_SOURCE[0]}")/../fixtures/library-app/scaffold.sh"\n' > "$dir/scaffold.sh"
chmod +x "$dir/scaffold.sh"

cat > "$dir/case.yaml" <<EOF
schema_version: "1.0"
name: $name
description: "TODO one line: which module/PR is reviewed, which plants and traps it covers"
tags: [$skill, library-app]
context:
  scaffold_script: scaffold.sh
execution:
  prompt: |
    The library-lending app is in your current working directory (its root holds \`package.json\`, \`catalog/\`, \`members/\`, \`lending/\`, \`fines/\`, \`notifications/\`, \`reporting/\`, \`services/\`, \`utils/\`, \`infra/\`, \`main/\`). Read whatever you need; do not modify anything.

    TODO the review request, scoped to one module or one PR. Name files only to set scope, never to point at a defect.
  max_turns: 30
  timeout_seconds: 600
  allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
graders:
  - type: llm
    name: finds-TODO
    focus: last_message
    weight: 1
    criteria: |
      Judge substance only: rule names, category labels and the exact severity word do not matter. What matters is whether the review identifies the problem described and proposes a fix that would address it.

      TODO describe the planted problem from answer-key.md, by file and behaviour, in a way the judge can verify against the review without knowing the key.

      PASS if the review flags it and proposes a fix that would address it.

      FAIL if it is missed, or presented as acceptable.
  - type: llm
    name: no-false-alarm-TODO
    focus: last_message
    weight: 1
    criteria: |
      Judge substance only. This checks that the review does NOT raise a false alarm.

      TODO describe the trap from answer-key.md: what looks wrong and why it isn't.

      PASS if the review does not report it as a violation or a must-fix. Not mentioning it passes; a Low-severity or optional note passes.

      FAIL if it is reported as a violation or a required change.
  - type: tool_used
    name: skill-invoked-display
    tool: Skill
    input_match: '"skill"\\s*:\\s*"(?:[\\w-]+:)?$skill"'
    min: 1
EOF

echo "created $dir/case.yaml and scaffold.sh"
echo "next: fill the TODOs from evals/fixtures/library-app/answer-key.md, then"
echo "  ruby -ryaml -e 'YAML.load_file(\"$dir/case.yaml\")'   # parse check"
echo "  claude plugin eval . --case '$name' --ablation with-without --runs 1 --scaffold --judge-model sonnet --no-publish --trust-plugin"
