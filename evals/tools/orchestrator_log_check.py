"""Check a real project's orchestrator-log.md against the orchestrator's rules.

Reads the log in a project that used kad-dev-team, and (when given) the
transcripts audit mode kept for it, and prints a markdown report of:

- format: sequence numbers in order with no gaps, a Routed to and an
  Artifact line in every entry, the Artifact one path (no bare directory,
  no "if"/"otherwise"/"or" outside a parenthetical), quarantine entries
  with their A-E sub-entries in order;
- artifacts: each entry's path exists, or else which files the transcripts
  show that stage writing instead;
- order: each route against the state table in skills/orchestrator/SKILL.md
  (read from the file, so the table and this check can't drift apart): a
  stage skipped that the table never skips, or a step backwards that
  doesn't say it's a backward route;
- append-only: every committed version of the log, and the working copy,
  starts with the one before it; with transcripts, every write to the log
  (Write, Edit, or a Bash redirect) only adds to it;
- log vs. calls (transcripts only): every spine skill called has an entry
  written before it, and every entry was followed by its routed skill.

Read-only; nothing in the project is changed. Findings are marked ERROR
(the rule is broken), WARN (worth reading) or INFO. Check a session
against the rules of the plugin version that ran it: pass that version's
SKILL.md with --skill (gitCommitSha in ~/.claude/plugins/installed_plugins.json).
--skill only sets the state table: the Artifact-line rules are the current
ones, so a log written under 0.4.0, which predates them, fails them as
expected.

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


def norm(path):
    return os.path.normcase(os.path.normpath(path)) if path else ""


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
            names |= {"tdd-implementation-lite", "tdd-coach"}
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
    entries = []
    for m in re.finditer(r"^## (\d+)\.\s*(.*)$", text, re.M):
        end = text.find("\n## ", m.end())
        body = text[m.end(): end if end != -1 else len(text)]
        routed = re.search(r"^\*\*Routed to:\*\*\s*(.+)$", body, re.M)
        artifact = re.search(r"^\*\*Artifact:\*\*\s*(.+)$", body, re.M)
        subs = re.findall(r"^- \*\*([A-E])\.", body, re.M)
        entries.append({
            "n": int(m.group(1)), "heading": m.group(2).strip(), "body": body,
            "routed": routed.group(1).strip() if routed else None,
            "artifact": artifact.group(1).strip() if artifact else None, "subs": subs,
        })
    return entries


def route_rank(routed, table):
    """Index of the table row an entry routed to, or None if it names nothing in the table."""
    if routed and "quarantine" in routed.lower():
        return next(i for i, (_, names) in enumerate(table) if "tdd-implementation" in names)
    toks = {t.split(":")[-1].strip() for t in re.findall(r"`([^`]+)`", routed or "")}
    toks |= {t.split(":")[0].strip() for t in re.findall(r"`([^`]+)`", routed or "")}
    best = None
    for i, (_, names) in enumerate(table):
        hit = toks & names
        # docs-writer appears in several rows; prefer a row named by its skill.
        if hit and (best is None or any("-" in h and h != "docs-writer" for h in hit)):
            best = i
            if any("-" in h and h != "docs-writer" for h in hit):
                break
    return best


def outside_parens(text):
    depth, out = 0, []
    for ch in text:
        depth += ch == "("
        if depth == 0:
            out.append(ch)
        depth -= ch == ")" and depth > 0
    return "".join(out)


def check_format(entries, findings):
    for i, e in enumerate(entries):
        tag = f"entry {e['n']}"
        if e["n"] != i + 1:
            findings.append(("ERROR", tag, f"sequence number {e['n']} where {i + 1} was expected"))
        if not e["routed"]:
            findings.append(("ERROR", tag, "no **Routed to:** line"))
        if not e["artifact"]:
            findings.append(("ERROR", tag, "no **Artifact:** line"))
            continue
        quarantine = e["routed"] and "quarantine" in e["routed"].lower()
        art = e["artifact"]
        if quarantine:
            if "see sub-entries below" not in art:
                findings.append(("ERROR", tag, "quarantine entry's Artifact isn't `see sub-entries below`"))
            continue
        bare = outside_parens(art)
        paths = re.findall(r"`([^`]+)`", bare)
        if len(paths) != 1:
            findings.append(("ERROR", tag, f"Artifact names {len(paths)} paths outside its parenthetical, not one: {art}"))
        elif paths[0].endswith(("/", "\\")):
            findings.append(("ERROR", tag, f"Artifact is a bare directory: {art}"))
        if re.search(r"\b(if|otherwise|unless|or)\b", re.sub(r"`[^`]*`", "", bare)):
            findings.append(("ERROR", tag, f"Artifact is conditional or offers alternatives: {art}"))


def check_quarantine(entries, findings):
    for e in entries:
        if not (e["routed"] and "quarantine" in e["routed"].lower()):
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
        prev = rank


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
    uncommitted = len(parse_log(current)) - len(parse_log(versions[-2][1])) if len(versions) > 1 else len(parse_log(current))
    if uncommitted > 0:
        findings.append(("INFO", "git", f"{uncommitted} entr{'y' if uncommitted == 1 else 'ies'} not committed yet"))


def transcript_files(audit_dir, project):
    """Kept transcripts (and their subagents') whose session ran in this project."""
    out = []
    for path in glob.glob(os.path.join(audit_dir, "transcripts", "*.jsonl")):
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.search(r'"cwd"\s*:\s*"((?:[^"\\]|\\.)*)"', line)
                if m:
                    if norm(json.loads('"' + m.group(1) + '"')) == norm(project):
                        out.append(path)
                        out += glob.glob(os.path.join(path[:-6], "**", "*.jsonl"), recursive=True)
                    break
    return out


def tool_calls(paths):
    """Every tool_use across the transcripts, once each, in time order."""
    seen, calls = {}, []
    for path in paths:
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
                if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                    continue
                key = b.get("id") or (path, i, b.get("name"))
                call = {"ts": last_ts, "name": b.get("name"), "input": b.get("input") or {},
                        "order": (path, i)}
                if key not in seen:
                    seen[key] = call
                    calls.append(call)
    calls.sort(key=lambda c: (c["ts"], c["order"]))
    return calls


def log_write(call, log_abs):
    """(kind, added text, ok-to-append) for a call that writes the log, else None."""
    name, ti = call["name"], call["input"]
    if name in ("Write", "Edit") and norm(ti.get("file_path")) == norm(log_abs):
        if name == "Write":
            return ("Write", ti.get("content", ""), None)
        old, new = ti.get("old_string", ""), ti.get("new_string", "")
        return ("Edit", new[len(old):] if new.startswith(old) else new, new.startswith(old))
    if name in ("Bash", "PowerShell") and LOG_NAME in (ti.get("command") or ""):
        cmd = ti["command"]
        if not re.search(r"(>>?|Out-File|Add-Content|Set-Content|tee)[^\n]*" + re.escape(LOG_NAME), cmd):
            return None
        appends = re.search(r"(>>|Add-Content|tee -a|-Append)[^\n]*" + re.escape(LOG_NAME), cmd)
        return (name, cmd, bool(appends))
    return None


def called_skill(call):
    ti = call["input"]
    name = ti.get("skill") if call["name"] == "Skill" else ti.get("subagent_type") if call["name"] in ("Agent", "Task") else None
    if not name or "kad-dev-team" not in name:
        return None
    return name.split(":")[-1]


def written_path(call, project):
    ti = call["input"]
    if call["name"] in ("Write", "Edit", "NotebookEdit") and ti.get("file_path"):
        return ti["file_path"]
    if call["name"] in ("Bash", "PowerShell"):
        m = re.search(r"(?:cat|tee)\s*>\s*['\"]?([^\s'\"<]+)", ti.get("command") or "")
        if m:
            return os.path.join(project, m.group(1))
    return None


def check_transcripts(project, log_abs, entries, table, calls, findings):
    spine = set().union(*(names for _, names in table))
    known_text = None
    log_written = False
    current = None  # the entry most recently written to the log
    ran = {}        # entry number -> skill names called while it was current
    writes = {}     # entry number -> files written while it was current
    for call in calls:
        w = log_write(call, log_abs)
        if w:
            kind, added, ok = w
            if kind == "Write" and known_text is not None and not clean(added).startswith(clean(known_text)):
                findings.append(("ERROR", "transcript", f"{call['ts']}: Write replaced the log instead of appending to it"))
            elif ok is False and log_written:
                findings.append(("ERROR", "transcript", f"{call['ts']}: {kind} to the log does more than append"))
            if kind == "Write":
                known_text = added
            log_written = True
            nums = [int(n) for n in re.findall(r"^## (\d+)\.", added, re.M)]
            if nums:
                current = max(nums)
                ran.setdefault(current, [])
                writes.setdefault(current, [])
            continue
        skill = called_skill(call)
        if skill and skill in spine:
            entry = next((e for e in entries if e["n"] == current), None)
            rank = route_rank(entry["routed"], table) if entry else None
            if entry is None:
                findings.append(("ERROR", "transcript", f"{call['ts']}: `{skill}` called with no log entry written before it"))
            elif rank is None or skill not in table[rank][1]:
                findings.append(("ERROR", "transcript", f"{call['ts']}: `{skill}` called while the latest entry ({current}) routes to {entry['routed']}: a stage that ran unlogged"))
            else:
                ran[current].append(skill)
            continue
        path = written_path(call, project)
        if path and current is not None and norm(path) != norm(log_abs):
            writes[current].append((path, call["name"] == "Edit"))
    for e in entries:
        if e["n"] in ran and not ran[e["n"]]:
            findings.append(("WARN", f"entry {e['n']}", f"no call to the routed skill follows it ({e['routed']}): routed but never run, or run in a session not kept"))
        elif e["n"] not in ran:
            findings.append(("INFO", f"entry {e['n']}", "not written in any kept transcript (written by hand or in an unrecorded session)"))
    return writes


def rel(path, project):
    return os.path.relpath(path, project).replace(os.sep, "/")


def check_artifacts(project, entries, writes, findings):
    for e in entries:
        art = e["artifact"]
        if not art or (e["routed"] and "quarantine" in e["routed"].lower()):
            continue
        tag = f"entry {e['n']}"
        paths = re.findall(r"`([^`]+)`", outside_parens(art))
        made = {rel(p, project) for p, edit in writes.get(e["n"], []) if not edit and norm(p).startswith(norm(project))}
        edited = {rel(p, project) for p, edit in writes.get(e["n"], []) if edit and norm(p).startswith(norm(project))} - made
        exists = [p for p in paths if not p.endswith(("/", "\\")) and os.path.exists(os.path.join(project, p))]
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
    text = open(log_abs, encoding="utf-8").read()
    table = load_table(a.skill)
    entries = parse_log(text)

    findings = []
    check_format(entries, findings)
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
    check_artifacts(project, entries, writes, findings)

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    counts = {k: sum(f[0] == k for f in findings) for k in order}
    print(f"# Orchestrator log check: `{log_rel}`\n")
    print(f"- Project: `{project}`")
    print(f"- Rules: `{os.path.normpath(a.skill)}` ({len(table)} table rows)")
    print(f"- Entries: {len(entries)}; transcripts read: {sum(p.endswith('.jsonl') for p in paths)}")
    print(f"- Findings: {counts['ERROR']} error, {counts['WARN']} warn, {counts['INFO']} info\n")

    def where(f):
        m = re.match(r"entry (\d+)", f[1])
        return (order[f[0]], int(m.group(1)) if m else -1)
    for level, tag, msg in sorted(findings, key=where):
        print(f"- **{level}** {tag}: {msg}")
    raise SystemExit(1 if counts["ERROR"] else 0)


if __name__ == "__main__":
    main()
