"""Summarise audit-mode logs into what to review first.

Reads the session logs `hooks/audit.sh` writes (KAD_AUDIT=1) and prints one
markdown section per session that used the plugin: where it ran, the
user's prompts in order, every kad-dev-team skill and agent called and
with what arguments, where its transcript is, and flags worth a look:

- pushback: a prompt right after a plugin call that reads as a correction
  ("no", "wrong", "undo", "that's not", "didn't ask", ...);
- repeat: the same skill invoked again in the same session;
- open: no SessionEnd in the log (still running, or ended without one);
- withheld: the audit sync (`audit_sync.py --transcripts`) found a value
  of a listed source in the session's transcripts and kept them back,
  read from the sync logs in the audit repository's clone;
- on disk, not copied: the transcript Claude Code writes is there (the
  path the hook payloads name) but no snapshot was kept and the sync has
  not carried it, so it is only on this machine;
- no transcript: not on disk and none kept (deleted, or transcript saving
  was off for the session).

Flags are heuristics to choose which transcripts to read, not verdicts;
the `audit-review` skill does the reading.

Usage: python3 -I evals/tools/audit_report.py [--dir ~/.claude/kad-audit]
           [--clone <dir>] [--since 2026-10-01] [--flagged-only]
"""
import argparse
import glob
import json
import os
import re

PUSHBACK = re.compile(
    r"(?i)^\s*(no\b|nope|wrong|undo|revert|stop\b|that'?s not|that is not|not what i|"
    r"didn'?t ask|don'?t\b|why did you|you (?:shouldn'?t|should not|missed|forgot))")


def short(value, n=160):
    text = value if isinstance(value, str) else json.dumps(value)
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1] + "…"


def load(path):
    events = []
    for line in open(path, encoding="utf-8", errors="replace"):
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    return events


def withheld_sessions(clone):
    """session id -> the sync-log line that withheld it (the latest), from
    every slice folder's sync-log.md in the clone."""
    out = {}
    for path in sorted(glob.glob(os.path.join(clone, "*", "sync-log.md"))):
        try:
            lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        for line in lines:
            if "withheld:" not in line:
                continue
            for sid in re.findall(r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}) \(", line.split("withheld:", 1)[1]):
                out[sid] = f"{os.path.basename(os.path.dirname(path))}: {line.strip()[2:]}"
    return out


def summarise(sid, events, transcripts, withheld):
    cwd, calls, flags, timeline = None, [], [], []
    live = None
    ended = False
    seen_skills = {}
    last_was_call = False
    for e in events:
        p = e.get("payload", {})
        cwd = cwd or p.get("cwd")
        live = live or p.get("transcript_path")
        kind = p.get("hook_event_name")
        if kind == "SessionEnd":
            ended = True
        elif kind == "UserPromptSubmit":
            prompt = p.get("prompt", "")
            timeline.append(f"- {e['ts']} > {short(prompt)}")
            if last_was_call and PUSHBACK.search(prompt):
                flags.append(f"pushback at {e['ts']}: \"{short(prompt, 100)}\"")
            last_was_call = False
        elif kind == "PostToolUse":
            ti = p.get("tool_input", {}) or {}
            name = ti.get("skill") or ti.get("subagent_type")
            if not name or "kad-dev-team" not in name:
                continue
            calls.append((e["ts"], p.get("tool_name"), name, ti.get("args") or ti.get("description") or ""))
            timeline.append(f"- {e['ts']} · {p.get('tool_name')} `{name}` {short(ti.get('args') or ti.get('description') or '', 120)}")
            last_was_call = True
            seen_skills[name] = seen_skills.get(name, 0) + 1
            if seen_skills[name] == 2:
                flags.append(f"repeat: {name} invoked more than once")
    if not ended:
        flags.append("open: no SessionEnd in the log (still running, or ended without one)")
    kept = os.path.join(transcripts, sid + ".jsonl")
    if os.path.isfile(kept):
        where = f"kept: `{kept}`"
    elif sid in withheld:
        where = f"withheld by the audit sync ({withheld[sid]})" + (f"; on disk at `{live}`" if live and os.path.isfile(live) else "")
        flags.append("withheld: a listed source's value in its transcripts; the owner decides")
    elif live and os.path.isfile(live):
        where = f"on disk, not copied: `{live}` ({os.path.getsize(live) // 1024} KB; run audit_sync.py --transcripts to carry it)"
        flags.append("transcript on disk, not copied")
    else:
        where = "none: not on disk and none kept"
        flags.append("no transcript: not on disk and none kept (deleted, or saving was off)")
    return cwd, calls, flags, timeline, where


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.environ.get("KAD_AUDIT_DIR", os.path.expanduser("~/.claude/kad-audit")))
    ap.add_argument("--clone", help="the audit repository's clone, whose sync logs name the withheld sessions (default: <dir>/repo)")
    ap.add_argument("--since", default="")
    ap.add_argument("--flagged-only", action="store_true")
    a = ap.parse_args()
    transcripts = os.path.join(a.dir, "transcripts")
    withheld = withheld_sessions(a.clone or os.path.join(a.dir, "repo"))
    logs = sorted(glob.glob(os.path.join(a.dir, "sessions", "*.jsonl")), key=os.path.getmtime)
    shown = 0
    for path in logs:
        sid = os.path.basename(path)[:-6]
        events = load(path)
        if not events or events[0].get("ts", "") < a.since:
            continue
        cwd, calls, flags, timeline, where = summarise(sid, events, transcripts, withheld)
        if not calls or (a.flagged_only and not flags):
            continue
        shown += 1
        print(f"## {events[0]['ts']} — session `{sid}`")
        print(f"- Directory: `{cwd}`")
        print(f"- Transcript: {where}")
        print("- Flags: " + ("; ".join(flags) if flags else "none"))
        print("\nTimeline:")
        print("\n".join(timeline))
        print()
    if not shown:
        print("No audited session used the plugin" + (" with flags." if a.flagged_only else "."))


if __name__ == "__main__":
    main()
