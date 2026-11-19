"""What a chunk-loop run cost, by role class, from the session transcripts.

The orchestrator's E step runs this once, inline, and puts the last line
on the E line: `cost $<n>` or `cost not measured: <why>`. The figure is an
estimate from list prices over the token counts Claude Code records on
every assistant message; it is not a bill.

Which sessions a total must cover is decided by id, never by whatever
transcripts happen to be on disk: `--log <orchestrator-log.md>` (every
session the log's last chunk loop names: its `A. Start` line's `session`
field and each `Resumed … session <id>` bullet after it, so a session
that ended before it recorded a round still counts, and an earlier
slice's loop in the same log does not), `--sidecar <rounds-slice-nnn.jsonl>`
(every distinct `session` its rows name) and `--session <id>` (repeatable;
the E step passes its own, `CLAUDE_CODE_SESSION_ID`). A `--log` or
`--sidecar` that cannot be read, or a sidecar line that is not JSON, is
`cost not measured` too: a list of ids that may be short is no list. For
each id the transcript is looked for
under `--projects-dir` (default `~/.claude/projects`, the project's own
directory, the one Claude Code writes to: `C--Users-...-app/` for
`C:\\Users\\...\\app`), then under `<audit dir>/transcripts/` (the
snapshots `hooks/audit.sh` keeps), with `<session>/subagents/` next to
it. **A total says what it does not cover.** A session the log or the
sidecar names whose transcript is nowhere (Claude Code saved none for it,
or it is another machine's) is skipped and named: the rest is totalled
and the last line reads `cost $<n>, not covering <id> (no transcript)`,
so one lost session of an old entry does not hide the cost of every
other. A session passed with `--session` is the caller's own and stays
required: without its transcript, or with none found for any id, the
output ends with `cost not measured: transcript missing for <id>`. Run
3's loop session had 79 subagent transcripts on disk and no main one; the
planning session's figure went on the E line as if it were the run's.

Without any id, `--transcript <session.jsonl>` (repeatable) names the
sessions outright; failing that, `--project <root>` takes every kept
transcript whose session ran in the project, then the project's own
directory, and says the sessions were chosen by directory, not by id.

Each assistant message is counted once by its id (a resumed or forked
session repeats earlier ones). Role classes come from the subagent's launch
description, as the orchestrator words them, by its opening verb first
(Build, Plan, Fix, Apply, Review chunk, Re-review chunk, Smoke, Stranger,
Walk, Decide, Triage, Run), then by the review names in it (the six slice
reviewers and their re-reviews, the comments pass, the cold review), then
by the agent type (`agentType` in the meta file): builder/planner, fixer,
runner (the chunk runner), reviewer:chunk, reviewer:<name>, smoke, walk,
consult, triage; the session itself is the orchestrator. "fix" counts only
at the start of the description. Prices are per million tokens for input, output, cache read
and cache write; `--price model=in,out,read,write` adds or overrides one.
A model with no price is counted at the most expensive known price and
named in the output, so the total is never silently low.

Usage: python3 -I evals/tools/cost_by_role.py --project <root> [--log orchestrator-log.md] [--sidecar rounds.jsonl] [--session ID ...]
                                            [--audit-dir DIR] [--projects-dir DIR]
                                            [--transcript s.jsonl ...] [--price model=in,out,read,write ...]
                                            [--json out.json]
"""
import argparse
import collections
import glob
import json
import os
import re
import sys

PRICES = {  # $ per million tokens: input, output, cache read, cache write (1.25x input)
    "claude-opus-5-5": (4.0, 20.0, 0.20, 5.0),
    "claude-sonnet-5-5": (2.0, 10.0, 0.20, 2.5),
    "claude-haiku-5-5": (0.8, 4.0, 0.08, 1.0),
}
# Classes come from the launch description's opening verb first, then from
# the words in it, then from the agent type; "fix" counts only at the start
# ("Re-review slice 002 chunk 4 fixes" is a re-review, not a fixer). Slice
# 2's first table counted the eleven re-reviews as fixers and the eight
# chunk reviews as "other" on the old word-anywhere rules.
def named_review(name, more=""):
    """`<name> review`, `<name> re-review`, and the form the slice review's
    launches take, `review: <name>` and `re-review: <name>` ("Slice 4
    review: security"): without the second, eight slice reviewers of one
    slice fell through to their agent type and were totalled as consults."""
    return re.compile(rf"\b{name} (?:review|re-review)\b|\b(?:review|re-review):\s*{name}\b{more}", re.I)


VERB_RULES = [
    (re.compile(r"^(?:run|chunk[- ]runner|run chunk)\b", re.I), "runner"),
    (re.compile(r"^(?:build|implement|plan|replan|write the chunk plan)\b", re.I), "builder/planner"),
    (re.compile(r"^(?:fix|apply|patch|repair)\b", re.I), "fixer"),
    (re.compile(r"^(?:smoke|smoke-run|stranger)\b", re.I), "smoke"),
    (re.compile(r"^(?:walk|ac walk|criteria walk)\b", re.I), "walk"),
    (re.compile(r"^(?:triage)\b", re.I), "triage"),
    (re.compile(r"^(?:decide|decision|consult)\b", re.I), "consult"),
    (re.compile(r"^(?:review|re-review)\b.*\bchunk\b|^re-review\b", re.I), "reviewer:chunk"),
    (re.compile(r"^(?:cold)\b", re.I), "reviewer:cold"),
]
WORD_RULES = [
    (re.compile(r"\b(?:smoke|stranger test)\b", re.I), "smoke"),
    (re.compile(r"\b(?:criteria walk|ac walk)\b", re.I), "walk"),
    (re.compile(r"\b(?:triage|external review)\b", re.I), "triage"),
    (re.compile(r"\b(?:chunk runner|runs? chunk)\b", re.I), "runner"),
    (re.compile(r"\b(?:why-comments|comments?[- ]only|comments? (?:pass|review))\b", re.I), "reviewer:comments"),
    (re.compile(r"\b(?:combined|chunk) review\b|\breview chunk\b|\bre-review\b.*\bchunk\b", re.I), "reviewer:chunk"),
    (re.compile(r"\bcold (?:read|review)\b", re.I), "reviewer:cold"),
    (named_review("accessibility", r"|\ba11y\b"), "reviewer:accessibility"),
    (re.compile(r"\btest[- ]quality\b", re.I), "reviewer:test-quality"),
    (named_review("architecture"), "reviewer:architecture"),
    (named_review("security"), "reviewer:security"),
    (named_review("reliability"), "reviewer:reliability"),
    (named_review("code"), "reviewer:code"),
    # "Slice 4 second fixer (regressions)", "Gate fixer: lint error", and
    # the delivery step's capture fixer ("Add slice 4 screen captures").
    (re.compile(r"\bfixer\b|\bscreen captures?\b", re.I), "fixer"),
    (re.compile(r"\b(?:plan slice|chunk plan|planner|replan|build chunk)\b", re.I), "builder/planner"),
    (re.compile(r"\b(?:decision|decide|consult|criterion)\b", re.I), "consult"),
]
# What an agent type is for when the description decides nothing.
TYPE_RULES = [
    ("chunk-runner", "runner"),
    ("code-reviewer", "reviewer:code"),
    ("tdd-coach", "builder/planner"),
    ("software-architect", "consult"),
    ("devsecops-engineer", "consult"),
    ("ux-designer", "consult"),
    ("accessibility-engineer", "consult"),
    ("product-slicer", "consult"),
    ("product-manager", "consult"),
    ("docs-writer", "consult"),
]


def role_of(description, agent_type=""):
    text = (description or "").strip()
    for rule, role in VERB_RULES:
        if rule.search(text):
            return role
    for rule, role in WORD_RULES:
        if rule.search(text):
            return role
    for key, role in TYPE_RULES:
        if key in (agent_type or ""):
            return role
    return "other"


def usage_of(path, seen):
    """Token counts and estimated cost of one transcript, messages not yet in `seen` only."""
    totals = dict(msgs=0, inp=0, out=0, read=0, write=0, cost=0.0)
    models = collections.Counter()
    first = last = None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            ts = row.get("timestamp")
            if ts:
                first = first or ts
                last = ts
            if row.get("type") != "assistant":
                continue
            message = row.get("message") or {}
            usage = message.get("usage") or {}
            mid = message.get("id")
            if not usage or not mid or mid in seen:
                continue
            seen.add(mid)
            model = message.get("model") or "?"
            if model == "<synthetic>":  # Claude Code's own placeholder turns carry no billed tokens
                continue
            models[model] += 1
            inp = usage.get("input_tokens", 0)
            out = usage.get("output_tokens", 0)
            read = usage.get("cache_read_input_tokens", 0)
            write = usage.get("cache_creation_input_tokens", 0)
            price = PRICES.get(model) or max(PRICES.values())
            totals["msgs"] += 1
            totals["inp"] += inp
            totals["out"] += out
            totals["read"] += read
            totals["write"] += write
            totals["cost"] += (inp * price[0] + out * price[1] + read * price[2] + write * price[3]) / 1e6
    totals["models"] = dict(models)
    totals["first"], totals["last"] = first, last
    return totals


def subagents_of(session):
    """(path, description, agent type) for every subagent transcript kept next to a session."""
    out = []
    for path in sorted(glob.glob(os.path.join(session[:-6], "subagents", "agent-*.jsonl"))):
        meta = path[:-6] + ".meta.json"
        description, agent_type = "", ""
        if os.path.isfile(meta):
            try:
                m = json.load(open(meta, encoding="utf-8"))
                description, agent_type = m.get("description", ""), m.get("agentType", "") or m.get("subagent_type", "")
            except ValueError:
                pass
        out.append((path, description, agent_type))
    return out


def inside(path, root):
    path = os.path.normcase(os.path.abspath(path))
    root = os.path.normcase(os.path.abspath(root))
    return path == root or path.startswith(root.rstrip("\\/") + os.sep) or path.startswith(root.rstrip("\\/") + "/")


def audit_sessions(audit_dir, project):
    """Kept transcripts whose session ran in the project (the checker's rule)."""
    out = []
    for path in sorted(glob.glob(os.path.join(audit_dir, "transcripts", "*.jsonl"))):
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.search(r'"cwd"\s*:\s*"((?:[^"\\]|\\.)*)"', line)
                if m:
                    if inside(json.loads('"' + m.group(1) + '"'), project):
                        out.append(path)
                    break
    return out


def project_folder(projects_dir, project):
    key = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(project))
    return os.path.join(projects_dir, key)


def project_sessions(projects_dir, project):
    """The project's own transcript directory under ~/.claude/projects."""
    folder = project_folder(projects_dir, project)
    return sorted(glob.glob(os.path.join(folder, "*.jsonl"))) if os.path.isdir(folder) else []


class UnreadableInput(Exception):
    pass


def sidecar_sessions(path):
    """The distinct session ids the sidecar's rows name, in first-seen order.
    Rows from before the field existed name none and are passed over (the
    log names their sessions); a line that is not JSON is an error."""
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    sid = json.loads(line).get("session")
                except ValueError:
                    raise UnreadableInput(f"sidecar line {n} is not JSON: {path}")
                if sid and sid not in out:
                    out.append(sid)
    except OSError as e:
        raise UnreadableInput(f"sidecar unreadable: {path} ({e.strerror})")
    return out


UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
LOG_SESSION = re.compile(r"\bsession\b[\s—\-:]*`?(" + UUID + r")`?", re.I)


A_LINE = re.compile(r"^\s*- \*\*A\. Start:\*\*", re.M)


def log_sessions(path):
    """The session ids of the log's **last** chunk loop: the last
    `A. Start` line's `session` field and every `Resumed … session <id>`
    bullet after it. A log holds every slice's loop, and the E step wants
    the cost of the one it is closing: read whole, slice 3's E line said
    $422.10 for a run that cost $105.94. A log with no A line is read
    whole."""
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError as e:
        raise UnreadableInput(f"orchestrator log unreadable: {path} ({e.strerror})")
    starts = [m.start() for m in A_LINE.finditer(text)]
    if starts:
        text = text[starts[-1]:]
    out = []
    for m in LOG_SESSION.finditer(text):
        sid = m.group(1).lower()
        if sid not in out:
            out.append(sid)
    return out


def transcript_for(sid, projects_dir, project, audit_dir):
    """The session's transcript: the live one under the project's directory first, else the audit snapshot."""
    candidates = []
    if project:
        candidates.append(os.path.join(project_folder(projects_dir, project), f"{sid}.jsonl"))
    candidates.append(os.path.join(audit_dir, "transcripts", f"{sid}.jsonl"))
    for c in candidates:
        if os.path.isfile(c):
            return c, candidates
    return None, candidates


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser()
    p.add_argument("--project")
    p.add_argument("--audit-dir", default=os.environ.get("KAD_AUDIT_DIR", os.path.expanduser("~/.claude/kad-audit")))
    p.add_argument("--projects-dir", default=os.path.expanduser("~/.claude/projects"))
    p.add_argument("--transcript", action="append", default=[])
    p.add_argument("--session", action="append", default=[], help="a session id the total must cover (repeatable)")
    p.add_argument("--sidecar", help="rounds-slice-<nnn>.jsonl: every session its rows name must be covered")
    p.add_argument("--log", help="orchestrator-log.md: every session its chunk-loop entry names must be covered")
    p.add_argument("--price", action="append", default=[], help="model=in,out,read,write ($/M)")
    p.add_argument("--json")
    a = p.parse_args()
    for spec in a.price:
        model, _, nums = spec.partition("=")
        PRICES[model] = tuple(float(x) for x in nums.split(","))

    required = list(a.session)
    try:
        named = (log_sessions(a.log) if a.log else []) + (sidecar_sessions(a.sidecar) if a.sidecar else [])
    except UnreadableInput as e:
        print(f"cost not measured: {e}")
        return 0
    for sid in named:
        if sid not in required:
            required.append(sid)
    sessions = list(a.transcript)
    source = "--transcript"
    skipped = []
    if required:
        sessions, missing = [], []
        for sid in required:
            found, looked = transcript_for(sid, a.projects_dir, a.project, a.audit_dir)
            if found:
                sessions.append(found)
            else:
                missing.append((sid, looked))
        for sid, looked in missing:
            print(f"transcript missing for {sid}: looked at {', '.join(looked)}")
        # A named session with no transcript is skipped and said so on the
        # last line; the caller's own (`--session`), or nothing found at
        # all, is no total.
        owed = [sid for sid, _ in missing if sid in a.session] or ([] if sessions else [sid for sid, _ in missing])
        if owed:
            print(f"cost not measured: transcript missing for {', '.join(owed)}")
            return 0
        skipped = [sid for sid, _ in missing]
        source = f"{len(required)} session id(s) from " + ", ".join(x for x in ("--log" if a.log else "", "--sidecar" if a.sidecar else "", "--session" if a.session else "") if x)
    if not sessions and a.project:
        sessions = audit_sessions(a.audit_dir, a.project)
        source = f"audit mode ({a.audit_dir})"
    if not sessions and a.project:
        sessions = project_sessions(a.projects_dir, a.project)
        source = f"the project's transcripts ({a.projects_dir})"
    if not sessions:
        why = "no transcript given" if not a.project else f"no transcript for {a.project} under {a.audit_dir} or {a.projects_dir} (audit mode off?)"
        print(f"cost not measured: {why}")
        return 0

    seen = set()
    rows = []
    for session in sessions:
        name = os.path.basename(session)[:8]
        rows.append((name, "orchestrator", "the session", usage_of(session, seen)))
        for path, description, agent_type in subagents_of(session):
            rows.append((name, role_of(description, agent_type), description, usage_of(path, seen)))

    by_role = collections.OrderedDict()
    for name, role, _, u in rows:
        key = (name, role)
        agg = by_role.setdefault(key, dict(n=0, msgs=0, out=0, read=0, write=0, cost=0.0, models=collections.Counter()))
        agg["n"] += 1
        for k in ("msgs", "out", "read", "write", "cost"):
            agg[k] += u[k]
        agg["models"].update(u["models"])

    unknown = sorted({m for _, _, _, u in rows for m in u["models"] if m not in PRICES})
    print(f"Sessions: {len(sessions)} ({source}); agents: {len(rows) - len(sessions)}; assistant messages counted once by id.")
    if not required:
        print("The sessions were chosen by directory, not by id: pass --log, --sidecar or --session for a total that is known to cover the run.")
    print()
    print("| session | role class | agents | msgs | output tok | cache read (M) | cache write (M) | est. $ | models |")
    print("|---|---|---|---|---|---|---|---|---|")
    total = 0.0
    per_session = collections.defaultdict(float)
    for (name, role), agg in sorted(by_role.items()):
        models = ", ".join(f"{m}:{n}" for m, n in sorted(agg["models"].items()))
        print(f"| {name} | {role} | {agg['n']} | {agg['msgs']} | {agg['out']:,} | {agg['read'] / 1e6:.1f} | {agg['write'] / 1e6:.2f} | {agg['cost']:.2f} | {models} |")
        total += agg["cost"]
        per_session[name] += agg["cost"]
    print()
    print("Per session: " + "; ".join(f"{k} ${v:.2f}" for k, v in sorted(per_session.items())))
    if unknown:
        print(f"Models with no price, counted at the highest known price: {', '.join(unknown)} (add --price model=in,out,read,write)")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"sessions": sessions, "total": round(total, 2), "not_covered": skipped, "unknown_models": unknown,
                       "rows": [dict(session=n, role=r, description=d, **u) for n, r, d, u in rows]}, f, indent=2)
    print(f"cost ${total:.2f}" + (f", not covering {', '.join(skipped)} (no transcript)" if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
