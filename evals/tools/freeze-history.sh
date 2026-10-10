#!/usr/bin/env bash
# Freezes one phase of an interactive case as the `context.history_file` the
# next phase resumes. `claude plugin eval` never offers AskUserQuestion, so an
# interactive skill asks in plain text and ends its turn; the next phase's case
# resumes that transcript and its `execution.prompt` is the user's answer.
#
# Keeps only the conversation (user and assistant entries), re-chained so each
# entry's parentUuid points at the previous kept one. Environment, skill
# listings, prompt snapshots and cost state are dropped: the resuming run
# injects its own, and they are noise to review before committing.
#
# Usage: evals/tools/freeze-history.sh <kept-run-dir> <output.jsonl>
#   kept-run-dir  a directory the eval kept with --keep-temp; it is the
#                 parent of `out/` in the run's tracePath (see --json output)
#   output.jsonl  usually evals/<next-phase-case>/history.jsonl
set -euo pipefail

kept="${1:?usage: freeze-history.sh <kept-run-dir> <output.jsonl>}"
out="${2:?usage: freeze-history.sh <kept-run-dir> <output.jsonl>}"

shopt -s nullglob
sessions=("$kept"/config/projects/*-home-cwd/*.jsonl)
[ "${#sessions[@]}" -eq 1 ] || { echo "expected one session transcript under $kept/config/projects/*-home-cwd/, found ${#sessions[@]}" >&2; exit 1; }

python3 -I - "${sessions[0]}" "$out" <<'EOF'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
kept, parent = [], None
for line in open(src):
    entry = json.loads(line)
    if entry.get("type") not in ("user", "assistant") or entry.get("isSidechain"):
        continue
    entry["parentUuid"] = parent
    parent = entry["uuid"]
    kept.append(entry)
if not kept or kept[-1]["type"] != "assistant":
    sys.exit("transcript does not end on an assistant turn; the phase did not finish asking")
with open(dst, "w") as f:
    for entry in kept:
        f.write(json.dumps(entry) + "\n")
print(f"wrote {len(kept)} entries to {dst}; last assistant turn:")
last = kept[-1]["message"]["content"]
print("".join(b.get("text", "") for b in last if isinstance(b, dict))[:600])
EOF
