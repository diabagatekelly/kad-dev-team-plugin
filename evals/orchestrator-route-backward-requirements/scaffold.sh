#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
bash "$here/../fixtures/library-app/scaffold.sh"
mkdir -p docs/pay-fine
cp -R "$here/../fixtures/library-app/route-plants/backward-pm/." docs/pay-fine/
