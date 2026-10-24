"""Check a real project's orchestrator-log.md against the orchestrator's rules.

Reads the log in a project that used kad-dev-team, and (when given) the
transcripts audit mode kept for it, and prints a markdown report of:

- format: sequence numbers in order with no gaps, every `## ` heading a
  numbered entry, exactly one Routed to and one Artifact line in every
  entry, the Artifact one path inside the project (no bare directory, no
  "if"/"otherwise"/"or" outside a parenthetical), the implementation
  entry (routed to the chunk loop, or to the quarantine flow in logs
  written before 0.6.0) with its A-E sub-entries in order;
- the chunk loop's own lines: the A line opens with the sandbox result and
  names the policy, branch and base; one C line per chunk, numbered in
  order and agreeing with B's count, each with commit hashes, a gate
  result, the three reviewers that always run, a round 0 and one segment
  per fix round (`r<i> fix <sha> → C/H/M/L (reg r, pre p)`), ending in
  `clean r<i>` with a clean last round or `cap:` after five rounds; the
  D and E lines the same way; and, when the A line's reviews directory
  holds a `rounds-slice-<nnn>.jsonl` sidecar, its rounds per chunk against
  the log's. One INFO per entry sums the rounds and the regression share,
  the number the fix-rounds rule is to be judged on;
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
  call to its routed skill (the implementation entry by any number of
  implementer, reviewer, map, delivery and triage launches), and every
  entry was followed by its routed skill.

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
           [--no-transcripts] [--sidecar path/to/rounds-slice-001.jsonl]
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
LOOP_STEPS = "ABCDE"
# The persona that implements; its launches under the implementation entry are many.
IMPLEMENTERS = {"tdd-implementation", "tdd-implementation-lite", "tdd-coach"}
# Skills the chunk loop calls under its one entry besides the implementers and the `*-review` skills.
LOOP_SKILLS = {"map-update", "map-query", "pr-writeup", "delivery", "ci-pipeline", "external-review-triage"}
REVIEWERS = {"tq": "test-quality", "co": "code", "ar": "architecture", "se": "security", "re": "reliability", "ac": "accessibility"}
ALWAYS = {"tq", "co", "ar"}
CAP = 5
SHA = r"[0-9a-f]{7,40}"
COUNTS = r"(\d+)/(\d+)/(\d+)/(\d+)"
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


def is_loop(entry):
    """The implementation entry: routed to the chunk loop (0.6.0+) or the quarantine flow before it."""
    low = (entry["routed"] or "").lower() if entry else ""
    return "chunk loop" in low or "quarantine" in low


def is_chunk_loop(entry):
    return bool(entry and entry["routed"] and "chunk loop" in entry["routed"].lower())


is_quarantine = is_loop  # the name the 0.5.0 checks used


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
    if "quarantine" in low or "chunk loop" in low:
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
        if is_loop(e):
            if "see sub-entries below" not in art:
                findings.append(("ERROR", tag, "implementation entry's Artifact isn't `see sub-entries below`"))
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


def rounds_of(text):
    """The fix-round segments on a C, D or E line: [(round, sha, (C, H, M, L), reg, pre)]; reg/pre None when absent."""
    out = []
    for m in re.finditer(r"\br(\d+) fix\s+`?(" + SHA + r")`?\s*(?:→|->)\s*`?" + COUNTS + r"`?(?:\s*\(reg\s+`?(\d+)`?,\s*pre\s+`?(\d+)`?\))?", text):
        out.append((int(m.group(1)), m.group(2), tuple(int(m.group(i)) for i in range(3, 7)),
                    int(m.group(7)) if m.group(7) else None, int(m.group(8)) if m.group(8) else None))
    return out


def round0_of(text):
    m = re.search(r"\br0\s+`?" + COUNTS + r"`?", text)
    return tuple(int(m.group(i)) for i in range(1, 5)) if m else None


def check_rounds(tag, what, text, findings):
    """Round 0, the fix rounds and the ending on one line. Returns (rounds, regressions, pre-existing, cap hit)."""
    r0 = round0_of(text)
    rounds = rounds_of(text)
    if r0 is None:
        findings.append(("ERROR", tag, f"{what}: no `r0 C/H/M/L` round-0 counts"))
    nums = [r[0] for r in rounds]
    if nums != list(range(1, len(nums) + 1)):
        findings.append(("ERROR", tag, f"{what}: fix rounds are not r1, r2, … in order: {', '.join('r%d' % n for n in nums) or 'none'}"))
    if nums and max(nums) > CAP:
        findings.append(("ERROR", tag, f"{what}: r{max(nums)} is past the cap of {CAP} rounds"))
    reg = pre = 0
    for n, _, counts, r, p in rounds:
        if r is None:
            findings.append(("WARN", tag, f"{what}: r{n} has no regression/pre-existing split"))
        else:
            reg, pre = reg + r, pre + p
            if r + p != sum(counts[:3]):
                findings.append(("WARN", tag, f"{what}: r{n} splits {r} + {p} but counts {sum(counts[:3])} Critical, High and Medium"))
    ending = re.search(r"\b(clean r(\d+)|cap:)", text)
    cap = False
    if ending is None:
        if r0 is not None and not re.search(r"gate\s+`?FAIL|stall:\s*`?ended", text):
            findings.append(("ERROR", tag, f"{what}: doesn't say how the rounds ended (`clean r<i>` or `cap: <standing>`)"))
    elif ending.group(1).startswith("clean"):
        i = int(ending.group(2))
        last = rounds[-1][2] if rounds else r0
        if i != (nums[-1] if nums else 0):
            findings.append(("ERROR", tag, f"{what}: says clean r{i} but the last round logged is r{nums[-1] if nums else 0}"))
        elif last and sum(last[:3]) != 0:
            findings.append(("ERROR", tag, f"{what}: says clean r{i} but that round logged {last[0]}/{last[1]}/{last[2]} Critical/High/Medium"))
    else:
        cap = True
        if (nums[-1] if nums else 0) != CAP:
            findings.append(("ERROR", tag, f"{what}: says cap but only {nums[-1] if nums else 0} fix rounds are logged, not {CAP}"))
    return len(rounds), reg, pre, cap


def reviewers_of(text):
    m = re.search(r"reviewers\s+`?([a-z][a-z ]*)`?", text)
    return m.group(1).split() if m else None


def check_chunk_loop(e, findings):
    """The chunk loop's A, B, C, D and E lines. Returns the sidecar path named on the A line, if any."""
    tag, body = f"entry {e['n']}", e["body"]
    a = re.search(r"^- \*\*A\. Start:\*\*(.*)$", body, re.M)
    sidecar = None
    steps = set(e["subs"])
    if a:
        text = a.group(1)
        sb = re.search(r"sandbox\s*[—-]+\s*`?(PASS|none on|FAIL)", text)
        if not sb:
            findings.append(("ERROR", tag, "A line doesn't open with the sandbox result (PASS, none on <platform>, or FAIL)"))
        elif sb.group(1) == "FAIL" and steps - {"A"}:
            findings.append(("ERROR", tag, f"A line says the sandbox check failed, yet the flow went on to {', '.join(sorted(steps - {'A'}))}"))
        elif sb.group(1) == "none on":
            findings.append(("INFO", tag, "ran unsandboxed on a platform without a sandbox, by the owner's logged choice"))
        if not re.search(r"policy\s*[—-]+\s*`?(heavy|lite)\b", text):
            findings.append(("ERROR", tag, "A line doesn't name the policy (heavy or lite)"))
        for part in ("branch", "base"):
            if not re.search(part + r"\s*[—-]+\s*`?\S", text):
                findings.append(("WARN", tag, f"A line has no {part}"))
        m = re.search(r"reviews\s*[—-]+\s*`([^`]+)`", text)
        sidecar = m.group(1) if m else None
    b = re.search(r"^- \*\*B\. Plan:\*\*\s*`?(\d+)`? chunks", body, re.M)
    planned = int(b.group(1)) if b else None
    if "B" in steps and planned is None:
        findings.append(("ERROR", tag, "B line doesn't open with the chunk count (`<k>` chunks)"))
    c_lines = re.findall(r"^- \*\*C\. Chunk (\d+)/(\d+):\*\*(.*)$", body, re.M)
    if "C" in steps and not c_lines:
        findings.append(("ERROR", tag, "C lines are not in the `C. Chunk <k>/<n>:` form"))
    ks = [int(k) for k, _, _ in c_lines]
    if ks != list(range(1, len(ks) + 1)):
        findings.append(("ERROR", tag, f"C lines are not chunk 1, 2, … in order: {', '.join(map(str, ks))}"))
    ns = {int(n) for _, n, _ in c_lines}
    if len(ns) > 1:
        findings.append(("ERROR", tag, f"C lines disagree on the chunk count: {', '.join(map(str, sorted(ns)))}"))
    elif ns and planned is not None and ns != {planned}:
        findings.append(("ERROR", tag, f"C lines say {ns.pop()} chunks, B planned {planned}"))
    total_rounds = reg = pre = caps = 0
    chunks_logged = {}
    for k, n, text in c_lines:
        what = f"C chunk {k}"
        if not re.search(r"commits\s+`?" + SHA, text):
            findings.append(("ERROR", tag, f"{what}: no commit hash"))
        gate = re.search(r"gate\s+`?(PASS|FAIL)", text)
        if not gate:
            findings.append(("ERROR", tag, f"{what}: no gate result"))
        elif gate.group(1) == "FAIL":
            findings.append(("INFO", tag, f"{what}: ended at the gate"))
            continue
        revs = reviewers_of(text)
        if revs is None:
            findings.append(("ERROR", tag, f"{what}: no reviewers"))
        else:
            unknown = [r for r in revs if r not in REVIEWERS]
            if unknown:
                findings.append(("ERROR", tag, f"{what}: unknown reviewer initials {', '.join(unknown)} (known: {', '.join(REVIEWERS)})"))
            missing = sorted(ALWAYS - set(revs))
            if missing:
                findings.append(("ERROR", tag, f"{what}: {', '.join(missing)} always run on a chunk and are missing"))
        r, g, p, cap = check_rounds(tag, what, text, findings)
        total_rounds, reg, pre, caps = total_rounds + r, reg + g, pre + p, caps + cap
        chunks_logged[int(k)] = r
        if re.search(r"stall:\s*`?(relaunched|ended)", text):
            findings.append(("INFO", tag, f"{what}: stall ({re.search(r'stall:\s*`?(relaunched|ended)', text).group(1)})"))
    d = re.search(r"^- \*\*D\. Slice review:\*\*(.*)$", body, re.M)
    if d:
        text = d.group(1)
        if not re.search(r"map\s+`[^`]+`", text):
            findings.append(("WARN", tag, "D line names no map path"))
        revs = reviewers_of(text)
        if revs is None:
            findings.append(("ERROR", tag, "D line: no reviewers"))
        elif len(set(revs) & set(REVIEWERS)) < 5:
            findings.append(("WARN", tag, f"D line: {len(revs)} reviewers; the slice review runs five, six for a UI slice"))
        r, g, p, cap = check_rounds(tag, "D", text, findings)
        total_rounds, reg, pre, caps = total_rounds + r, reg + g, pre + p, caps + cap
    ev = re.search(r"^- \*\*E\. Delivery:\*\*(.*)$", body, re.M)
    if ev:
        text = ev.group(1)
        if not re.search(r"PR\s+`?#?\d+", text):
            findings.append(("WARN", tag, "E line names no pull request number"))
        if not re.search(r"pushed\s+`?" + SHA, text):
            findings.append(("WARN", tag, "E line names no pushed commit"))
        if not re.search(r"audit\s+`?(" + SHA + r"|not configured|none)", text):
            findings.append(("WARN", tag, "E line doesn't say what the audit sync did (a commit, `not configured` or `none`)"))
        ext = [int(m.group(1)) for m in re.finditer(r"\bext r(\d+)\s+`?\d+`?c:", text)]
        if ext != list(range(1, len(ext) + 1)):
            findings.append(("ERROR", tag, f"E line: external rounds are not r1, r2, … in order: {', '.join('r%d' % n for n in ext)}"))
        if ext and max(ext) > CAP:
            findings.append(("ERROR", tag, f"E line: ext r{max(ext)} is past the cap of {CAP} rounds"))
        if ext and not re.search(r"\b(clean r\d+|cap:)", text):
            findings.append(("ERROR", tag, "E line: external rounds don't say how they ended (`clean r<i>` or `cap: <open>`)"))
        total_rounds += len(ext)
    if c_lines or d:
        findings.append(("INFO", tag, f"{len(c_lines)} chunk{'s' if len(c_lines) != 1 else ''} logged, {total_rounds} fix round{'s' if total_rounds != 1 else ''} "
                         f"({reg} regression{'s' if reg != 1 else ''}, {pre} pre-existing), {caps} cap hit{'s' if caps != 1 else ''}"))
    return sidecar, chunks_logged


def check_sidecar(project, log_dir, e, sidecar_path, chunks_logged, findings):
    """The rounds-slice sidecar against the log's C lines: a chunk with m fix rounds has findings in rounds 0..m-1."""
    tag = f"entry {e['n']}"
    candidates = []
    if sidecar_path:
        if os.path.isfile(sidecar_path):
            candidates = [sidecar_path]
        else:
            d = sidecar_path if os.path.isabs(sidecar_path) else None
            for base in [d] if d else [os.path.join(log_dir, sidecar_path), os.path.join(project, sidecar_path)]:
                if base and os.path.isdir(base):
                    candidates = sorted(glob.glob(os.path.join(base, "rounds-slice-*.jsonl")))
                    break
    if not candidates:
        if sidecar_path and chunks_logged:
            findings.append(("INFO", tag, f"no rounds sidecar found at {sidecar_path} (the reviews directory may be on another machine)"))
        return
    by_chunk = {}
    bad = 0
    for path in candidates:
        for line in open(path, encoding="utf-8", errors="replace"):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                k, i, sev = rec["chunk"], int(rec["round"]), str(rec.get("severity", ""))
            except (ValueError, KeyError, TypeError):
                bad += 1
                continue
            if sev[:1].upper() in "CHM":
                by_chunk.setdefault(k, set()).add(i)
    if bad:
        findings.append(("WARN", tag, f"sidecar: {bad} line{'s' if bad != 1 else ''} not a rounds record"))
    for k, m in sorted(chunks_logged.items()):
        have = by_chunk.get(k, set())
        need = set(range(m))
        if m and not need <= have:
            findings.append(("WARN", tag, f"sidecar: chunk {k} logs {m} fix round{'s' if m != 1 else ''} but has Critical/High/Medium records only for rounds {sorted(have) or 'none'}"))
        if not m and have:
            findings.append(("WARN", tag, f"sidecar: chunk {k} logs no fix round but has Critical/High/Medium records in rounds {sorted(have)}"))
    extra = sorted(k for k in by_chunk if isinstance(k, int) and k not in chunks_logged)
    if extra:
        findings.append(("WARN", tag, f"sidecar: records for chunks {', '.join(map(str, extra))} that have no C line"))


def check_loop(entries, findings, project=None, log_dir=None, sidecar_arg=None):
    for e in entries:
        if not is_loop(e):
            continue
        tag = f"entry {e['n']}"
        subs = e["subs"]
        chunk_loop = is_chunk_loop(e)
        if subs != sorted(subs):
            findings.append(("ERROR", tag, f"sub-entries out of order: {', '.join(subs)}"))
        repeated = sorted({s for s in subs if subs.count(s) > 1 and not (chunk_loop and s == "C")})
        if repeated:
            findings.append(("ERROR", tag, f"sub-entries repeated: {', '.join(repeated)}"))
        present = set(subs)
        if present:
            last = max(present)
            missing = [s for s in LOOP_STEPS if s < last and s not in present]
            if missing:
                findings.append(("ERROR", tag, f"sub-entries {', '.join(missing)} missing before {last}"))
            if last != "E":
                findings.append(("WARN", tag, f"sub-entries stop at {last}: the flow stopped there, or the rest was never logged"))
        else:
            findings.append(("WARN", tag, "no A-E sub-entries yet (fine only if the flow stopped before A)"))
        if chunk_loop:
            sidecar, chunks_logged = check_chunk_loop(e, findings)
            if project is not None:
                check_sidecar(project, log_dir, e, sidecar_arg or sidecar, chunks_logged, findings)
            continue
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
            if is_loop(entry) and (skill.endswith("-review") or skill in LOOP_SKILLS):
                named.add(skill)  # the loop's own reviewers, map, delivery and triage calls
            primary = stage_key(row) if row else None
            if entry is None:
                findings.append(("ERROR", "transcript", f"{call['ts']}: `{skill}` called with no log entry written before it in this session"))
            elif skill not in named:
                findings.append(("ERROR", "transcript", f"{call['ts']}: `{skill}` called while the latest entry ({cur}) routes to {entry['routed']}: a stage that ran unlogged"))
            elif skill == primary and primary in ran[cur] and not (is_loop(entry) and skill in IMPLEMENTERS):
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
        if not art or is_loop(e):
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
    ap.add_argument("--sidecar", help="the chunk loop's rounds-slice-<nnn>.jsonl (default: found in the A line's reviews directory)")
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
    check_loop(entries, findings, project, os.path.dirname(log_abs), a.sidecar)
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
