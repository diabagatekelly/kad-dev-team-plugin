#!/usr/bin/env bash
# The pay-a-fine planning set with its accessibility criteria, the one-file
# portal (fixtures/library-app/ui-plants/ac-walk/serve.mjs) and the
# orchestrator's scratch launcher copied in as tools/scratch_run.py, since
# a real launch hands the agent the launcher by absolute path.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
fx="$here/../fixtures/library-app"
bash "$fx/scaffold.sh"
mkdir -p docs/pay-fine tools
cp "$fx/planning/pay-fine-design/problem.md" "$fx/planning/pay-fine-design/requirements-001.md" "$fx/ui-plants/pay-fine/design-001.md" "$fx/ui-plants/pay-fine/slice-001.md" docs/pay-fine/
cp "$fx/ui-plants/ac-walk/accessibility-review-001.md" docs/pay-fine/
cp "$fx/ui-plants/ac-walk/serve.mjs" tools/serve.mjs
cp "$here/../../skills/orchestrator/scripts/scratch_run.py" tools/scratch_run.py
