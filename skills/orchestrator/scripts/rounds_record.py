"""Review and smoke reports into the fix-round sidecar, and the counts for the log line.

The chunk loop's reviewers write findings to files and hand back counts;
the orchestrator never parses a report itself. This script is the one path
from those files to the two records the audit reads: the sidecar
`rounds-slice-<nnn>.jsonl` (one JSON object per finding, every round of
every chunk, the slice review as chunk `D`, the external review as `pr`)
and the C-line fragment the orchestrator appends to its log entry. It
exists because the first real run had the orchestrator write three such
scripts on the fly and twice misfile a fixer's lines.

The shared finding format every review skill states, and the only one
parsed here:

    ### <short title>

    **Severity:** Critical | High | Medium | Low | needs-decision (<persona>)
    **Location:** <path>:<line>
    **Category:** <category>

A finding is a `###` or `####` heading (or an older `## Finding: <title>`
heading) followed, before the next heading of any level, by a
`**Severity:**` line. A heading with no Severity line under it (`###
Summary`, `### What's working`, an entry under "Pre-existing, not
blocking" that carries none) is not a finding. The severity's first word
names one of the four levels, case-insensitive, trailing text ignored
(`High (pre-existing)` is High); `needs-decision (<persona>)` is the fifth
value, kept as severity `needs-decision` with the persona in its own
field, for the orchestrator's gap step. The location is the first
`path:line`, `path:line-line` or bare `path` token on the Location line,
backticks stripped; a finding whose location names no file (a test name,
say) keeps `file` and `line` null. The title is the heading text without
a `Finding:` prefix.

Each finding becomes one sidecar row:

    {"chunk": 3, "round": 1, "reviewer": "review", "severity": "Medium",
     "persona": null, "title": "...", "file": "src/x.ts", "line": 12,
     "class": "regression" | "pre-existing" | "owed" | null, "fix": "<sha>" | null,
     "fixer": "<agent id>" | null, "turns": n | null,
     "report": "chunk-3-r1-review.md", "session": "<the session that recorded it>"}

`chunk` is an int when numeric (`D` and `pr` stay strings); `reviewer` is
the report filename's last `-` segment (`chunk-3-r1-review.md` -> review,
`chunk-3-r0-smoke.md` -> smoke, `slice-r0-test-quality.md` ->
test-quality) unless `--reviewer` says otherwise; `report` is the report's
path relative to the sidecar's directory when it lies under it, else as
given. Re-running for the same reports replaces their rows and leaves
every other row byte for byte: a corrected report never duplicates.

`class`, the regression rule, only with `--range <before>..<after>` (the
fix's commits; `--project` is the repository, default `.`): `git diff
<range> -U0` names, per file, the new-side line ranges of every hunk
(`@@ -a,b +c,d @@` is lines c..c+d-1; d=0 is the single line c). A
Critical, High or Medium whose file and line (or line range) fall inside a
hunk is a `regression`; one whose file is in the diff but that names no
line is a regression too (the file was touched); any other is
`pre-existing`: the re-review found it in lines the fix did not write, so
it stands and is never fixed in this scope. A smoke report's findings are
always regressions when a range is given: a smoke failure never stands.
Without `--range` (round 0) `class` is null, with one exception: a
finding titled "browser checks not run" (a UI smoke agent with no browser
to drive, naming what it could not check) is `owed` in any round. It is
never a fixer's (no fix makes a browser appear), it is left out of the
counts and the smoke count, it is printed as an `owed:` line, and it
stands like a pre-existing finding: `--standing` lists it, so it reaches
the pull request body and its issue as the owner's checklist.

`session` is the session that ran this script (`--session`, else
`CLAUDE_CODE_SESSION_ID`, else null): `cost_by_role.py` reads the distinct
ids from the sidecar to know which transcripts a cost total must cover.

Printed last, exactly, for the C line:

    r<i> <C>/<H>/<M>[ nd <n>][ (reg <r>, pre <p>)][; smoke PASS | ; smoke <n> findings][; L <n>][; owed <n>]

`nd` appears only when a finding needs a decision; the regression split
only with `--range`, counted over Critical, High and Medium; the smoke
part only when a smoke report was among the inputs (PASS is a smoke report
with no finding); `L` only when a Low was parsed (the slice review at D: a chunk report's
Lows are dropped before anything is recorded, with one `lows dropped <n>`
line); `owed` only when a "browser checks not run" finding was parsed.
Before that line, one `needs-decision: <persona> — <title> (<file>:<line>)`
per such finding and, with `--range`, one `standing: <severity> — <title>
(<file>:<line>)` per pre-existing Critical, High or Medium.

`--standing [--chunk <k>]` reads the sidecar instead and lists every
pre-existing Critical, High and Medium, grouped by chunk then severity, so
the orchestrator sees what is carried without opening a report:

    chunk <k> r<i> <severity> — <title> (<file>:<line>) [<reviewer>]
    ...
    standing <C>/<H>/<M>

Exit 0 after any parsed report, a report with no finding included. Exit 1
when a report file is missing; when a report holds finding-shaped blocks
(a Location, a What's happening or a Suggested fix under a heading) and
not one Severity line anywhere; or when a smoke report yields no finding
and its `## Result` is missing or does not start with `PASS`: the format
error is printed as `format: ... <path>` and nothing is written for that
file, so a report the parser cannot read never counts as clean. A list
marker before `**Severity:**` or `**Location:**` is tolerated.

Usage: python3 -I ${CLAUDE_SKILL_DIR}/scripts/rounds_record.py --sidecar <path>
           --report <path> [--report <path> ...] [--reviewer NAME ...]
           --chunk <k|D|pr> --round <i>
           [--project <root> --range <before>..<after>]
           [--fix <sha>] [--fixer <agent id>] [--turns <n>] [--json <out>]
       python3 -I .../rounds_record.py --sidecar <path> --standing [--chunk <k>]
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HEADING = re.compile(r"^(#{2,4})\s+(.+?)\s*#*\s*$")
# A leading list marker is tolerated: the first real smoke agent wrote
# `- **Severity:** Critical` and the count silently read as PASS.
SEVERITY = re.compile(r"^\s*(?:[-*]\s+)?\*\*Severity:?\*\*:?\s*(.+?)\s*$", re.I)
LOCATION = re.compile(r"^\s*(?:[-*]\s+)?\*\*Location:?\*\*:?\s*(.+?)\s*$", re.I)
FINDING_SHAPED = re.compile(r"^\s*(?:[-*]\s+)?\*\*(Location|What's happening|Suggested fix|Category):?\*\*", re.I)
RESULT_PASS = re.compile(r"^PASS\b", re.I)
NEEDS_DECISION = re.compile(r"needs[- ]decision(?:\s*\(\s*`?([^)`]+?)`?\s*\))?", re.I)
LEVELS = {"critical": "Critical", "high": "High", "medium": "Medium", "low": "Low"}
ACTIONABLE = ("Critical", "High", "Medium")
OWED = re.compile(r"^\s*browser checks not run\b", re.I)
PATH_TOKEN = re.compile(r"`?((?:[\w.@+-]+/)*[\w@+-]+(?:\.[\w-]+)+)`?(?::(\d+)(?:\s*[-–]\s*(?:L?)(\d+))?)?")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def read_lines(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def parse_severity(text):
    m = NEEDS_DECISION.search(text)
    if m:
        return "needs-decision", (m.group(1) or "").strip() or None
    first = re.sub(r"[^A-Za-z-]", " ", text).split()
    level = LEVELS.get(first[0].lower()) if first else None
    return level, None


def parse_location(text):
    m = PATH_TOKEN.search(text)
    if not m:
        return None, None, None
    path = m.group(1).replace("\\", "/")
    if path.startswith("./"):
        path = path[2:]
    line = int(m.group(2)) if m.group(2) else None
    end = int(m.group(3)) if m.group(3) else line
    return path, line, end


def parse_report(path):
    """(findings, finding_shaped_blocks, result): each finding is a dict with
    title, severity, persona, file, line, line_end; the second value says
    whether any heading's block looked like a finding, for the format check;
    the third is the first non-blank line under a `## Result` heading, or
    None when the report has none."""
    lines = read_lines(path)
    headings = [(i, len(m.group(1)), m.group(2)) for i, l in enumerate(lines) for m in [HEADING.match(l)] if m]
    findings, shaped, result = [], False, None
    for n, (start, _level, title) in enumerate(headings):
        end = headings[n + 1][0] if n + 1 < len(headings) else len(lines)
        block = lines[start + 1:end]
        if result is None and title.strip().lower() == "result":
            result = next((l.strip() for l in block if l.strip()), "")
        severity_line = next((SEVERITY.match(l) for l in block if SEVERITY.match(l)), None)
        if severity_line is None:
            shaped = shaped or any(FINDING_SHAPED.match(l) for l in block)
            continue
        severity, persona = parse_severity(severity_line.group(1))
        clean_title = re.sub(r"^(?:finding\s*:\s*)", "", title.strip().strip("*`"), flags=re.I).strip().strip("*`")
        if severity is None:
            print(f'warning: unrecognised severity "{severity_line.group(1)}" under "{clean_title}" in {path}')
            continue
        location_line = next((LOCATION.match(l) for l in block if LOCATION.match(l)), None)
        file, line, line_end = parse_location(location_line.group(1)) if location_line else (None, None, None)
        findings.append({"title": clean_title, "severity": severity, "persona": persona,
                         "file": file, "line": line, "line_end": line_end})
    return findings, shaped, result


def reviewer_of(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    return stem.rsplit("-", 1)[-1] if "-" in stem else stem


_GIT = None


def find_git():
    """The first git that answers `--version`: whatever PATH holds, then the
    Homebrew and MacPorts paths. macOS's /usr/bin/git is Apple's xcrun
    shim, which fails inside a sandbox that cannot read the developer
    directory; the candidates are tried by running them, not by stat,
    since such a sandbox may deny the stat and still allow the exec."""
    global _GIT
    if _GIT is None:
        for c in (shutil.which("git") or "git", "/opt/homebrew/bin/git", "/usr/local/bin/git", "/opt/local/bin/git"):
            try:
                if subprocess.run([c, "--version"], capture_output=True, timeout=15).returncode == 0:
                    _GIT = c
                    break
            except (OSError, subprocess.TimeoutExpired):
                continue
        _GIT = _GIT or "git"
    return _GIT


def hunks(project, rng):
    """{file: [(first, last), ...]} of new-side lines the range's diff wrote."""
    git = find_git()
    proc = subprocess.run([git, "diff", rng, "-U0", "--no-color"], cwd=project, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise SystemExit(f"git diff {rng}: {proc.stderr.strip()}")
    out, current = {}, None
    for line in proc.stdout.splitlines():
        if line.startswith("+++ "):
            target = line[4:].strip()
            current = None if target == "/dev/null" else target[2:] if target.startswith("b/") else target
            if current is not None:
                out.setdefault(current, [])
        elif current is not None:
            m = HUNK.match(line)
            if m:
                first, count = int(m.group(1)), int(m.group(2)) if m.group(2) is not None else 1
                out[current].append((first, first + max(count, 1) - 1))
    return out


def classify(finding, reviewer, changed):
    if OWED.match(finding["title"] or ""):
        return "owed"
    if changed is None:
        return None
    if reviewer == "smoke":
        return "regression"
    if finding["file"] is None or finding["file"] not in changed:
        return "pre-existing"
    if finding["line"] is None:
        return "regression"
    lo, hi = finding["line"], finding["line_end"] or finding["line"]
    return "regression" if any(a <= hi and lo <= b for a, b in changed[finding["file"]]) else "pre-existing"


def chunk_value(text):
    return int(text) if text.isdigit() else text


def report_key(report, sidecar):
    base = os.path.dirname(os.path.abspath(sidecar))
    full = os.path.abspath(report)
    rel = os.path.relpath(full, base)
    key = rel if not rel.startswith("..") else report
    return key.replace("\\", "/")


def where(row):
    if not row.get("file"):
        return "no location"
    return f"{row['file']}:{row['line']}" if row.get("line") is not None else row["file"]


def load_sidecar(path):
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [l for l in f.read().splitlines() if l.strip()]


def row_of(raw):
    try:
        return json.loads(raw)
    except ValueError:
        return None


def record(a):
    reviewers = list(a.reviewer or [])
    reports = []
    for n, report in enumerate(a.report):
        reports.append((report, reviewers[n] if n < len(reviewers) else reviewer_of(report)))
    missing = [r for r, _ in reports if not os.path.isfile(r)]
    for r in missing:
        print(f"missing: {r}")
    if missing:
        return 1

    changed = hunks(a.project, a.range) if a.range else None
    rows, failed, smoke_seen = [], False, False
    for report, reviewer in reports:
        findings, shaped, result = parse_report(report)
        if isinstance(chunk_value(a.chunk), int):
            # A chunk review raises no Low (the slice review at D collects
            # them once): one that slipped through is dropped, and said.
            lows = [f for f in findings if f["severity"] == "Low"]
            if lows:
                findings = [f for f in findings if f["severity"] != "Low"]
                print(f"lows dropped {len(lows)} from {os.path.basename(report)}")
        if not findings and shaped:
            print(f"format: no finding in the shared format in {report}")
            failed = True
            continue
        if reviewer == "smoke" and not findings:
            # A smoke report with no parsed finding counts as PASS only when
            # it says so: anything else is a finding the parser did not see.
            if result is None:
                print(f"format: no `## Result` in the smoke report {report}")
                failed = True
                continue
            if not RESULT_PASS.match(result.strip("*`_ ")):
                print(f"format: smoke result is not PASS and no finding parsed in {report}: {result[:80]}")
                failed = True
                continue
        smoke_seen = smoke_seen or reviewer == "smoke"
        key = report_key(report, a.sidecar)
        for f in findings:
            rows.append({"chunk": chunk_value(a.chunk), "round": a.round, "reviewer": reviewer,
                         "severity": f["severity"], "persona": f["persona"], "title": f["title"],
                         "file": f["file"], "line": f["line"],
                         "class": classify(f, reviewer, changed),
                         "fix": a.fix, "fixer": a.fixer, "turns": a.turns, "report": key,
                         "session": a.session or None})

    keys = {report_key(r, a.sidecar) for r, _ in reports}
    kept = [raw for raw in load_sidecar(a.sidecar) if not ((row_of(raw) or {}).get("report") in keys)]
    os.makedirs(os.path.dirname(os.path.abspath(a.sidecar)), exist_ok=True)
    # Written whole to a temporary name, then renamed: a run that stops
    # halfway leaves the previous sidecar, never a prefix of the new one.
    tmp = a.sidecar + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        for raw in kept:
            f.write(raw + "\n")
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(tmp, a.sidecar)

    owed = [r for r in rows if r["class"] == "owed"]
    counted = [r for r in rows if r["class"] != "owed"]
    counts = {s: sum(1 for r in counted if r["severity"] == s) for s in ("Critical", "High", "Medium", "Low", "needs-decision")}
    actionable = [r for r in counted if r["severity"] in ACTIONABLE]
    regressions = sum(1 for r in actionable if r["class"] == "regression")
    standing = [r for r in actionable if r["class"] == "pre-existing"]
    smoke_findings = sum(1 for r in counted if r["reviewer"] == "smoke")

    for r in rows:
        if r["severity"] == "needs-decision":
            print(f"needs-decision: {r['persona'] or 'persona not named'} — {r['title']} ({where(r)})")
    for r in standing:
        print(f"standing: {r['severity']} — {r['title']} ({where(r)})")
    for r in owed:
        print(f"owed: {r['severity']} — {r['title']} ({where(r)}); stands, never handed to a fixer")

    line = f"r{a.round} {counts['Critical']}/{counts['High']}/{counts['Medium']}"
    if counts["needs-decision"]:
        line += f" nd {counts['needs-decision']}"
    if changed is not None:
        line += f" (reg {regressions}, pre {len(standing)})"
    if smoke_seen:
        smoke_owed = any(r["reviewer"] == "smoke" for r in owed)
        line += "; smoke PASS" if smoke_findings == 0 and not smoke_owed else f"; smoke {smoke_findings} findings"
    if counts["Low"]:
        line += f"; L {counts['Low']}"
    if owed:
        line += f"; owed {len(owed)}"
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"rows": rows, "counts": counts, "regressions": regressions, "standing": len(standing),
                       "smoke": None if not smoke_seen else smoke_findings, "line": line}, f, indent=2)
    print(line)
    return 1 if failed else 0


def list_standing(a):
    rows = [r for r in (row_of(raw) for raw in load_sidecar(a.sidecar)) if r]
    rows = [r for r in rows if r.get("class") in ("pre-existing", "owed") and r.get("severity") in ACTIONABLE]
    if a.chunk is not None:
        rows = [r for r in rows if str(r.get("chunk")) == a.chunk]
    order = {s: n for n, s in enumerate(ACTIONABLE)}
    rows.sort(key=lambda r: (str(r.get("chunk")).rjust(4), order[r["severity"]], r.get("round", 0)))
    for r in rows:
        print(f"chunk {r.get('chunk')} r{r.get('round')} {r['severity']} — {r.get('title')} ({where(r)}) [{r.get('reviewer')}]")
    print("standing " + "/".join(str(sum(1 for r in rows if r["severity"] == s)) for s in ACTIONABLE))
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sidecar", required=True, help="rounds-slice-<nnn>.jsonl, created if missing")
    p.add_argument("--report", action="append", default=[], help="a review or smoke report in the shared format (repeatable)")
    p.add_argument("--reviewer", action="append", help="reviewer name for the report in the same position (default: the filename's last segment)")
    p.add_argument("--chunk", help="chunk number, D for the slice review, pr for the external review")
    p.add_argument("--round", type=int, help="round number: 0 the first review, 1 the re-review of the first fix, ...")
    p.add_argument("--project", default=".", help="the repository, for --range")
    p.add_argument("--range", help="<before>..<after> of the fix being re-reviewed; classifies each finding by hunk")
    p.add_argument("--fix", help="the fix commit these findings were raised against")
    p.add_argument("--fixer", help="the fixer agent's id")
    p.add_argument("--turns", type=int, help="the fixer's turn count")
    p.add_argument("--json", help="also write the rows and counts here")
    p.add_argument("--standing", action="store_true", help="list the pre-existing and owed Critical/High/Medium rows instead")
    p.add_argument("--session", default=os.environ.get("CLAUDE_CODE_SESSION_ID"), help="the session recording this round (default: CLAUDE_CODE_SESSION_ID)")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if a.standing:
        return list_standing(a)
    if not a.report or a.chunk is None or a.round is None:
        p.error("--report, --chunk and --round are required unless --standing")
    return record(a)


if __name__ == "__main__":
    sys.exit(main())
