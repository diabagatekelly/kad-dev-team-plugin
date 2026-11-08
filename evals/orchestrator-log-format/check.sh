#!/usr/bin/env bash
# Eval case 11 of implementation flow v4, run without a model: the
# orchestrator log checker (evals/tools/orchestrator_log_check.py) against
# two logs.
#
# 1. A v4 entry written from the orchestrator's own template (v4-entry.md
#    here, appended to the loop fixture's planning entries) parses with zero
#    errors.
# 2. The second real run's log (personal-finance-tracker-2, slice 1), read
#    with its three session transcripts and their subagents, reports exactly
#    the five errors in expected-run2.txt (entries 4 and 11's Artifact lines,
#    and entry 28's three real deviations: repeated A/D/E lines, chunk 6
#    with no commit hash, no E line) and none of the "called with no log
#    entry written before it in this session" false positives the checker
#    reported before PR 2 fixed it. That log and those transcripts are
#    private to the owner's machine, so this part runs only when they are
#    given.
#
# Usage: bash evals/orchestrator-log-format/check.sh
#        bash evals/orchestrator-log-format/check.sh <app root> --log planning/orchestrator-log.md \
#             --transcript <session>.jsonl [--transcript ...]
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
evals="$(cd "$here/.." && pwd)"
checker="$evals/tools/orchestrator_log_check.py"
for py in python3 python; do
  if "$py" -I -c "pass" >/dev/null 2>&1; then break; fi
done

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/docs/cancel-hold"
cat "$evals/fixtures/library-app/code-plants/loop/docs/orchestrator-log-planning.md" "$here/v4-entry.md" \
  > "$tmp/docs/cancel-hold/orchestrator-log.md"
out="$("$py" -I "$checker" "$tmp" --log docs/cancel-hold/orchestrator-log.md --no-transcripts 2>&1 || true)"
# Known since 0.14.0 and not this check's: the order check reads entry 4's
# route to `product-slicer` (`vertical-slicing` + `acceptance-criteria`)
# as skipping vertical-slicing on the way to the implementation row. It
# is printed and left out of the count until the checker's reading of a
# persona-plus-skills route is fixed.
known="$(printf '%s\n' "$out" | grep '^- \*\*ERROR\*\*' | grep 'skips vertical-slicing' || true)"
[ -n "$known" ] && echo "KNOWN $known"
errors="$(printf '%s\n' "$out" | grep '^- \*\*ERROR\*\*' | grep -vc 'skips vertical-slicing' || true)"
if [ "$errors" != "0" ]; then
  echo "FAIL  v4 entry: $errors error(s) on the template entry:"
  printf '%s\n' "$out" | grep '^- \*\*ERROR\*\*' | grep -v 'skips vertical-slicing'
  exit 1
fi
echo "PASS  v4 entry: 0 errors on the template entry (entries 1-7 of the loop fixture's log)"

# 1b. The same step lines after two readiness backward routes, in both
#     forms: appended under the second route's entry (slice 2's log, which
#     the checker reads as the chunk-loop entry's since 0.14.1, with a WARN)
#     and under a new chunk-loop entry opened after the last route (what
#     the skill prescribes since 0.14.1). Neither may yield an error, and
#     neither a "stage that ran unlogged" line.
for variant in v4-entry-after-routes v4-entry-new-after-routes; do
  cat "$evals/fixtures/library-app/code-plants/loop/docs/orchestrator-log-planning.md" "$here/$variant.md" \
    > "$tmp/docs/cancel-hold/orchestrator-log.md"
  out="$("$py" -I "$checker" "$tmp" --log docs/cancel-hold/orchestrator-log.md --no-transcripts 2>&1 || true)"
  # the same known order error, left out of the count
  errors="$(printf '%s\n' "$out" | grep '^- \*\*ERROR\*\*' | grep -vc 'skips vertical-slicing' || true)"
  if [ "$errors" != "0" ]; then
    echo "FAIL  $variant: $errors error(s):"
    printf '%s\n' "$out" | grep '^- \*\*ERROR\*\*' | grep -v 'skips vertical-slicing'
    exit 1
  fi
  echo "PASS  $variant: 0 errors (the readiness routes' entries and the loop lines read as one entry)"
done

if [ "$#" -eq 0 ]; then
  echo "SKIP  run 2: no app root given; pass <app root> --log ... --transcript ... to check the second real run"
  echo "log format check: PASS"
  exit 0
fi

run2="$("$py" -I "$checker" "$@" 2>&1 || true)"
got="$tmp/run2-errors.txt"
printf '%s\n' "$run2" | grep '^- \*\*ERROR\*\*' | sed 's/[[:space:]]*$//' > "$got" || true
if ! diff -u "$here/expected-run2.txt" "$got" > "$tmp/run2.diff"; then
  echo "FAIL  run 2: the errors differ from expected-run2.txt:"
  cat "$tmp/run2.diff"
  exit 1
fi
false_positives="$(printf '%s\n' "$run2" | grep -c 'no log entry written before it' || true)"
if [ "$false_positives" != "0" ]; then
  echo "FAIL  run 2: $false_positives 'no log entry written before it' line(s), the false positive PR 2 removed"
  exit 1
fi
echo "PASS  run 2: exactly the $(grep -c '' "$here/expected-run2.txt") expected errors, no false positive"
echo "log format check: PASS"
