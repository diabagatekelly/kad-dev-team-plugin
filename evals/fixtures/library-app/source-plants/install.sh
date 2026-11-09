#!/usr/bin/env bash
# Puts the owner's "sheet" beside an eval run's project: the invented fee
# export in `owner-files/` (the owner's own folder: ignored by git when the
# working directory is a repository, so nothing can commit it), and, with a
# target directory as the argument, the `sources.md` a planning stage would
# have written when the owner first pointed at the file. Every row of
# desk-fees.csv is made up; README.md here says what each case plants.
#
# Usage, from the eval run's working directory:
#   bash install.sh [target directory]
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p owner-files
cp "$here/desk-fees.csv" owner-files/desk-fees.csv
if [ -d .git ]; then
  printf 'owner-files/\n' >> .git/info/exclude
fi
if [ -n "${1:-}" ]; then
  mkdir -p "$1"
  cp "$here/sources.md" "$1/sources.md"
fi
