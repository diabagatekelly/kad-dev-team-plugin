#!/usr/bin/env bash
# An empty repository holding only the bank-connection problem and its
# agreed requirements (fixtures/bank-connection/docs/).
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
cp -R "$here/../fixtures/bank-connection/docs" "$PWD"/
