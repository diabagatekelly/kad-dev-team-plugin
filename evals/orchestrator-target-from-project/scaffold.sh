#!/usr/bin/env bash
# The library app, with a CLAUDE.md at its root that names the directory
# the project's planning artifacts live in. Nothing exists there yet.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
cat > CLAUDE.md <<'EOF'
# Library lending service

A small lending service for a public library: members, loans, holds, fines.

- Run the tests with `npm test`.
- Planning artifacts for every feature (problem docs, requirements, slices, designs, the orchestrator's log) live in `docs/planning/`.
- Code is TypeScript; `lending/` holds the use cases, `infra/` the adapters.
EOF
