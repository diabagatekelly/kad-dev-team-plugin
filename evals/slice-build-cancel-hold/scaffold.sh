#!/usr/bin/env bash
# The cancel-hold slice, fully planned, on its slice branch with nothing
# built: the loop fixture's base (fixtures/library-app/code-plants/loop/base.sh;
# everything under fixtures/library-app/code-plants/loop/ is loaded) over
# the app, the fixtures/library-app/code-plants/tdd/ runner and the
# fixtures/library-app/route-plants/cancel-hold/ planning set, and the
# task the orchestrator's S step hands its one builder, as a file (the
# paths are this run's own).
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$here/../fixtures/library-app/code-plants/loop/base.sh" "$here/../fixtures/library-app/route-plants/cancel-hold"
git checkout -q -b slice-001-cancel-hold
plugin="$(cd "$here/../.." && pwd)"
root="$PWD"
target="$root/docs/cancel-hold"
mkdir -p "$target/implementation"
cat > "$target/implementation/build-task.md" <<EOF
# Task: build slice 001

Invoke \`kad-dev-team:slice-build\` first, by name, and build the whole slice as it says. The orchestrator checks the result, and you commit.

- Slice file: \`$target/slice-001.md\`
- Design: \`$target/design-001.md\`
- Domain model: none in this project
- Security and reliability criteria: in the slice file (this slice has no separate documents)
- Screen design and accessibility criteria: none, the slice has no screen
- Read context: \`$target/requirements-001.md\`
- Project root: \`$root\`
- Test command: \`npm test\`
- Report path: \`$target/implementation/implementation-report-slice-001.md\`
- Module directories: \`lending/\`, \`infra/memory/\`
- Scripts directory: \`$plugin/skills/orchestrator/scripts\`
EOF
printf 'docs/cancel-hold/implementation/build-task.md\n' >> .git/info/exclude
