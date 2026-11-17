#!/usr/bin/env bash
# C1's "done when" with a real browser: the loop fixture's holds desk is
# captured by the pinned Playwright Chromium and judged by screen_check.py,
# three times over.
#
#   1. The desk as it is on the fixture's `main`: its captures are within
#      the threshold of the baselines committed in the fixture (skipped
#      while those are still the drawn stand-ins, `captures/PLACEHOLDER`).
#   2. The slice's style change as intended (the refusal notice alone):
#      the verdict is BASELINES OWED, one changed and one new, and nothing
#      is reported.
#   3. The same change written on the rule every notice shares: the
#      verdict is FAIL, `hold-cancelled` is reported and
#      `hold-not-cancelled` is not.
#
# Run by .github/workflows/fixture-screens.yml on Ubuntu 24.04, which is
# the one fixed environment the fixture's images come from: the captures
# it leaves under <work dir>/out/ are that workflow's artifact, and the
# fixture's baselines and its two capture sets are copied from it.
# Anywhere else it needs network for `npm ci` and the browser download,
# and its pixels are that machine's, not the fixture's.
#
# Usage: bash evals/tools/fixture_screens.sh <work dir>
set -euo pipefail

work="${1:?usage: fixture_screens.sh <work dir>}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
screens="$root/evals/fixtures/library-app/code-plants/loop/screens"
project="$work/project"
out="$work/out"
planning=docs/cancel-hold

rm -rf "$project" "$out"
mkdir -p "$project/$planning" "$project/tools" "$out"
cp -R "$screens/base/." "$project/"
cp -R "$screens/base-planning/." "$project/$planning/"
cp "$root/skills/ci-pipeline/screens/capture.mjs" "$root/skills/ci-pipeline/screens/package.json" \
  "$root/skills/ci-pipeline/screens/package-lock.json" "$project/screens/"
cp "$root/skills/orchestrator/scripts/screen_check.py" "$project/tools/screen_check.py"
cd "$project"

(cd screens && npm ci --no-audit --no-fund && npx playwright install --with-deps chromium)

judge() {  # judge <name> <expected exit> <expected last line>
  local name="$1" want="$2" last="$3" code=0
  node screens/capture.mjs --out "$out/$name/captures"
  python3 -I tools/screen_check.py compare --planning "$planning" --captures "$out/$name/captures" --out "$out/$name" || code=$?
  local got; got="$(tail -1 "$out/$name/screen-check.txt")"
  if [ "$code" != "$want" ] || [ "$got" != "$last" ]; then
    echo "fixture screens: $name: expected exit $want and '$last'; got exit $code and '$got'" >&2
    exit 1
  fi
  echo "ok: $name: $got"
}

if [ -f "$screens/captures/PLACEHOLDER" ]; then
  # First run: the fixture's images are still drawn stand-ins. Take this
  # run's own capture of the desk as the baselines for steps 2 and 3.
  node screens/capture.mjs --out "$out/base/captures"
  rm -f "$planning/visual-ux/baselines/"*.png
  cp "$out/base/captures/"*.png "$planning/visual-ux/baselines/"
  echo "note: the fixture's baselines are stand-ins; this run's captures are in the artifact to replace them"
else
  judge base 0 "screens: PASS (2 states)"
fi

cp -R "$screens/slice-planning/." "$planning/"
cp "$screens/slice/screens/states.mjs" screens/states.mjs
cp "$screens/slice/main/desk.css" main/desk.css
judge intended 3 "screens: BASELINES OWED 1 changed, 1 new, 0 removed"

cp "$screens/planted/main/desk.css" main/desk.css
judge planted 1 "screens: FAIL 1 not listed: hold-cancelled"
grep -q '^changed  *hold-not-cancelled:' "$out/planted/screen-check.txt" \
  || { echo "fixture screens: planted: the intended change to hold-not-cancelled was not read as listed" >&2; exit 1; }
echo "fixture screens: the stray change is reported and the intended one is not"
