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
   does not list was never loaded by a test, and fails.
3. changes: the change set is not empty. A build that changed nothing is
   not an implementation, whatever the suite says.
4. scope: every file changed since the baseline is inside one of the
   `--allow` entries: an entry ending in `/` allows everything under that
   directory, any other entry allows exactly that file. Untracked files
   count as changed; so do both sides of a rename.
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


def working_tree_changes(project, base):
    """Files that differ from `base`: tracked changes (both sides of a
    rename, so a file moved out of scope or into it is seen) plus untracked
    files git does not ignore. Ignored files are build output and stay out."""
    tracked = git(project, "diff", "--name-only", "--no-renames", base).stdout.splitlines()
    untracked = git(project, "ls-files", "--others", "--exclude-standard").stdout.splitlines()
    return sorted({f for f in tracked + untracked if f})


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


def parse_coverage(output):
    """Node's spec reporter prints the coverage report as an indented tree:

        ℹ file                 | line % | branch % | funcs % | uncovered lines
        ℹ lending              |        |          |         |
        ℹ  cancel-hold.ts      | 100.00 |   100.00 |  100.00 |

    Directory rows have empty numbers; one leading space per level. Returns
    {"lending/cancel-hold.ts": (line %, branch %)}. The TAP reporter's `#`
    prefix is accepted too."""
    rows, stack = {}, []
    row = re.compile(r"^(?:ℹ|#)( *)(\S[^|]*?)\s*\|\s*([\d.]*)\s*\|\s*([\d.]*)\s*\|")
    for line in output.splitlines():
        m = row.match(line)
        if not m or m.group(2) in ("file", "all files"):
            continue
        depth, name, line_pct, branch_pct = len(m.group(1)), m.group(2), m.group(3), m.group(4)
        stack = stack[:depth] + [name]
        if line_pct:
            rows["/".join(stack)] = (float(line_pct), float(branch_pct or 0))
    return rows


SOURCE = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
TEST_DIRS = {"test", "tests", "__tests__", "spec"}
TEST_NAME = re.compile(r"\.(test|spec)\.[cm]?[jt]sx?$")


def is_test_file(path):
    parts = path.split("/")
    return any(p in TEST_DIRS for p in parts[:-1]) or bool(TEST_NAME.search(parts[-1]))


def check_coverage(output, files, min_line, min_branch):
    """`files`: the changed files that exist. Node lists every file the tests
    loaded, so a changed source file with no row was never loaded: that is
    zero coverage, not nothing to check."""
    rows = parse_coverage(output)
    if not rows:
        return {"passed": False, "reason": "no coverage table in the test output", "files": {}}
    checked, low, unmeasured = {}, [], []
    for f in files:
        if is_test_file(f) or not f.endswith(SOURCE):
            continue
        if f not in rows:
            unmeasured.append(f)
            continue
        line, branch = rows[f]
        checked[f] = {"line": line, "branch": branch}
        if line < min_line or branch < min_branch:
            low.append(f)
    return {"passed": not low and not unmeasured, "files": checked, "below_minimum": low,
            "not_measured": unmeasured, "min_line": min_line, "min_branch": min_branch}


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
        report["checks"]["coverage"] = check_coverage(output, present, a.min_line, a.min_branch)
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
        elif name == "coverage" and not c["passed"]:
            detail = " " + (c.get("reason") or "below minimum: " + ", ".join(
                c["below_minimum"] + [f + " (not in the coverage table)" for f in c["not_measured"]]))
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
