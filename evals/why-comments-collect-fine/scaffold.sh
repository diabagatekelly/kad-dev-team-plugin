#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
cp "$here/../fixtures/library-app/docs-plants/why-comments/fines/collect-fine.ts" fines/collect-fine.ts
