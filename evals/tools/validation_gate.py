"""Mechanical checks on an implementation candidate, before any reviewer reads it.

Run inside a project (or a candidate's worktree) after an implementation
lands. It answers four questions that need no judgment, and prints a JSON
verdict so the orchestrator's Grade step can drop a candidate that fails
them without spending reviewers on it:

1. suite: the project's test runner exits 0 and prints a summary with no
   failures (Node's spec reporter: `ℹ fail 0`; anything else: exit code).
2. coverage: with `--coverage`, Node's `--experimental-test-coverage` table
   reports line and branch coverage at or above `--min-line` / `--min-branch`
   for the source files the change touched. A changed source file the table
   does not list was never loaded by a test, and fails.
3. scope: every file changed since `--base` (git) is inside one of the
   `--allow` path prefixes. Untracked files count as changed.
4. protected: every `--protect` file is byte-identical to `--base`.

Exit 0 when every check passes, 1 otherwise (also when git cannot compute
the change set: an unknown `--base` must not read as "nothing changed").
The same checks are what the
`tdd-implementation-*` eval cases prove with trace regexes; this is the
runtime version for real candidates.

Usage: python3 -I evals/tools/validation_gate.py [--project DIR] [--base HEAD]
           [--allow lending/ --allow test/ ...] [--protect docs/x/design.md ...]
           [--test-cmd "npm test"] [--coverage] [--min-line 90] [--min-branch 80]
           [--json out.json]
"""
import argparse
import json
import os
import re
import subprocess
import sys


def git(project, *args):
    proc = subprocess.run(["git", *args], cwd=project, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"FAIL  git {' '.join(args)}: {proc.stderr.strip()}\nvalidation gate: FAIL")
    return proc


def changed_files(project, base):
    tracked = git(project, "diff", "--name-only", base).stdout.splitlines()
    untracked = git(project, "ls-files", "--others", "--exclude-standard").stdout.splitlines()
    return sorted({f for f in tracked + untracked if f})


def check_scope(files, allow):
    outside = [f for f in files if not any(f.startswith(p) for p in allow)]
    return {"passed": not outside, "changed": files, "outside": outside}


def check_protected(project, protect, changed_files):
    """A protected file fails if git reports it changed since base (so a
    CRLF checkout doesn't count as a change), or if it is missing."""
    changed = [p for p in protect
               if p in changed_files or not os.path.isfile(os.path.join(project, p))]
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


def run_tests(project, cmd, coverage):
    env = dict(os.environ)
    if coverage:
        cmd, node_options = coverage_command(project, cmd)
        if node_options:
            env["NODE_OPTIONS"] = node_options
    proc = subprocess.run(cmd, cwd=project, shell=True, capture_output=True, text=True,
                          env=env, encoding="utf-8", errors="replace")
    out = proc.stdout + proc.stderr
    fails = re.findall(r"ℹ fail (\d+)", out)
    summary_green = fails[-1] == "0" if fails else None
    passed = proc.returncode == 0 and summary_green is not False
    return {"passed": passed, "exit_code": proc.returncode, "summary_fail_count": fails[-1] if fails else None,
            "output_tail": out[-2000:]}, out


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


SOURCE = (".ts", ".js", ".mjs", ".cjs")


def check_coverage(output, files, min_line, min_branch):
    """`files`: the changed files that exist. Node lists every file the tests
    loaded, so a changed source file with no row was never loaded: that is
    zero coverage, not nothing to check."""
    rows = parse_coverage(output)
    if not rows:
        return {"passed": False, "reason": "no coverage table in the test output", "files": {}}
    checked, low, unmeasured = {}, [], []
    for f in files:
        if f.startswith("test/") or f.endswith(".test.ts") or not f.endswith(SOURCE):
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
    p.add_argument("--allow", action="append", default=[], help="path prefix the change may touch (repeatable)")
    p.add_argument("--protect", action="append", default=[], help="file that must be unchanged (repeatable)")
    p.add_argument("--test-cmd", default="npm test")
    p.add_argument("--coverage", action="store_true")
    p.add_argument("--min-line", type=float, default=90)
    p.add_argument("--min-branch", type=float, default=80)
    p.add_argument("--json")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    project = os.path.abspath(a.project)
    files = changed_files(project, a.base)
    report = {"base": a.base, "checks": {}}
    report["checks"]["suite"], output = run_tests(project, a.test_cmd, a.coverage)
    if a.coverage:
        present = [f for f in files if os.path.isfile(os.path.join(project, f))]
        report["checks"]["coverage"] = check_coverage(output, present, a.min_line, a.min_branch)
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
        elif name == "coverage" and not c["passed"]:
            detail = " " + (c.get("reason") or "below minimum: " + ", ".join(
                c["below_minimum"] + [f + " (not in the coverage table)" for f in c["not_measured"]]))
        elif name == "suite" and not c["passed"]:
            detail = f" exit {c['exit_code']}, summary fail count {c['summary_fail_count']}"
        print(f"{'PASS' if c['passed'] else 'FAIL'}  {name}{detail}")
    print("validation gate:", "PASS" if report["passed"] else "FAIL")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
