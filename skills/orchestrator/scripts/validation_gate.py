"""Mechanical checks on an implementation candidate, before any reviewer reads it.

Run inside a project (or a candidate's worktree) after an implementation
lands. It answers five questions that need no judgment, and prints a JSON
verdict so the orchestrator's Grade step can drop a candidate that fails
them without spending reviewers on it (the skill's "Quarantine, grade,
combine" section says when it runs and with which arguments):

1. suite: the project's test runner exits 0 within `--timeout` seconds and
   prints a summary with no failures (Node's spec reporter: `ℹ fail 0`;
   anything else: exit code). On failure the output's tail is printed.
2. coverage: with `--coverage`, Node's `--experimental-test-coverage` table
   reports line and branch coverage at or above `--min-line` / `--min-branch`
   for the source files the change touched. A changed source file the table
   does not list was never loaded by a test, and fails. Two things that are
   not gaps, told apart with `ts_runtime_lines.mjs` next to this script
   (Node strips the types and says which lines keep runtime code): a
   TypeScript file with no runtime code at all (a port interface, a types
   module) is exempt, since nothing can load it; and uncovered lines that
   hold only erased type declarations are discounted from a loaded file's
   line percentage, since under `--experimental-transform-types` Node
   counts them against it. Without `node`, or when Node cannot parse the
   file, every line counts as it did before.
3. changes: the change set is not empty. A build that changed nothing is
   not an implementation, whatever the suite says.
4. scope: every file changed since the baseline is inside one of the
   `--allow` entries: an entry ending in `/` allows everything under that
   directory, any other entry allows exactly that file. Untracked files
   count as changed; so do both sides of a rename. Claude Code's own files
   are never part of the change set: a `.claude/` directory at any depth
   (the `Agent` tool keeps the quarantine candidates' worktrees under
   `.claude/worktrees/` inside the real project, and the session's sandbox
   mounts empty placeholder settings into every directory a command runs
   from, both of which git lists as untracked) and `.mcp.json`.
5. protected: every `--protect` file is byte-identical to the baseline.

The change set is computed after the test command has run, so a test that
edits the tree is caught too.

The baseline is `--base` (a commit, default `HEAD`), or better a baseline
file: `--record-baseline FILE` writes the current commit plus a hash of
every file already modified or untracked in the working tree, and
`--baseline FILE` later diffs against that commit while ignoring those
files as long as their content is still what was recorded. That is how a
real project with uncommitted planning documents is gated without the
documents counting as the candidate's changes. Record it in the real
project before the candidates are launched; keep the file outside the
working tree (`.git/` is a good place) so it is never a change itself.

Exit 0 when every check passes, 1 otherwise (also when git cannot compute
the change set: an unknown base must not read as "nothing changed").
The same checks are what the
`tdd-implementation-*` eval cases prove with trace regexes; this is the
runtime version for real candidates.

Usage: python3 -I ${CLAUDE_SKILL_DIR}/scripts/validation_gate.py [--project DIR]
           [--base HEAD | --baseline FILE] [--allow lending/ --allow test/ ...]
           [--protect docs/x/design.md ...] [--test-cmd "npm test"] [--timeout 600]
           [--coverage] [--min-line 90] [--min-branch 80] [--json out.json]
       python3 -I .../validation_gate.py [--project DIR] --record-baseline FILE
       (from this repository: python3 -I skills/orchestrator/scripts/validation_gate.py ...)
The test command is split the way a shell would and run without one (so
no pipes or `&&`); its program is resolved on PATH, which is how `npm`
finds its `npm.cmd` shim on Windows.
"""
import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys


def git(project, *args):
    proc = subprocess.run(["git", *args], cwd=project, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"FAIL  git {' '.join(args)}: {proc.stderr.strip()}\nvalidation gate: FAIL")
    return proc


def file_hash(project, path):
    full = os.path.join(project, path)
    if not os.path.isfile(full):
        return None
    with open(full, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def claude_code_path(path):
    """Claude Code's own files inside the project, never a candidate's
    change: a `.claude/` directory at any depth (the `Agent` tool's
    worktrees under `.claude/worktrees/`, session scratch, and the empty
    placeholder settings the session's sandbox mounts into every directory
    a command runs from, which git lists as untracked from inside it) and
    `.mcp.json` beside it. A settings edit there is the sandbox check's to
    catch before every launch, not the gate's."""
    parts = path.split("/")
    return ".claude" in parts or parts[-1] == ".mcp.json"


def working_tree_changes(project, base):
    """Files that differ from `base`: tracked changes (both sides of a
    rename, so a file moved out of scope or into it is seen) plus untracked
    files git does not ignore. Ignored files are build output and stay out,
    and so does everything `claude_code_path` names."""
    tracked = git(project, "diff", "--name-only", "--no-renames", base).stdout.splitlines()
    untracked = git(project, "ls-files", "--others", "--exclude-standard").stdout.splitlines()
    return sorted({f for f in tracked + untracked if f and not claude_code_path(f)})


def record_baseline(project, path):
    base = git(project, "rev-parse", "HEAD").stdout.strip()
    files = {f: file_hash(project, f) for f in working_tree_changes(project, base)}
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"base": base, "project": os.path.abspath(project), "files": files}, f, indent=2)
    print(f"baseline recorded: commit {base[:12]}, {len(files)} pre-existing change(s)")


def changed_files(project, base, baseline):
    """The candidate's own changes: everything that differs from the base
    commit, minus files the baseline recorded whose content is unchanged."""
    files = working_tree_changes(project, base)
    if baseline:
        recorded = baseline["files"]
        files = [f for f in files if f not in recorded or file_hash(project, f) != recorded[f]]
        # A pre-existing untracked file that is now gone is a change too: it
        # appears in neither git listing, only in the baseline.
        if os.path.abspath(project) == baseline.get("project", os.path.abspath(project)):
            files += [f for f in recorded if recorded[f] and f not in files and file_hash(project, f) is None]
    return sorted(set(files))


def allowed(path, entry):
    return path.startswith(entry) if entry.endswith("/") else path == entry


def check_scope(files, allow):
    outside = [f for f in files if not any(allowed(f, e) for e in allow)]
    return {"passed": not outside, "changed": files, "outside": outside}


def check_protected(project, protect, changed_files):
    """A protected file fails if it is in the change set, which already
    covers a deleted tracked file and a baseline-recorded file that is gone.
    Absence alone is not a change: an uncommitted planning document does not
    exist in a candidate's worktree, and a CRLF checkout is not an edit."""
    changed = [p for p in protect if p in changed_files]
    return {"passed": not changed, "changed": changed}


def coverage_command(project, cmd):
    """`npm test` with coverage: run the package's test script through node
    directly with `--experimental-test-coverage` inserted, since npm's
    Windows shim rejects NODE_OPTIONS and node ignores the flag after the
    test file list. Any other command is run as given with NODE_OPTIONS."""
    if cmd.strip() in ("npm test", "npm run test"):
        try:
            script = json.load(open(os.path.join(project, "package.json"), encoding="utf-8"))["scripts"]["test"]
        except (OSError, ValueError, KeyError):
            script = None
        if script and script.startswith("node "):
            return "node --experimental-test-coverage " + script[len("node "):], None
    return cmd, (os.environ.get("NODE_OPTIONS", "") + " --experimental-test-coverage").strip()


def run_tests(project, cmd, coverage, timeout):
    env = dict(os.environ)
    if coverage:
        cmd, node_options = coverage_command(project, cmd)
        if node_options:
            env["NODE_OPTIONS"] = node_options
    argv = shlex.split(cmd)
    if not argv:
        raise SystemExit("FAIL  --test-cmd is empty" + chr(10) + "validation gate: FAIL")
    program = shutil.which(argv[0])
    if not program:
        raise SystemExit(f"FAIL  --test-cmd: {argv[0]} is not on PATH" + chr(10) + "validation gate: FAIL")
    try:
        # The operator's own test command, resolved above and run without a shell.
        proc = subprocess.run([program, *argv[1:]], cwd=project, capture_output=True, text=True,  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
                              env=env, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as e:
        out = ((e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")) + \
              ((e.stderr or b"").decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or ""))
        return {"passed": False, "exit_code": None, "timed_out": True, "timeout": timeout,
                "summary_fail_count": None, "output_tail": out[-2000:]}, out
    out = proc.stdout + proc.stderr
    fails = re.findall(r"ℹ fail (\d+)", out)
    summary_green = fails[-1] == "0" if fails else None
    passed = proc.returncode == 0 and summary_green is not False
    return {"passed": passed, "exit_code": proc.returncode, "timed_out": False,
            "summary_fail_count": fails[-1] if fails else None, "output_tail": out[-2000:]}, out


def parse_uncovered(text):
    """The `uncovered lines` column: `3-5 12-14 16` (Node separates the
    ranges with spaces; commas are accepted too) as a set of line numbers,
    or None when the column was cut short (`…`), since a partial list
    cannot be discounted from."""
    if "…" in text or "..." in text:
        return None
    lines = set()
    for a, b in re.findall(r"(\d+)(?:-(\d+))?", text):
        lines.update(range(int(a), int(b or a) + 1))
    return lines


def parse_coverage(output):
    """Node's spec reporter prints the coverage report as an indented tree:

        ℹ file                 | line % | branch % | funcs % | uncovered lines
        ℹ lending              |        |          |         |
        ℹ  cancel-hold.ts      | 100.00 |   100.00 |  100.00 | 3-5

    Directory rows have empty numbers. After the reporter's own `ℹ ` prefix
    (the TAP reporter's `# ` is accepted too), one leading space per level:
    a top-level directory has none, a file inside it has one. Returns
    {"lending/cancel-hold.ts": {"line": %, "branch": %, "uncovered": set}}."""
    rows, stack = {}, []
    row = re.compile(r"^(?:ℹ|#) ( *)(\S[^|]*?)\s*\|\s*([\d.]*)\s*\|\s*([\d.]*)\s*\|\s*([\d.]*)\s*\|(.*)$")
    for line in output.splitlines():
        m = row.match(line)
        if not m or m.group(2) in ("file", "all files"):
            continue
        depth, name, line_pct, branch_pct = len(m.group(1)), m.group(2), m.group(3), m.group(4)
        stack = stack[:depth] + [name]
        if line_pct:
            rows["/".join(stack)] = {"line": float(line_pct), "branch": float(branch_pct or 0),
                                     "uncovered": parse_uncovered(m.group(6))}
    return rows


SOURCE = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
TEST_DIRS = {"test", "tests", "__tests__", "spec"}
TEST_NAME = re.compile(r"\.(test|spec)\.[cm]?[jt]sx?$")


def is_test_file(path):
    parts = path.split("/")
    return any(p in TEST_DIRS for p in parts[:-1]) or bool(TEST_NAME.search(parts[-1]))


def runtime_lines(project, files):
    """{file: set of 1-based lines holding runtime code} for the TypeScript
    files among `files`, from `ts_runtime_lines.mjs` (Node strips the types;
    strip mode keeps lines in place, transform mode answers through its
    source map when strip mode refuses a construct). A file Node cannot
    parse is left out, and so is everything when `node` is not on PATH or
    the helper fails: a missing answer means every line counts."""
    ts = [f for f in files if f.endswith((".ts", ".tsx"))]
    helper = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ts_runtime_lines.mjs")
    node = shutil.which("node")
    if not ts or not node or not os.path.isfile(helper):
        return {}
    try:
        # The helper next to this script, given the changed files; no shell.
        proc = subprocess.run([node, "--no-warnings", helper, *ts], cwd=project,  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        answers = json.loads(proc.stdout)
    except (subprocess.TimeoutExpired, ValueError, OSError):
        return {}
    return {a["file"]: set(a["lines"]) for a in answers if isinstance(a, dict) and "lines" in a}


def check_coverage(output, files, min_line, min_branch, project):
    """`files`: the changed files that exist. Node lists every file the tests
    loaded, so a changed source file with no row was never loaded: that is
    zero coverage, not nothing to check. Except a file with no runtime code
    (types only), which nothing can load: exempt, and named as such. For a
    loaded file, uncovered lines that hold no runtime code (erased type
    declarations, counted against the file under transform mode) are taken
    out of both sides of the line percentage: the table's own numbers give
    the lines it counted (`uncovered / (1 - line%)`), and the discount
    recomputes against the rest."""
    rows = parse_coverage(output)
    if not rows:
        return {"passed": False, "reason": "no coverage table in the test output", "files": {}}
    runtime = runtime_lines(project, [f for f in files if not is_test_file(f)])
    checked, low, unmeasured, type_only = {}, [], [], []
    for f in files:
        if is_test_file(f) or not f.endswith(SOURCE):
            continue
        if f in runtime and not runtime[f]:
            type_only.append(f)
            continue
        if f not in rows:
            unmeasured.append(f)
            continue
        line, branch, uncovered = rows[f]["line"], rows[f]["branch"], rows[f]["uncovered"]
        checked[f] = {"line": line, "branch": branch}
        if f in runtime and uncovered and line < 100:
            erased = uncovered - runtime[f]
            if erased:
                counted = round(len(uncovered) / (1 - line / 100))
                covered = counted - len(uncovered)
                remaining = counted - len(erased)
                line = 100.0 if remaining <= 0 else round(100.0 * covered / remaining, 2)
                checked[f].update({"line": line, "reported_line": rows[f]["line"],
                                   "type_only_lines_discounted": sorted(erased)})
        if line < min_line or branch < min_branch:
            low.append(f)
    return {"passed": not low and not unmeasured, "files": checked, "below_minimum": low,
            "not_measured": unmeasured, "type_only": type_only,
            "min_line": min_line, "min_branch": min_branch}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", default=".")
    p.add_argument("--base", default="HEAD")
    p.add_argument("--baseline", help="baseline file written by --record-baseline (overrides --base)")
    p.add_argument("--record-baseline", metavar="FILE", help="write the baseline for later runs and exit")
    p.add_argument("--allow", action="append", default=[], help="path the change may touch: dir/ or exact file (repeatable)")
    p.add_argument("--protect", action="append", default=[], help="file that must be unchanged (repeatable)")
    p.add_argument("--test-cmd", default="npm test")
    p.add_argument("--timeout", type=float, default=600, help="seconds the test command may take")
    p.add_argument("--coverage", action="store_true")
    p.add_argument("--min-line", type=float, default=90)
    p.add_argument("--min-branch", type=float, default=80)
    p.add_argument("--json")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    project = os.path.abspath(a.project)
    if a.record_baseline:
        record_baseline(project, a.record_baseline)
        return 0

    baseline, base = None, a.base
    if a.baseline:
        with open(a.baseline, encoding="utf-8") as f:
            baseline = json.load(f)
        base = baseline["base"]
    git(project, "rev-parse", "--verify", "--quiet", base + "^{commit}")

    report = {"base": base, "baseline": a.baseline, "checks": {}}
    report["checks"]["suite"], output = run_tests(project, a.test_cmd, a.coverage, a.timeout)
    # After the tests, so a test command that edits the tree is seen.
    files = changed_files(project, base, baseline)
    if a.coverage:
        present = [f for f in files if os.path.isfile(os.path.join(project, f))]
        report["checks"]["coverage"] = check_coverage(output, present, a.min_line, a.min_branch, project)
    report["checks"]["changes"] = {"passed": bool(files), "count": len(files),
                                   "files": sorted(files)}
    if a.allow:
        report["checks"]["scope"] = check_scope(files, a.allow)
    if a.protect:
        report["checks"]["protected"] = check_protected(project, a.protect, files)
    report["passed"] = all(c["passed"] for c in report["checks"].values())

    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    for name, c in report["checks"].items():
        detail = ""
        if name == "scope" and c["outside"]:
            detail = " outside: " + ", ".join(c["outside"])
        elif name == "protected" and c["changed"]:
            detail = " changed: " + ", ".join(c["changed"])
        elif name == "changes":
            # Listed, not only counted: the orchestrator hands the finalized
            # build's reviewers exactly these files. As a JSON list, so a
            # comma or a space in a name cannot split or join entries.
            detail = (f" {c['count']} file(s): " + json.dumps(c["files"]) if c["passed"]
                      else " 0 file(s), nothing changed")
        elif name == "coverage":
            if not c["passed"]:
                detail = " " + (c.get("reason") or "below minimum: " + ", ".join(
                    c["below_minimum"] + [f + " (not in the coverage table)" for f in c["not_measured"]]))
            if c.get("type_only"):
                detail += " (types only, exempt: " + ", ".join(c["type_only"]) + ")"
            discounted = [f for f, v in c.get("files", {}).items() if "reported_line" in v]
            if discounted:
                detail += " (erased type lines discounted: " + ", ".join(
                    f"{f} {c['files'][f]['reported_line']:g} -> {c['files'][f]['line']:g}" for f in discounted) + ")"
        elif name == "suite" and not c["passed"]:
            detail = (f" timed out after {c['timeout']:g}s" if c["timed_out"]
                      else f" exit {c['exit_code']}, summary fail count {c['summary_fail_count']}")
        print(f"{'PASS' if c['passed'] else 'FAIL'}  {name}{detail}")
    if not report["checks"]["suite"]["passed"]:
        tail = "\n".join(output.splitlines()[-30:])
        print("--- test output, last 30 lines ---\n" + tail + "\n---")
    print("validation gate:", "PASS" if report["passed"] else "FAIL")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
