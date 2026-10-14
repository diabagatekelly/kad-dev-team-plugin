"""Which frozen phase histories carry skill text that no longer matches the skill.

A `history.jsonl` holds every skill's SKILL.md as it was loaded in the
frozen turn; a later phase keeps running that text until the earlier
phase is re-run and re-frozen. For each `evals/*/history.jsonl` this
prints the skills it loaded and whether each still matches
`skills/<name>/SKILL.md` (frontmatter and the CLI's appended
`ARGUMENTS:` line aside), with the number of differing lines when not.

Usage: python3 -I evals/tools/history_stale.py [case ...]
Exit 1 if any history is stale.
"""
import difflib
import glob
import json
import os
import re
import sys

EVALS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(EVALS)
LOADED = re.compile(r"Base directory for this skill: <plugin-root>/skills/([\w-]+)\s*\n\n([\s\S]*)")


def texts(entry):
    content = entry["message"].get("content", "")
    if isinstance(content, str):
        return [content]
    out = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            out.append(block.get("text", ""))
        elif isinstance(block.get("content"), str):
            out.append(block["content"])
        elif isinstance(block.get("content"), list):
            out.append("".join(x.get("text", "") for x in block["content"] if isinstance(x, dict)))
    return out


def current(name):
    path = os.path.join(ROOT, "skills", name, "SKILL.md")
    text = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    return re.sub(r"^---[\s\S]*?---\s*\n", "", text).strip()


def loaded_skills(history):
    for line in open(history, encoding="utf-8"):
        entry = json.loads(line)
        if entry.get("type") != "user":
            continue
        for text in texts(entry):
            m = LOADED.match(text or "")
            if m:
                body = re.sub(r"\n+ARGUMENTS:[\s\S]*$", "", m.group(2)).strip()
                yield m.group(1), body


def main(argv):
    histories = sorted(glob.glob(os.path.join(EVALS, "*", "history.jsonl")))
    if argv:
        histories = [h for h in histories if os.path.basename(os.path.dirname(h)) in argv]
    stale = 0
    for history in histories:
        case = os.path.basename(os.path.dirname(history))
        parts = []
        for name, body in loaded_skills(history):
            cur = current(name)
            if cur == body:
                parts.append(f"{name}: current")
            else:
                diff = [d for d in difflib.unified_diff(body.splitlines(), cur.splitlines(), lineterm="", n=0)
                        if d[:1] in "+-" and d[:3] not in ("+++", "---")]
                parts.append(f"{name}: STALE ({len(diff)} lines differ)")
                stale += 1
        print(f"{case}: {'; '.join(parts) or 'no skill text'}")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
