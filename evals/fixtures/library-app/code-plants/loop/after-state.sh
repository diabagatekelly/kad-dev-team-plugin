#!/usr/bin/env bash
# A step past one of state.sh's states, for the 0.17.0 cases: each variant
# is run by a case's scaffold right after `state.sh <state>`, in the same
# directory, and leaves what a previous session would have left one step
# further on. state.sh is not changed by these (its states' trees stay as
# `loop_states.json` records them); a case that uses a variant depends on
# this file through its own scaffold.
#
# Usage, from the eval run's working directory:
#   bash after-state.sh <variant>
# Variants, with the state each follows:
#   gate-fixer-check   after `chunk1-outside`: the gate on chunk 1 failed
#                      on scope (really run, saved as gate-chunk-1-r0.txt),
#                      the gate's own fixer moved the card wording into the
#                      lending module and left it exported there, where
#                      nothing imports it, and the gate on that fix (really
#                      run, gate-chunk-1-r0-fix.txt) fails on one line, the
#                      unused-code count one over its baseline; next: the
#                      runner's step 2 from that second gate file
#   gate-fixer-suite   the same, the fixer having reworded the rejection
#                      reason instead: the second gate fails on the suite
#   light              after `chunk1-built`: the A line and the handoff say
#                      the cadence is `light`
#   card-wording       after `chunk1-gated`: one more commit keeps the
#                      card's wording in `lending/card-wording.ts` (the
#                      full number, which the rejection reason uses, and
#                      the masked form, which nothing but its test uses
#                      yet), and the plan gains a fourth chunk, masking
#                      the card number in the rejection reason. Planted
#                      (answer key L18): once the reason is masked nothing
#                      imports the full-number helper, so the unused-code
#                      count is one over its baseline
#   named-test         after `chunk1-gated`: one more commit pins the
#                      rejection reason's wording with a test the plan
#                      names, `the rejection reason names the card and the
#                      ISBN` (two assertions: the card number, the ISBN),
#                      and round 0's review, with its finding that the
#                      reason carries the whole card number, is in the
#                      records. Planted (answer key L19): the fix changes
#                      what that test checks
set -euo pipefail

variant="${1:?usage: after-state.sh <variant>}"
loop="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plugin="$(cd "$loop/../../../../.." && pwd)"
scripts="$plugin/skills/orchestrator/scripts"
for py in python3 python; do
  if "$py" -I -c "pass" >/dev/null 2>&1; then break; fi
done

target=docs/cancel-hold
records=$target/implementation
report=$records/implementation-report-slice-001.md
log=$target/orchestrator-log.md
handoff=$records/handoff-slice-001.md
chunk1_files=(lending/hold-queue.ts lending/cancel-hold.ts infra/memory/in-memory-hold-queue.ts test/cancel-hold.test.ts test/in-memory-hold-queue.test.ts)
protect=($target/slice-001.md $target/design-001.md $target/requirements-001.md $target/user-story-001.md $target/problem.md)

sha_of() { git log --format=%h -1 --grep "$1"; }

gate() {  # gate <base> <out>: the real gate on chunk 1's files, as state.sh runs it
  local args=()
  for f in "${chunk1_files[@]}"; do args+=(--allow "$f"); done
  for f in "${protect[@]}"; do args+=(--protect "$f"); done
  "$py" -I "$scripts/validation_gate.py" --project . --base "$1" --test-cmd 'npm test' \
    "${args[@]}" --allow "$records/" --allow "$log" --module-dir lending/ --module-dir infra/memory/ --coverage \
    > "$2" 2>&1 || true
}

rewrite() {  # rewrite <file> <line start> <new line>: one line of a file replaced, found exactly once
  "$py" -I - "$@" <<'PY'
import sys
path, start, new = sys.argv[1:4]
lines = open(path, encoding="utf-8").read().split("\n")
hits = [i for i, line in enumerate(lines) if line.startswith(start)]
if len(hits) != 1:
    sys.exit(f"after-state.sh: {start!r} found {len(hits)} times in {path}")
lines[hits[0]] = new
open(path, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
PY
}

replace() {  # replace <file> <old> <new>: one piece of text replaced, found exactly once
  "$py" -I - "$@" <<'PY'
import sys
path, old, new = sys.argv[1:4]
text = open(path, encoding="utf-8").read()
if text.count(old) != 1:
    sys.exit(f"after-state.sh: {old!r} found {text.count(old)} times in {path}")
open(path, "w", encoding="utf-8", newline="\n").write(text.replace(old, new))
PY
}

commit_handoff() {
  git add "$handoff"
  git commit -qm "Records: slice 001 handoff"
}

case "$variant" in
  gate-fixer-check|gate-fixer-suite)
    plan_sha="$(sha_of '^Plan: slice 001')"
    c1_sha="$(sha_of "^Cancel a member's hold on a title")"
    gate "$plan_sha" "$records/gate-chunk-1-r0.txt"
    grep -q '^FAIL  scope' "$records/gate-chunk-1-r0.txt" || { echo "after-state.sh: the first gate did not fail on scope" >&2; exit 1; }
    git rm -q utils/card-number.ts
    if [ "$variant" = gate-fixer-check ]; then
      replace lending/cancel-hold.ts "import { describeCard } from '../utils/card-number';
" ""
      printf '\nexport function describeCard(cardNumber: string): string {\n  return `card ${cardNumber}`;\n}\n' >> lending/cancel-hold.ts
      want='^FAIL  check unused-export'
    else
      replace lending/cancel-hold.ts "import { describeCard } from '../utils/card-number';
" ""
      replace lending/cancel-hold.ts '`${describeCard(cardNumber)} has no hold on ${isbn}`' '`nothing is held on ${isbn} for card ${cardNumber}`'
      want='^FAIL  suite'
    fi
    git add lending/cancel-hold.ts
    git commit -qm "Keep the card wording inside the lending module"
    g_sha="$(git rev-parse --short HEAD)"
    gate "$plan_sha" "$records/gate-chunk-1-r0-fix.txt"
    grep -q "$want" "$records/gate-chunk-1-r0-fix.txt" || { echo "after-state.sh: the second gate did not fail as planted ($want)" >&2; cat "$records/gate-chunk-1-r0-fix.txt" >&2; exit 1; }
    [ "$(grep -c '^FAIL  ' "$records/gate-chunk-1-r0-fix.txt")" = 1 ] || { echo "after-state.sh: the second gate fails on more than one line" >&2; cat "$records/gate-chunk-1-r0-fix.txt" >&2; exit 1; }
    rewrite "$handoff" '- **State:**' "- **State:** C.2 for chunk 1 of 3: the implementer (agent-2b8e, 43 turns) committed $c1_sha; the gate on $plan_sha..$c1_sha failed ($records/gate-chunk-1-r0.txt); the gate's own fixer (agent-77d0, 9 turns) handed back with commit $g_sha; the gate on $plan_sha..$g_sha is saved as $records/gate-chunk-1-r0-fix.txt and nothing has been done since"
    rewrite "$handoff" '- **Next action:**' "- **Next action:** the runner's step 2, from that second gate file"
    replace "$handoff" "reviewer launches 0; fixers 0;" "reviewer launches 0; fixers 1;"
    commit_handoff ;;
  light)
    replace "$log" 'cadence — `loop`' 'cadence — `light`'
    replace "$handoff" 'cadence loop;' 'cadence light;'
    git add "$handoff"
    git commit -q --amend --no-edit ;;
  card-wording)
    cat > lending/card-wording.ts <<'TS'
export function fullCard(cardNumber: string): string {
  return `card ${cardNumber}`;
}

export function maskedCard(cardNumber: string): string {
  return `card ending ${cardNumber.slice(-4)}`;
}
TS
    replace lending/cancel-hold.ts "import type { HoldQueue } from './hold-queue';" "import { fullCard } from './card-wording';
import type { HoldQueue } from './hold-queue';"
    replace lending/cancel-hold.ts '`card ${cardNumber} has no hold on ${isbn}`' '`${fullCard(cardNumber)} has no hold on ${isbn}`'
    cat > test/card-wording.test.ts <<'TS'
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { maskedCard } from '../lending/card-wording';

test('a masked card shows its last four characters and nothing before them', () => {
  assert.equal(maskedCard('4111222233334444'), 'card ending 4444');
});
TS
    replace "$report" "### Chunk 1: Cancel a member's hold on a title" "### Chunk 4
- **Title**: Mask the card number in the rejection reason
- **Delivers**: Security \"a rejection's reason shows no more of the member's card number than its last four characters\"
- **Files**: lending/cancel-hold.ts; test/cancel-hold.test.ts
- **Done when**: seam \"a rejected cancel through the real in-memory queue shows only the last four characters of the card\" is green
- **Touches**: none

### Chunk 1: Cancel a member's hold on a title"
    printf -- '- **Fix r1**: this commit; the card wording kept in one module (`lending/card-wording.ts`), the masked form for the desk notice of chunk 3\n' >> "$report"
    git add lending/card-wording.ts lending/cancel-hold.ts test/card-wording.test.ts "$report"
    git commit -qm "Keep the card wording in one module"
    # The slice's criterion the fourth chunk delivers, added by its owner.
    replace "$target/slice-001.md" "- Reliability: a cancel asked for twice" "- Security: a rejection's reason shows no more of the member's card
  number than its last four characters.
- Reliability: a cancel asked for twice"
    git add "$target/slice-001.md"
    git commit -qm "Planning: the rejection reason masks the card number"
    w_sha="$(git rev-parse --short HEAD)"
    "$py" -I "$scripts/validation_gate.py" --project . --test-cmd 'npm test' --checks-only > /dev/null \
      || { echo "after-state.sh: the checks do not pass before the fourth chunk" >&2; exit 1; }
    rewrite "$handoff" '- **State:**' "- **State:** chunks 1 to 3 of 4 are not this session's: chunk 4 was added to the plan after the security review of chunk 1 and is built first; the commit before it is $w_sha"
    rewrite "$handoff" '- **Next action:**' "- **Next action:** C.1: build chunk 4"
    commit_handoff ;;
  named-test)
    plan_sha="$(sha_of '^Plan: slice 001')"
    c1_sha="$(sha_of "^Cancel a member's hold on a title")"
    cat >> test/cancel-hold.test.ts <<'TS'

test('the rejection reason names the card and the ISBN', async () => {
  const queue = await queueWith([isbn, '1001']);
  const result = await new CancelHold(queue).run(isbn, '4111222233334444');
  assert.match(result.reason ?? '', /4111222233334444/);
  assert.match(result.reason ?? '', /9780140449136/);
});
TS
    replace "$report" '`removes only that member'"'"'s hold on that title`, `in-memory queue removes' '`removes only that member'"'"'s hold on that title`, `the rejection reason names the card and the ISBN`, `in-memory queue removes'
    replace "$report" '- **Commit**: this commit; 7 tests green' "- **Commit**: $c1_sha; 8 tests green"
    git add test/cancel-hold.test.ts "$report"
    git commit -qm "Pin the rejection reason's wording"
    n_sha="$(git rev-parse --short HEAD)"
    gate "$plan_sha" "$records/gate-chunk-1-r0.txt"
    grep -q '^validation gate: PASS' "$records/gate-chunk-1-r0.txt" || { echo "after-state.sh: the gate does not pass before the fix" >&2; cat "$records/gate-chunk-1-r0.txt" >&2; exit 1; }
    sed "s/@PLAN@/$plan_sha/; s/@C1@/$n_sha/" "$loop/records/chunk-1-r0-review.md" > "$records/chunk-1-r0-review.md"
    cp "$loop/records/chunk-1-r0-smoke.md" "$records/"
    "$py" -I "$scripts/rounds_record.py" --sidecar "$records/rounds-slice-001.jsonl" --report "$records/chunk-1-r0-review.md" \
      --report "$records/chunk-1-r0-smoke.md" --chunk 1 --round 0 > /dev/null
    rewrite "$handoff" '- **State:**' "- **State:** C.4 for chunk 1 of 3: round 0 recorded (0/0/2, smoke PASS); the reports are $records/chunk-1-r0-review.md and $records/chunk-1-r0-smoke.md; no fixer has been launched; the chunk's last commit is $n_sha"
    rewrite "$handoff" '- **Next action:**' "- **Next action:** the runner's step 4: one fixer for round 0's findings"
    replace "$handoff" "reviewer launches 0; fixers 0;" "reviewer launches 2; fixers 0;"
    commit_handoff ;;
  *) echo "unknown variant: $variant" >&2; exit 1 ;;
esac
