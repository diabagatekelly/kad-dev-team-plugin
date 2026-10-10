#!/usr/bin/env bash
# Stages the library-app fixture into an eval run's working directory.
# Each library-app-* case holds a one-line scaffold.sh stub that execs this
# script (claude plugin eval only accepts a scaffold_script inside the case
# directory). Runs are launched with `claude plugin eval --scaffold`; without
# the flag the agent sees an empty working directory and cannot review anything.
set -euo pipefail
src="$(cd "$(dirname "${BASH_SOURCE[0]}")/app" && pwd)"
cp -R "$src"/. "$PWD"/
