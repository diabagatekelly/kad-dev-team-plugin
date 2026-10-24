"""Check a real project's orchestrator-log.md against the orchestrator's rules.

Reads the log in a project that used kad-dev-team, and (when given) the
transcripts audit mode kept for it, and prints a markdown report of:

- format: sequence numbers in order with no gaps, every `## ` heading a
  numbered entry, exactly one Routed to and one Artifact line in every
  entry, the Artifact one path inside the project (no bare directory, no
  "if"/"otherwise"/"or" outside a parenthetical), quarantine entries with
  their A-E sub-entries in order;
- artifacts: each entry's path exists (relative to the log's directory, or
  the project), or else which files the transcripts show that stage
  writing instead;
- order: each route against the state table in skills/orchestrator/SKILL.md
  (read from the file, so the table and this check can't drift apart): a
  stage skipped that the table never skips, or a step backwards that
  doesn't say it's a backward route;
- append-only: every committed version of the log, and the working copy,
  starts with the one before it; with transcripts, every successful write
  to the log (Write, Edit, or a shell redirect) only adds to its end;
- log vs. calls (transcripts only): every spine skill called has an entry
  written before it in that session, each entry is followed by exactly one
  call to its routed skill (a quarantine entry by any number of
  implementer launches), and every entry was followed by its routed skill.

Read-only; nothing in the project is changed. Findings are marked ERROR
(the rule is broken), WARN (worth reading) or INFO. Check a session
against the rules of the plugin version that ran it: every Skill result in
a transcript begins with `Base directory for this skill:
.../kad-dev-team/<version>/skills/<name>`, `git log -S'"version":
"<version>"' -- .claude-plugin/plugin.json` names that version's bump
commit, and `git show <commit>:skills/orchestrator/SKILL.md > /tmp/x.md`
gives the file to pass with --skill. --skill only sets the state table:
the Artifact-line rules are the current ones, so a log written under
0.4.0, which predates them, fails them as expected.

Usage: python3 -I evals/tools/orchestrator_log_check.py <project dir>
           [--log planning/orchestrator-log.md] [--skill path/to/SKILL.md]
           [--audit-dir ~/.claude/kad-audit | --transcript t.jsonl ...]
           [--no-transcripts]
Exits 1 when there is any ERROR.
"""
import argparse
import glob
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SKILL = os.path.join(HERE, "..", "..", "skills", "orchestrator", "SKILL.md")
LOG_NAME = "orchestrator-log.md"

# Stages the table can legitimately pass over: the scope decision is made
# once per problem, the design system and stack once per project, and the
# UI rows only apply to a UI-touching slice.
SKIPPABLE = {"scope-map", "design-system", "technology-bootstrap"}
UI_ONLY = {"design-system", "screen-design", "accessibility-review"}
# After a slice is implemented, the next unit starts again at requirements.
RESTARTS = {"requirements-refinement"}
QUARANTINE_STEPS = "ABCDE"
# The persona that implements; its launches under a quarantine entry are many.
IMPLEMENTERS = {"tdd-implementation", "tdd-implementation-lite", "tdd-coach"}
CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def norm(path):
    return os.path.normcase(os.path.normpath(path)) if path else ""


def inside(path, root):
    """True when `path` is `root` or a file or directory under it (path-aware, not a string prefix)."""
    try:
        return os.path.commonpath([norm(os.path.abspath(path)), norm(os.path.abspath(root))]) == norm(os.path.abspath(root))
    except ValueError:  # different drives
        return False


def safe(text):
    """Untrusted log or transcript text, with terminal control characters removed."""
    return CONTROL.sub("?", str(text))


def load_table(skill_path):
    """The state table's rows in order: (state text, set of skill names it routes to)."""
    rows = []
    for line in open(skill_path, encoding="utf-8"):
        if not line.startswith("| ") or line.startswith("| Detected state") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        names = set()
        for tok in re.findall(r"`([^`]+)`", cells[1]):
            names.add(tok.split(":")[-1].strip())
        if "tdd-implementation" in names:
            names |= IMPLEMENTERS
        if names:
            rows.append((cells[0], names))
    if not rows:
        raise SystemExit(f"no state table found in {skill_path}")
    return rows


def stage_key(names):
    """A row's own name: the skill it routes to, or for docs-writer's scope decision, scope-map."""
    for n in ("scope-map", "vertical-slicing", "tdd-implementation"):
        if n in names:
            return n
    return sorted(n for n in names if "-" in n)[0] if any("-" in n for n in names) else sorted(names)[0]


def parse_log(text):
    """(entries, malformed headings). A heading is `## <n>. <title>`; any other `## ` line is malformed."""
    entries, malformed = [], []
    for m in re.finditer(r"^## (.*)$", text, re.M):
        if not re.match(r"\d+\.\s", m.group(1) + " "):
            malformed.append(m.group(1).strip())
    for m in re.finditer(r"^## (\d+)\.\s*(.*)$", text, re.M):
        end = text.find("\n## ", m.end())
        body = text[m.end(): end if end != -1 else len(text)]
        routed = re.findall(r"^\*\*Routed to:\*\*\s*(.+)$", body, re.M)
        artifact = re.findall(r"^\*\*Artifact:\*\*\s*(.+)$", body, re.M)
        subs = re.findall(r"^- \*\*([A-E])\.", body, re.M)
        entries.append({
            "n": int(m.group(1)), "heading": m.group(2).strip(), "body": body,
            "routed": routed[0].strip() if routed else None, "routed_lines": len(routed),
            "artifact": artifact[0].strip() if artifact else None, "artifact_lines": len(artifact),
            "subs": subs,
        })
    return entries, malformed


def is_quarantine(entry):
    return bool(entry and entry["routed"] and "quarantine" in entry["routed"].lower())


NONE = "none"  # an entry routed outside the spine ("none (user-directed)")


def routed_names(routed):
    """The names an entry's Routed to line puts in backticks, in order: skill and persona halves of each."""
    out = []
    for t in re.findall(r"`([^`]+)`", routed or ""):
        for part in (t.split(":")[-1].strip(), t.split(":")[0].strip()):
            if part and part not in out:
                out.append(part)
    return out


def route_rank(routed, table):
    """Index of the table row an entry routed to; NONE for an entry routed outside the spine;
    None if it names nothing in the table. The first skill named decides the row."""
    low = (routed or "").lower().strip()
    if "quarantine" in low:
        return next(i for i, (_, names) in enumerate(table) if "tdd-implementation" in names)
    if low.startswith(NONE):
        return NONE
    toks = routed_names(routed)
    specific = [t for t in toks if "-" in t and t != "docs-writer"]
    if not specific and "scope" in low:
        # docs-writer routes to several rows; a plain docs-writer route that names the
        # scope decision is the scope-map row, not the problem-framing one.
        specific = ["scope-map"]
    for t in specific + [t for t in toks if t not in specific]:
        for i, (_, names) in enumerate(table):
            if t in names:
                return i
    return None


def outside_parens(text):
    depth, out = 0, []
    for ch in text:
        depth += ch == "("
        if depth == 0:
            out.append(ch)
        depth -= ch == ")" and depth > 0
    return "".join(out)


def artifact_paths(entry):
    return re.findall(r"`([^`]+)`", outside_parens(entry["artifact"] or ""))


def escapes(path):
    """An Artifact path that is absolute or climbs out of the directory it is relative to."""
    return os.path.isabs(path) or re.match(r"^[A-Za-z]:", path) is not None or ".." in path.replace("\\", "/").split("/")


def check_format(text, entries, malformed, findings):
    if not text.strip():
        findings.append(("ERROR", "log", "the log is empty: no routing history at all"))
    elif not entries:
        findings.append(("ERROR", "log", "the log has content but no `## <n>. <title>` entry could be parsed"))
    for h in malformed:
        findings.append(("ERROR", "log", f"heading is not a numbered entry (`## <n>. <title>`): ## {h}"))
    for i, e in enumerate(entries):
        tag = f"entry {e['n']}"
        if e["n"] != i + 1:
            findings.append(("ERROR", tag, f"sequence number {e['n']} where {i + 1} was expected"))
        if e["routed_lines"] != 1:
            findings.append(("ERROR", tag, f"{e['routed_lines']} **Routed to:** lines, not one"))
        if e["artifact_lines"] != 1:
            findings.append(("ERROR", tag, f"{e['artifact_lines']} **Artifact:** lines, not one"))
        if not e["artifact"]:
            continue
        art = e["artifact"]
        if is_quarantine(e):
            if "see sub-entries below" not in art:
                findings.append(("ERROR", tag, "quarantine entry's Artifact isn't `see sub-entries below`"))
            continue
        bare = outside_parens(art)
        paths = re.findall(r"`([^`]+)`", bare)
        if len(paths) != 1:
            findings.append(("ERROR", tag, f"Artifact names {len(paths)} paths outside its parenthetical, not one: {art}"))
        elif paths[0].endswith(("/", "\\")):
            findings.append(("ERROR", tag, f"Artifact is a bare directory: {art}"))
        elif escapes(paths[0]):
            findings.append(("ERROR", tag, f"Artifact path is absolute or leaves the project: {art}"))
        if re.search(r"\b(if|otherwise|unless|or)\b", re.sub(r"`[^`]*`", "", bare)):
            findings.append(("ERROR", tag, f"Artifact is conditional or offers alternatives: {art}"))


def check_quarantine(entries, findings):
    for e in entries:
        if not is_quarantine(e):
            continue
        tag = f"entry {e['n']}"
        subs = e["subs"]
        if subs != sorted(subs) or len(set(subs)) != len(subs):
            findings.append(("ERROR", tag, f"sub-entries out of order or repeated: {', '.join(subs)}"))
        present = set(subs)
        if present:
            last = max(present)
            missing = [s for s in QUARANTINE_STEPS if s < last and s not in present]
            if missing:
                findings.append(("ERROR", tag, f"sub-entries {', '.join(missing)} missing before {last}"))
            if last != "E":
                findings.append(("WARN", tag, f"sub-entries stop at {last}: the flow stopped there, or the rest was never logged"))
        else:
            findings.append(("WARN", tag, "no A-E sub-entries yet (fine only if the flow stopped before A)"))
        a = re.search(r"^- \*\*A\..*$", e["body"], re.M)
        if a and not re.search(r"policy\s*[—-]+\s*`?(heavy|lite|compare)", a.group(0)):
            findings.append(("ERROR", tag, "A line doesn't open with the policy (heavy, lite or compare)"))


def check_order(entries, table, findings):
    prev = None
    for e in entries:
        tag = f"entry {e['n']}"
        rank = route_rank(e["routed"], table)
        if rank is None:
            findings.append(("ERROR", tag, f"routes to something not in the state table: {e['routed']}"))
            continue
        if rank == NONE:
            findings.append(("INFO", tag, "routed outside the spine (user-directed); not ranked"))
            continue
        key = stage_key(table[rank][1])
        backward = re.search(r"(?i)backward|supersed", e["heading"] + e["body"])
        if prev is None:
            if rank != 0:
                findings.append(("INFO", tag, f"log starts at `{key}`, not the first row (fine if earlier stages predate the plugin)"))
        elif rank > prev + 1:
            skipped = [stage_key(table[r][1]) for r in range(prev + 1, rank)]
            hard = [s for s in skipped if s not in SKIPPABLE | UI_ONLY]
            ui = [s for s in skipped if s in UI_ONLY]
            if hard:
                findings.append(("ERROR", tag, f"skips {', '.join(hard)} on the way to `{key}`"))
            if ui:
                findings.append(("WARN", tag, f"skips {', '.join(ui)}: right only if the slice isn't UI-touching (or the design system already exists)"))
        elif rank == prev:
            findings.append(("INFO", tag, f"`{key}` routed again (a correction, a \"not now\", or a re-run)"))
        elif rank < prev and not backward and not (key in RESTARTS and prev == len(table) - 1):
            findings.append(("ERROR", tag, f"goes back to `{key}` without saying it's a backward route or what it supersedes"))
        elif rank < prev and backward and not re.search(r"(?i)supersed", e["body"] + e["heading"]):
            findings.append(("WARN", tag, "backward route doesn't name the artifact it supersedes"))
        if not (backward and prev is not None and rank < prev):
            prev = rank  # a backward route is a detour: the unit's position stays where it was


def git(project, *args):
    r = subprocess.run(["git", "-C", project, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else None


def clean(text):
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).rstrip()


def check_git_append_only(project, log_rel, current, findings):
    commits = git(project, "log", "--reverse", "--format=%h", "--", log_rel)
    if commits is None:
        findings.append(("INFO", "git", "not a git repository; append-only checked from transcripts only"))
        return
    versions = [(c, git(project, "show", f"{c}:{log_rel.replace(os.sep, '/')}") or "") for c in commits.split()]
    versions.append(("working copy", current))
    for (a, old), (b, new) in zip(versions, versions[1:]):
        if not clean(new).startswith(clean(old)):
            findings.append(("ERROR", "git", f"log changed in place between {a} and {b}, not only appended to"))
    count = lambda t: len(parse_log(t)[0])
    uncommitted = count(current) - count(versions[-2][1]) if len(versions) > 1 else count(current)
    if uncommitted > 0:
        findings.append(("INFO", "git", f"{uncommitted} entr{'y' if uncommitted == 1 else 'ies'} not committed yet"))


def transcript_files(audit_dir, project):
    """Kept transcripts (and their subagents') whose session ran in this project or a directory under it."""
    out = []
    for path in glob.glob(os.path.join(audit_dir, "transcripts", "*.jsonl")):
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.search(r'"cwd"\s*:\s*"((?:[^"\\]|\\.)*)"', line)
                if m:
                    if inside(json.loads('"' + m.group(1) + '"'), project):
                        out.append(path)
                        out += glob.glob(os.path.join(path[:-6], "**", "*.jsonl"), recursive=True)
                    break
    return out


def session_of(path, paths):
    """The top-level transcript a file belongs to: itself, or the session whose directory holds it."""
    for p in paths:
        if p != path and inside(path, p[:-6]):
            return p
    return path


def tool_calls(paths):
    """Every tool_use across the transcripts, once each, in time order, with whether its result was an error."""
    seen, calls, errored = {}, [], set()
    for path in paths:
        session = session_of(path, paths)
        last_ts = ""
        for i, line in enumerate(open(path, encoding="utf-8", errors="replace")):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            last_ts = e.get("timestamp") or last_ts
            msg = e.get("message")
            content = msg.get("content") if isinstance(msg, dict) else None
            if not isinstance(content, list):
                continue
            for b in content:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_result":
                    if b.get("is_error") and b.get("tool_use_id"):
                        errored.add(b["tool_use_id"])
                    continue
                if b.get("type") != "tool_use":
                    continue
                key = b.get("id") or (path, i, b.get("name"))
                call = {"ts": last_ts, "name": b.get("name"), "input": b.get("input") or {},
                        "order": (path, i), "session": session, "id": b.get("id")}
                if key not in seen:
                    seen[key] = call
                    calls.append(call)
    for c in calls:
        c["error"] = c["id"] in errored
    calls.sort(key=lambda c: (c["ts"], c["order"]))
    return calls


SHELL_WRITE = (r"(?<![-=<>])(>>|>|\btee\s+(?:-a\s+)?|\bOut-File\s+(?:-FilePath\s+)?|\bAdd-Content\s+(?:-Path\s+)?"
               r"|\bSet-Content\s+(?:-Path\s+)?)\s*[\"']?([^\s\"'|;&<>()]+)")
PATHLIKE = re.compile(r"^[\w$~./\\:-]*[\w-]\.[A-Za-z0-9]+$")  # has a name and an extension
IN_PLACE = re.compile(r"\b(sed\s+-i|perl\s+-p?i)[^\n]*" + re.escape(LOG_NAME))
HEREDOC = re.compile(r"<<-?\s*[\"']?(\w+)[\"']?\s*\n.*?\n\1\s*$", re.S | re.M)


def shell_body(cmd):
    """The text a shell command appends, when it can be read from the command: a heredoc or a quoted echo."""
    m = re.search(r"<<-?\s*[\"']?(\w+)[\"']?\s*\n(.*?)\n\1\s*$", cmd, re.S | re.M)
    if m:
        return m.group(2)
    m = re.search(r"\b(?:echo|printf)\s+(['\"])(.*?)\1\s*>>", cmd, re.S)
    if m:
        return m.group(2)
    return None


def log_write(call, log_abs):
    """A call that writes the log, as a dict (kind, and what it changes), else None."""
    name, ti = call["name"], call["input"]
    if name in ("Write", "Edit") and norm(ti.get("file_path")) == norm(log_abs):
        if name == "Write":
            return {"kind": "Write", "content": ti.get("content", "")}
        return {"kind": "Edit", "old": ti.get("old_string", ""), "new": ti.get("new_string", "")}
    if name in ("Bash", "PowerShell") and LOG_NAME in (ti.get("command") or ""):
        cmd = ti["command"]
        target = None
        for m in re.finditer(SHELL_WRITE, HEREDOC.sub("", cmd)):
            if m.group(2).replace("\\", "/").endswith(LOG_NAME):
                target = m
                break
        if target is None:
            if IN_PLACE.search(cmd):
                return {"kind": name, "cmd": cmd, "append": False, "body": None}
            return None  # the log is read, listed or named, not written
        op = target.group(1)
        append = op.startswith(">>") or "tee -a" in op or "Add-Content" in op or re.search(r"-Append\b", cmd) is not None
        return {"kind": name, "cmd": cmd, "append": append, "body": shell_body(cmd) if append else None}
    return None


def called_skill(call):
    ti = call["input"]
    if call["name"] == "Skill":
        name = ti.get("skill")
    elif call["name"] in ("Agent", "Task"):
        name = ti.get("subagent_type")
    else:
        return None
    if not name or "kad-dev-team" not in name:
        return None
    parts = name.split(":")
    if len(parts) >= 3 and parts[-1] == "AGENT":
        # kad-dev-team:<persona>:AGENT names the persona; the task names the skill it runs
        # ("Invoke the skill `kad-dev-team:test-quality-review` first"), which is what the log routes to.
        for m in re.findall(r"kad-dev-team:([A-Za-z0-9_-]+)(?!:AGENT)", ti.get("prompt") or ""):
            if m != parts[-2] and m != "AGENT":
                return m
        return parts[-2]
    return parts[-1]


def written_paths(call, project):
    """Files a call writes: Write/Edit targets, and every shell redirect or file-writing cmdlet target."""
    ti = call["input"]
    if call["name"] in ("Write", "Edit", "NotebookEdit") and ti.get("file_path"):
        return [ti["file_path"]]
    if call["name"] in ("Bash", "PowerShell"):
        out = []
        for m in re.finditer(SHELL_WRITE, HEREDOC.sub("", ti.get("command") or "")):
            p = m.group(2)
            if p.startswith(("/dev/", "&", "#")) or p.lower() == "$null" or not PATHLIKE.match(p):
                continue
            out.append(p if os.path.isabs(p) else os.path.join(project, p))
        return out
    return []


def check_transcripts(project, log_abs, entries, table, calls, findings):
    spine = set().union(*(names for _, names in table))
    by_n = {e["n"]: e for e in entries}
    known_text = None      # the log's text as the transcripts last showed it, None when unknown
    log_written = False
    current = {}           # session -> the entry most recently written to the log in that session
    ran = {}               # entry number -> skill names called while it was current
    writes = {}            # entry number -> files written while it was current
    for call in calls:
        s = call["session"]
        w = log_write(call, log_abs)
        if w:
            if call["error"]:
                findings.append(("INFO", "transcript", f"{call['ts']}: a {w['kind']} to the log failed; not counted as written"))
                continue
            added = ""
            if w["kind"] == "Write":
                if known_text is not None and not clean(w["content"]).startswith(clean(known_text)):
                    findings.append(("ERROR", "transcript", f"{call['ts']}: Write replaced the log instead of appending to it"))
                added = w["content"][len(known_text):] if known_text is not None and w["content"].startswith(known_text) else w["content"]
                known_text = w["content"]
            elif w["kind"] == "Edit":
                old, new = w["old"], w["new"]
                if known_text is not None:
                    at_end = old != "" and clean(known_text).endswith(clean(old))
                    if not (at_end and new.startswith(old)):
                        findings.append(("ERROR", "transcript", f"{call['ts']}: Edit changed the log in place, not at its end"))
                    known_text = known_text.replace(old, new, 1) if old and old in known_text else None
                elif log_written and not new.startswith(old):
                    findings.append(("ERROR", "transcript", f"{call['ts']}: Edit to the log does more than append"))
                added = new[len(old):] if new.startswith(old) else new
            else:
                if not w["append"] and log_written:
                    findings.append(("ERROR", "transcript", f"{call['ts']}: {w['kind']} to the log does more than append"))
                added = w["body"] if w["body"] is not None else w["cmd"]
                known_text = (known_text + "\n" + w["body"]) if (known_text is not None and w["body"] is not None and w["append"]) else None
            log_written = True
            nums = [int(n) for n in re.findall(r"^## (\d+)\.", added, re.M)]
            if nums:
                current[s] = max(nums)
                ran.setdefault(current[s], [])
                writes.setdefault(current[s], [])
            continue
        skill = called_skill(call)
        if skill and skill in spine:
            cur = current.get(s)
            entry = by_n.get(cur)
            rank = route_rank(entry["routed"], table) if entry else None
            row = table[rank][1] if isinstance(rank, int) else set()
            named = row | set(routed_names(entry["routed"]) if entry else [])
            if is_quarantine(entry) and skill.endswith("-review"):
                named.add(skill)  # the quarantine flow's own reviewers, accessibility-review among them
            primary = stage_key(row) if row else None
            if entry is None:
                findings.append(("ERROR", "transcript", f"{call['ts']}: `{skill}` called with no log entry written before it in this session"))
            elif skill not in named:
                findings.append(("ERROR", "transcript", f"{call['ts']}: `{skill}` called while the latest entry ({cur}) routes to {entry['routed']}: a stage that ran unlogged"))
            elif skill == primary and primary in ran[cur] and not (is_quarantine(entry) and skill in IMPLEMENTERS):
                findings.append(("ERROR", "transcript", f"{call['ts']}: `{skill}` called again under entry {cur} with no new entry written: a stage that ran unlogged"))
            else:
                ran[cur].append(skill)
            continue
        cur = current.get(s)
        if cur is not None:
            for path in written_paths(call, project):
                if norm(os.path.abspath(path)) != norm(log_abs):
                    writes[cur].append((path, call["name"] == "Edit"))
    for e in entries:
        if e["n"] in ran and not ran[e["n"]]:
            findings.append(("WARN", f"entry {e['n']}", f"no call to the routed skill follows it ({e['routed']}): routed but never run, or run in a session not kept"))
        elif e["n"] not in ran:
            findings.append(("INFO", f"entry {e['n']}", "not written in any kept transcript (written by hand or in an unrecorded session)"))
    return writes


def rel(path, project):
    return os.path.relpath(path, project).replace(os.sep, "/")


def check_artifacts(project, log_dir, entries, writes, findings):
    for e in entries:
        art = e["artifact"]
        if not art or is_quarantine(e):
            continue
        tag = f"entry {e['n']}"
        paths = [p for p in artifact_paths(e) if not escapes(p)]  # escaping paths are format errors, never probed
        made = {rel(p, project) for p, edit in writes.get(e["n"], []) if not edit and inside(p, project)}
        edited = {rel(p, project) for p, edit in writes.get(e["n"], []) if edit and inside(p, project)} - made
        exists = [p for p in paths if not p.endswith(("/", "\\"))
                  and any(inside(c, project) and os.path.exists(c) for c in (os.path.join(log_dir, p), os.path.join(project, p)))]
        if exists:
            continue
        if made or edited:
            md = sorted(p for p in made if p.endswith(".md")) or sorted(made)
            level = "INFO" if len(paths) == 1 and "(" in art else "WARN"
            saved = f"wrote {', '.join(md[:4])}{' …' if len(md) > 4 else ''}" if md else "wrote nothing new"
            also = f"; edited {', '.join(sorted(edited))}" if edited else ""
            findings.append((level, tag, f"{saved}{also} (logged: {art})"))
        elif len(paths) == 1 and not paths[0].endswith(("/", "\\")):
            findings.append(("WARN", tag, f"`{paths[0]}` doesn't exist and no kept transcript shows what was written instead"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--log", help="path to the log, relative to the project (default: found under it)")
    ap.add_argument("--skill", default=DEFAULT_SKILL, help="the orchestrator SKILL.md whose rules to check against")
    ap.add_argument("--audit-dir", default=os.environ.get("KAD_AUDIT_DIR", os.path.expanduser("~/.claude/kad-audit")))
    ap.add_argument("--transcript", action="append", default=[], help="a transcript to read (repeatable); overrides --audit-dir")
    ap.add_argument("--no-transcripts", action="store_true")
    a = ap.parse_args()

    project = os.path.abspath(a.project)
    if a.log:
        log_rel = a.log
    else:
        found = [p for p in glob.glob(os.path.join(project, "**", LOG_NAME), recursive=True) if "node_modules" not in p]
        if len(found) != 1:
            raise SystemExit(f"found {len(found)} {LOG_NAME} files under {project}; pass --log")
        log_rel = os.path.relpath(found[0], project)
    log_abs = os.path.join(project, log_rel)
    if not inside(log_abs, project):
        raise SystemExit(f"--log must point inside the project: {log_rel}")
    text = open(log_abs, encoding="utf-8").read()
    table = load_table(a.skill)
    entries, malformed = parse_log(text)

    findings = []
    check_format(text, entries, malformed, findings)
    check_quarantine(entries, findings)
    check_order(entries, table, findings)
    check_git_append_only(project, log_rel, text, findings)
    writes, paths = {}, []
    if not a.no_transcripts:
        paths = a.transcript or transcript_files(a.audit_dir, project)
        if paths:
            writes = check_transcripts(project, log_abs, entries, table, tool_calls(paths), findings)
        else:
            findings.append(("INFO", "transcript", f"no kept transcript for this project under {a.audit_dir}"))
    check_artifacts(project, os.path.dirname(log_abs), entries, writes, findings)

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    counts = {k: sum(f[0] == k for f in findings) for k in order}
    print(f"# Orchestrator log check: `{safe(log_rel)}`\n")
    print(f"- Project: `{safe(project)}`")
    print(f"- Rules: `{os.path.normpath(a.skill)}` ({len(table)} table rows)")
    print(f"- Entries: {len(entries)}; transcripts read: {sum(p.endswith('.jsonl') for p in paths)}")
    print(f"- Findings: {counts['ERROR']} error, {counts['WARN']} warn, {counts['INFO']} info\n")

    def where(f):
        m = re.match(r"entry (\d+)", f[1])
        return (order[f[0]], int(m.group(1)) if m else -1)
    for level, tag, msg in sorted(findings, key=where):
        print(f"- **{level}** {safe(tag)}: {safe(msg)}")
    raise SystemExit(1 if counts["ERROR"] else 0)


if __name__ == "__main__":
    main()
