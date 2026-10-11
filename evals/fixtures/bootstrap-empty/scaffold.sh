#!/usr/bin/env bash
# Stages an empty repo holding only docs/ into the eval working directory.
set -euo pipefail
cp -R "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docs" "$PWD"/
