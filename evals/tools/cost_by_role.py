"""What a chunk-loop run cost, by role class, from the session transcripts.

The orchestrator's E step runs this once, inline, and puts the last line
on the E line: `cost $<n>` or `cost not measured: <why>`. The figure is an
estimate from list prices over the token counts Claude Code records on
every assistant message; it is not a bill.

Transcripts come from one of three places, the first that yields any:
- `--transcript <session.jsonl>` (repeatable): a session and, next to it,
  its `<session>/subagents/agent-*.jsonl` with their `.meta.json`;
- `--project <root>` with audit mode on (`hooks/audit.sh`): every
  transcript under `<audit dir>/transcripts/` whose session ran in that
  project, with its subagents;
- `--project <root>` with `--projects-dir` (default `~/.claude/projects`):
  the project's own transcript directory, the one Claude Code writes to
  (`C--Users-...-app/` for `C:\\Users\\...\\app`), for a run that audit
  mode did not keep.

Each assistant message is counted once by its id (a resumed or forked
session repeats earlier ones). Role classes come from the subagent's launch
description, as the orchestrator words them: builder/planner, fixer,
reviewer (combined chunk review, one of the slice reviewers, or the
comments pass), smoke, consult, triage; the session itself is the
orchestrator. Prices are per million tokens for input, output, cache read
and cache write; `--price model=in,out,read,write` adds or overrides one.
A model with no price is counted at the most expensive known price and
named in the output, so the total is never silently low.

Usage: python3 -I evals/tools/cost_by_role.py --project <root> [--audit-dir DIR] [--projects-dir DIR]
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
ROLE_RULES = [
    (re.compile(r"\b(smoke|stranger test)\b", re.I), "smoke"),
    (re.compile(r"\b(triage|external review)\b", re.I), "triage"),
    (re.compile(r"\b(fix|fixer)\b", re.I), "fixer"),
    (re.compile(r"\b(plan slice|chunk plan|planner|replan)\b", re.I), "builder/planner"),
    (re.compile(r"^build\b|\bbuild chunk\b|\bimplement\b", re.I), "builder/planner"),
    (re.compile(r"\b(why-comments|comments? (pass|review))\b", re.I), "reviewer:comments"),
    (re.compile(r"\b(combined|chunk) review\b|\breview chunk\b", re.I), "reviewer:chunk"),
    (re.compile(r"\baccessibility review\b|\ba11y\b", re.I), "reviewer:accessibility"),
    (re.compile(r"\btest[- ]quality\b", re.I), "reviewer:test-quality"),
    (re.compile(r"\barchitecture review\b", re.I), "reviewer:architecture"),
    (re.compile(r"\bsecurity review\b", re.I), "reviewer:security"),
    (re.compile(r"\breliability review\b", re.I), "reviewer:reliability"),
    (re.compile(r"\bcode review\b", re.I), "reviewer:code"),
    (re.compile(r"\b(consult|decision|decide)\b", re.I), "consult"),
]


def role_of(description):
    for rule, role in ROLE_RULES:
        if rule.search(description or ""):
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
    """(path, description) for every subagent transcript kept next to a session."""
    out = []
    for path in sorted(glob.glob(os.path.join(session[:-6], "subagents", "agent-*.jsonl"))):
        meta = path[:-6] + ".meta.json"
        description = ""
        if os.path.isfile(meta):
            try:
                description = json.load(open(meta, encoding="utf-8")).get("description", "")
            except ValueError:
                pass
        out.append((path, description))
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


def project_sessions(projects_dir, project):
    """The project's own transcript directory under ~/.claude/projects."""
    key = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(project))
    folder = os.path.join(projects_dir, key)
    return sorted(glob.glob(os.path.join(folder, "*.jsonl"))) if os.path.isdir(folder) else []


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser()
    p.add_argument("--project")
    p.add_argument("--audit-dir", default=os.environ.get("KAD_AUDIT_DIR", os.path.expanduser("~/.claude/kad-audit")))
    p.add_argument("--projects-dir", default=os.path.expanduser("~/.claude/projects"))
    p.add_argument("--transcript", action="append", default=[])
    p.add_argument("--price", action="append", default=[], help="model=in,out,read,write ($/M)")
    p.add_argument("--json")
    a = p.parse_args()
    for spec in a.price:
        model, _, nums = spec.partition("=")
        PRICES[model] = tuple(float(x) for x in nums.split(","))

    sessions = list(a.transcript)
    source = "--transcript"
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
        for path, description in subagents_of(session):
            rows.append((name, role_of(description), description, usage_of(path, seen)))

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
            json.dump({"sessions": sessions, "total": round(total, 2), "unknown_models": unknown,
                       "rows": [dict(session=n, role=r, description=d, **u) for n, r, d, u in rows]}, f, indent=2)
    print(f"cost ${total:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
