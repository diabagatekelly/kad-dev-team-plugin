"""Summarise audit-mode logs into what to review first.

Reads the session logs `hooks/audit.sh` writes (KAD_AUDIT=1) and prints one
markdown section per session that used the plugin: where it ran, the
user's prompts in order, every kad-dev-team skill and agent called and
with what arguments, and flags worth a look:

- pushback: a prompt right after a plugin call that reads as a correction
  ("no", "wrong", "undo", "that's not", "didn't ask", ...);
- repeat: the same skill invoked again in the same session;
- no transcript: the session ended without a kept transcript (it may
  still be running, or SessionEnd never fired).

Flags are heuristics to choose which transcripts to read, not verdicts;
the `audit-review` skill does the reading.

Usage: python3 -I evals/tools/audit_report.py [--dir ~/.claude/kad-audit]
           [--since 2026-10-01] [--flagged-only]
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
    for line in open(path):
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    return events


def summarise(sid, events, transcripts):
    cwd, calls, flags, timeline = None, [], [], []
    seen_skills = {}
    last_was_call = False
    for e in events:
        p = e.get("payload", {})
        cwd = cwd or p.get("cwd")
        kind = p.get("hook_event_name")
        if kind == "UserPromptSubmit":
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
    if not os.path.isfile(os.path.join(transcripts, sid + ".jsonl")):
        flags.append("no transcript kept")
    return cwd, calls, flags, timeline


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.environ.get("KAD_AUDIT_DIR", os.path.expanduser("~/.claude/kad-audit")))
    ap.add_argument("--since", default="")
    ap.add_argument("--flagged-only", action="store_true")
    a = ap.parse_args()
    transcripts = os.path.join(a.dir, "transcripts")
    logs = sorted(glob.glob(os.path.join(a.dir, "sessions", "*.jsonl")), key=os.path.getmtime)
    shown = 0
    for path in logs:
        sid = os.path.basename(path)[:-6]
        events = load(path)
        if not events or events[0].get("ts", "") < a.since:
            continue
        cwd, calls, flags, timeline = summarise(sid, events, transcripts)
        if not calls or (a.flagged_only and not flags):
            continue
        shown += 1
        print(f"## {events[0]['ts']} — session `{sid}`")
        print(f"- Directory: `{cwd}`")
        tp = os.path.join(transcripts, sid + ".jsonl")
        if os.path.isfile(tp):
            print(f"- Transcript: `{tp}`")
        print("- Flags: " + ("; ".join(flags) if flags else "none"))
        print("\nTimeline:")
        print("\n".join(timeline))
        print()
    if not shown:
        print("No audited session used the plugin" + (" with flags." if a.flagged_only else "."))


if __name__ == "__main__":
    main()
