#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/self-service
cp "$here/../fixtures/library-app/planning/self-service/problem.md" docs/self-service/
