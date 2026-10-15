"""Recreate the files an earlier phase wrote, from its frozen history.

A phase that resumes `history.jsonl` starts in a fresh sandbox: the files
the frozen turns wrote with the Write tool (design candidates, a draft
document) are in the transcript but not on disk, so a skill told to
"rewrite the chosen candidate" has nothing to read. A phase's scaffold.sh
calls this after copying the fixture, and the files come back exactly as
the frozen run wrote them.

Only Write calls count (the freeze script already made their paths
relative to the sandbox). A path that is absolute or escapes the target
directory is refused. Nothing is written when the history holds no Write
call; pass --require to make that an error.

Usage: python3 -I evals/tools/history_files.py <history.jsonl> <target-dir> [--require]
"""
import json
import os
import sys


def writes(history):
    for line in open(history, encoding="utf-8"):
        entry = json.loads(line)
        if entry.get("type") != "assistant":
            continue
        content = entry["message"].get("content", "")
        if isinstance(content, str):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            if block.get("name") != "Write":
                continue
            inp = block.get("input") or {}
            path = inp.get("file_path") or inp.get("path")
            if path and "content" in inp:
                yield path, inp["content"]


def main(argv):
    require = "--require" in argv
    argv = [a for a in argv if a != "--require"]
    if len(argv) != 2:
        sys.exit(__doc__)
    history, target = argv
    target = os.path.realpath(target)
    written = []
    for path, content in writes(history):
        if os.path.isabs(path):
            sys.exit(f"refusing absolute path in history: {path}")
        full = os.path.realpath(os.path.join(target, path))
        # realpath follows any symlink already inside the target, so a
        # link pointing out of it is caught too, not only a lexical `..`.
        if os.path.commonpath([target, full]) != target:
            sys.exit(f"refusing path outside {target}: {path}")
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        written.append(path)
    if require and not written:
        sys.exit(f"{history} holds no Write call to recreate")
    for path in written:
        print(f"recreated {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
