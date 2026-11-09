#!/usr/bin/env bash
# Freezes one phase of an interactive case as the `context.history_file` the
# next phase resumes. `claude plugin eval` never offers AskUserQuestion, so an
# interactive skill asks in plain text and ends its turn; the next phase's case
# resumes that transcript and its `execution.prompt` is the user's answer.
#
# Keeps only the conversation (user and assistant entries), re-chained so each
# entry's parentUuid points at the previous kept one. Environment, skill
# listings, prompt snapshots and cost state are dropped: the resuming run
# injects its own, and they are noise to review before committing. The
# plugin's absolute path (in the "Base directory for this skill" line) becomes
# `<plugin-root>`, and the freeze refuses to write if the home directory still
# appears anywhere, so a committed history carries no local account name.
# Paths into the frozen run's own sandbox become relative, so the resuming
# run reads and writes inside its own.
#
# Usage: evals/tools/freeze-history.sh <kept-run-dir> <output.jsonl>
#        evals/tools/freeze-history.sh <session.jsonl> <output.jsonl> <ending>
#   kept-run-dir  a phase-1 run the eval kept with --keep-temp; it is the
#                 parent of `out/` in the run's tracePath (see --json output)
#   session.jsonl a resumed phase's transcript. A run that resumes a
#                 history_file writes it next to that history.jsonl (as
#                 <session-id>.jsonl), and every run of the case shares it,
#                 one branch per run
#   ending        text from the chosen run's final message (its `evidence` in
#                 the --json output) that picks that run's branch
#   output.jsonl  usually evals/<next-phase-case>/history.jsonl
set -euo pipefail

usage="usage: freeze-history.sh <kept-run-dir> | <session.jsonl> <output.jsonl> [ending]"
src="${1:?$usage}"
out="${2:?$usage}"
ending="${3:-}"

if [ -d "$src" ]; then
  shopt -s nullglob
  sessions=("$src"/config/projects/*-home-cwd/*.jsonl)
  [ "${#sessions[@]}" -eq 1 ] || { echo "expected one session transcript under $src/config/projects/*-home-cwd/, found ${#sessions[@]}" >&2; exit 1; }
  src="${sessions[0]}"
else
  [ -n "$ending" ] || { echo "a session.jsonl needs <ending> to pick a run's branch" >&2; exit 1; }
fi

plugin_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"

python3 -I - "$src" "$out" "$plugin_root" "$HOME" "$ending" <<'EOF'
import json, os, sys
src, dst, plugin_root, home, ending = sys.argv[1:6]

def text(entry):
    content = entry["message"].get("content", "")
    if isinstance(content, str):
        return content
    return "".join(b.get("text", "") for b in content if isinstance(b, dict))

entries = [json.loads(line) for line in open(src)]
if ending:
    # A resumed run's first entry points into the history it resumed, which
    # the transcript does not repeat: read that history too, then walk back
    # from the leaf whose branch ends with the chosen message.
    resumed = os.path.join(os.path.dirname(src), "history.jsonl")
    pool = entries + ([json.loads(line) for line in open(resumed)] if os.path.exists(resumed) else [])
    by_uuid = {e["uuid"]: e for e in pool if e.get("uuid")}
    matches = [e for e in entries if e.get("type") == "assistant" and not e.get("isSidechain") and ending in text(e)]
    if len(matches) != 1:
        sys.exit(f"expected one assistant message containing the ending, found {len(matches)}")
    chain, node = [], matches[0]
    while node is not None:
        chain.append(node)
        node = by_uuid.get(node.get("parentUuid"))
    entries = list(reversed(chain))

kept, parent = [], None
for entry in entries:
    if entry.get("type") not in ("user", "assistant") or entry.get("isSidechain"):
        continue
    entry["parentUuid"] = parent
    parent = entry["uuid"]
    kept.append(entry)
if not kept or kept[-1]["type"] != "assistant":
    sys.exit("transcript does not end on an assistant turn; the phase did not finish asking")
# The frozen run's sandbox working directory is absolute and will not exist
# for the run that resumes it: a path into it would point outside the new
# sandbox (a write there is refused). Make those paths relative.
# Only absolute ones: the entries a resumed phase inherits from its own
# history carry the "." an earlier freeze wrote, and replacing "./" in every
# string turned the skill text's `/../` into `/.` (found re-freezing a skill
# that names a script by `${CLAUDE_SKILL_DIR}/../`).
cwds = {e.get("cwd") for e in kept if e.get("cwd") and os.path.isabs(e["cwd"])}
def relativize(text):
    for cwd in cwds:
        text = text.replace(cwd + "/", "").replace(cwd, ".")
    return text
lines = [relativize(json.dumps(entry)).replace(plugin_root, "<plugin-root>") + "\n" for entry in kept]
if any(home in line for line in lines):
    sys.exit(f"{home} still appears after replacing the plugin root; remove it by hand before freezing")
with open(dst, "w") as f:
    f.writelines(lines)
print(f"wrote {len(kept)} entries to {dst}; last assistant turn:")
print(text(kept[-1])[:600])
EOF
