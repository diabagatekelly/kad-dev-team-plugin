"""Mechanical checks on an implementation change, before any reviewer reads it.

Run inside a project after a chunk (or a fix) has been committed. It
answers seven questions that need no judgment, and prints a JSON verdict so
the orchestrator's chunk loop can send a failing chunk back to a fixer
without spending reviewers on it (the skill's "The chunk loop" section says
when it runs and with which arguments: `--base` is the commit before the
chunk, `--allow` the chunk's planned files, `--module-dir` the design's
module directories as the orchestrator's B step lists them):

1. suite: the project's test runner exits 0 within `--timeout` seconds and
   prints a summary with no failures (Node's spec reporter: `ℹ fail 0`;
   anything else: exit code). On failure the output's tail is printed.
1b. typecheck and lint: the project's own scripts, when it has them. With
   `--typecheck-cmd` / `--lint-cmd` those commands run as given; otherwise
   `package.json`'s `scripts.typecheck` and `scripts.lint` run through the
   runner the test command names (`npm test` -> `npm run typecheck`,
   `corepack pnpm test` -> `corepack pnpm run typecheck`, likewise `pnpm`,
   `yarn`, `bun`; a bare `node ...` test command uses `npm`). A script the
   manifest does not have is a `SKIP` line, never a failure: the Definition
   of Done at D is where a missing linter becomes a finding. Exit 0 within
   `--timeout` is PASS; on FAIL the output's tail is printed.
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
   file (JSX: Node's type stripping takes no `.tsx`), every line counts as
   it did before. The per-line data comes from Node's `lcov` reporter,
   added next to the project's own reporter when the test script is a
   `node` command, so the discount never depends on the table's
   `uncovered lines` column, which Node truncates with `…` when it is
   long; with another test command the table is all there is, and a
   truncated column means no discount, which the output says.
3. changes: the change set is not empty. A build that changed nothing is
   not an implementation, whatever the suite says.
4. scope: every file changed since the baseline is inside one of the
   `--allow` entries: an entry ending in `/` allows everything under that
   directory, any other entry allows exactly that file. A changed file on
   no `--allow` entry but inside a `--module-dir` (repeatable; the design's
   module directories) is a **deviation**: the chunk plan did not name it,
   the design's structure does, so it is listed on the `scope` line and in
   the JSON (`scope.deviations`) for the orchestrator's C line, and the
   check still passes; the builder's report names why. A changed file
   under neither is `outside` and fails the check: that is the one the
   fixer moves. Untracked files
   count as changed; so do both sides of a rename. Claude Code's own
   placeholders are not: an untracked path under a `.claude/` directory,
   or named `.mcp.json`, that is not a regular file with content (the
   `Agent` tool keeps worktree-isolated agents' trees under
   `.claude/worktrees/` inside the real project, and the session's sandbox
   mounts empty placeholder settings into every directory a command runs
   from, both of which git lists as untracked). A settings file a
   change that actually wrote one there has content and stays in the set.
5. protected: every `--protect` file is byte-identical to the baseline.

After the checks, two report-only `INFO` lines (never part of the
verdict; also under `metrics` in the JSON), computed over the changed
source files (`.ts .tsx .js .jsx .mjs .cjs .py`, test files left out) so
the orchestrator records them per commit and the Definition of Done at D
acts on the slice's figures:

- comments: comment lines as a share of non-blank lines in the changed
  source files, and the same share across `src/` (or, without a `src/`,
  across the `--module-dir`s). A comment line is one whose first token
  opens `//`, `#` (Python) or a `/* ... */` block (JSX `{/* */}` too), one
  inside such a block, or a line of a Python docstring opened at the
  start of a statement. Strings are not parsed, so a `//` inside a string
  at the start of a line would count: a heuristic, close enough for a
  5% threshold.
- size: files over 300 non-blank lines; functions over 40 lines (TS/JS:
  `function name(`, `name(...) {` methods, `const name = (...) => {` and
  `= function` expressions, measured to the brace that closes the body
  with braces inside strings and comments ignored line by line; Python:
  a `def` to the last line indented deeper than it); and the share of
  non-blank lines at nesting depth 4 or more (brace depth at the start
  of the line for brace languages, indent level for Python, the indent
  unit being the file's smallest indent). All approximate: a brace in a
  multi-line template literal or a regex is counted, a one-line arrow
  function is not a function. The numbers are prompts for the reviewer,
  not findings.

The change set is computed after the test command has run, so a test that
edits the tree is caught too.

The baseline is `--base` (a commit, default `HEAD`): the chunk loop
commits the planning documents and each chunk, so the previous commit is
always the right base. For a tree with uncommitted documents that must not
count as the change, a baseline file still works: `--record-baseline FILE`
writes the current commit plus a hash of every file already modified or
untracked, and `--baseline FILE` later diffs against that commit while
ignoring those files as long as their content is unchanged; keep the file
outside the working tree (`.git/` is a good place).

Exit 0 when every check passes, 1 otherwise (also when git cannot compute
the change set: an unknown base must not read as "nothing changed").
The same checks are what the
`tdd-implementation-*` eval cases prove with trace regexes; this is the
runtime version for real changes.

A protected document the user amends while the flow is running (a design
reopened after an escalation) would fail the protected check for a reason
that is not the build's: `--baseline FILE --accept-protected PATH`, with
the same `--protect` list as the gate (the path must be on it), rewrites
that one file's recorded hash to its current content, prints the old and
new hash, and exits, so the next gate run accepts the user's amendment
and still catches any other change to it. It never re-records the whole
baseline, which would hide the build's own files, and it refuses a path
that is not a protected document, since accepting a source file would
hide a candidate's edit the same way.

Usage: python3 -I ${CLAUDE_SKILL_DIR}/scripts/validation_gate.py [--project DIR]
           [--base HEAD | --baseline FILE] [--allow lending/ --allow test/ ...]
           [--module-dir src/lending ...] [--protect docs/x/design.md ...]
           [--test-cmd "npm test"] [--typecheck-cmd CMD] [--lint-cmd CMD] [--timeout 600]
           [--coverage] [--min-line 90] [--min-branch 80] [--json out.json]
       python3 -I .../validation_gate.py [--project DIR] --record-baseline FILE
       python3 -I .../validation_gate.py [--project DIR] --baseline FILE --protect PATH ... --accept-protected PATH
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
import stat
import subprocess
import sys
import tempfile


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


def git(project, *args):
    proc = subprocess.run([find_git(), *args], cwd=project, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"FAIL  git {' '.join(args)}: {proc.stderr.strip()}\nvalidation gate: FAIL")
    return proc


def file_hash(project, path):
    full = os.path.join(project, path)
    if not os.path.isfile(full):
        return None
    with open(full, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def claude_code_placeholder(project, path):
    """An untracked path under a `.claude/` directory, or named `.mcp.json`,
    that nothing wrote: Claude Code's own presence in the project, never a
    candidate's change. The `Agent` tool keeps the quarantine candidates'
    worktrees under `.claude/worktrees/` (git lists each as an untracked
    directory of the real tree), and the session's sandbox mounts empty
    placeholder settings into every directory a command runs from (device
    nodes or empty files, listed as untracked from inside it). What stays
    in the change set: a regular file with content, wherever it is, so a
    candidate that writes a `.claude/settings.json` or an `.mcp.json` is
    seen by scope and by the judge; and every tracked change."""
    parts = path.split("/")
    if ".claude" not in parts and parts[-1] != ".mcp.json":
        return False
    try:
        st = os.lstat(os.path.join(project, path))
    except OSError:
        return True  # listed but gone or unreachable: nothing a candidate left
    return not stat.S_ISREG(st.st_mode) or st.st_size == 0


def working_tree_changes(project, base):
    """Files that differ from `base`: tracked changes (both sides of a
    rename, so a file moved out of scope or into it is seen) plus untracked
    files git does not ignore. Ignored files are build output and stay out,
    and so do Claude Code's own placeholders (`claude_code_placeholder`)."""
    tracked = git(project, "diff", "--name-only", "--no-renames", base).stdout.splitlines()
    untracked = git(project, "ls-files", "--others", "--exclude-standard").stdout.splitlines()
    untracked = [f for f in untracked if f and not claude_code_placeholder(project, f)]
    return sorted({f for f in tracked + untracked if f})


def record_baseline(project, path):
    base = git(project, "rev-parse", "HEAD").stdout.strip()
    files = {f: file_hash(project, f) for f in working_tree_changes(project, base)}
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"base": base, "project": os.path.abspath(project), "files": files}, f, indent=2)
    print(f"baseline recorded: commit {base[:12]}, {len(files)} pre-existing change(s)")


def accept_protected(project, path, rel, protect):
    """Rewrite one file's recorded hash in the baseline to its current
    content: the user's own amendment of a protected document, accepted
    without re-recording anything else. Only a path the same command names
    with `--protect` can be accepted: a source file a candidate edited is
    never a protected document, and accepting it would hide the edit from
    the scope and coverage checks (`changed_files` drops a recorded file
    whose hash still matches)."""
    if rel not in protect:
        print(f"baseline not updated: {rel} is not among this command's --protect files; "
              "only a protected document can be accepted")
        return 1
    with open(path, encoding="utf-8") as f:
        baseline = json.load(f)
    old = baseline["files"].get(rel)
    new = file_hash(project, rel)
    if new is None:
        print(f"baseline not updated: {rel} does not exist in {project}")
        return 1
    baseline["files"][rel] = new
    # Written whole into a sibling file and swapped in, so an interrupted
    # write never leaves the baseline truncated.
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2)
    os.replace(tmp, path)
    print(f"baseline updated: {rel} {(old or 'unrecorded')[:12]} -> {new[:12]}")
    return 0


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


def under(path, directory):
    return path.startswith(directory.rstrip("/") + "/")


def check_scope(files, allow, module_dirs=()):
    """Three-way: on an `--allow` entry, fine; off the list but inside a
    `--module-dir`, a deviation the chunk plan did not foresee (reported,
    not failed); under neither, outside the slice, which fails."""
    unlisted = [f for f in files if not any(allowed(f, e) for e in allow)]
    deviations = [f for f in unlisted if any(under(f, d) for d in module_dirs)]
    outside = [f for f in unlisted if f not in deviations]
    return {"passed": not outside, "changed": files, "deviations": deviations, "outside": outside}


def check_protected(project, protect, changed_files):
    """A protected file fails if it is in the change set, which already
    covers a deleted tracked file and a baseline-recorded file that is gone.
    Absence alone is not a change: an uncommitted planning document does not
    exist in a candidate's worktree, and a CRLF checkout is not an edit."""
    changed = [p for p in protect if p in changed_files]
    return {"passed": not changed, "changed": changed}


def with_lcov_reporter(script, lcov_path):
    """The node test script with Node's `lcov` reporter writing to
    `lcov_path` beside the script's own reporter(s). Node requires one
    destination per reporter, so each reporter the script names without a
    destination gets `stdout`, and a script that names none gets the
    default `spec` on `stdout` explicitly (adding `lcov` alone would replace
    the default and take the summary with it)."""
    args = shlex.split(script)
    reporters = sum(1 for a in args if a == "--test-reporter" or a.startswith("--test-reporter="))
    destinations = sum(1 for a in args if a == "--test-reporter-destination" or a.startswith("--test-reporter-destination="))
    extra = []
    if reporters == 0:
        extra += ["--test-reporter=spec", "--test-reporter-destination=stdout"]
    else:
        extra += ["--test-reporter-destination=stdout"] * max(0, reporters - destinations)
    extra += ["--test-reporter=lcov", "--test-reporter-destination=" + lcov_path]
    # Before the test file list: node ignores test-runner flags after it. A
    # flag that takes its value as the next argument keeps it.
    head, tail = [], []
    rest = args[1:]
    i = 0
    while i < len(rest):
        a = rest[i]
        if tail or not a.startswith("-"):
            tail.append(a)
        else:
            head.append(a)
            if a in VALUE_FLAGS and i + 1 < len(rest):
                head.append(rest[i + 1])
                i += 1
        i += 1
    return " ".join(shlex.quote(a) for a in ["node", "--experimental-test-coverage", *head, *extra, *tail])


# Node flags whose value is the next argument when written without `=`.
VALUE_FLAGS = {"--import", "--require", "-r", "--loader", "--experimental-loader", "--conditions", "-C",
               "--env-file", "--input-type", "--test-reporter", "--test-reporter-destination",
               "--test-name-pattern", "--test-skip-pattern", "--test-concurrency", "--test-timeout",
               "--test-shard", "--test-coverage-include", "--test-coverage-exclude", "--max-old-space-size"}


def coverage_command(project, cmd, lcov_path):
    """`npm test` with coverage: run the package's test script through node
    directly with `--experimental-test-coverage` inserted, since npm's
    Windows shim rejects NODE_OPTIONS and node ignores the flag after the
    test file list; the `lcov` reporter is added for exact per-line data.
    Any other command is run as given with NODE_OPTIONS, and only the
    table is available."""
    if cmd.strip() in ("npm test", "npm run test"):
        try:
            script = json.load(open(os.path.join(project, "package.json"), encoding="utf-8"))["scripts"]["test"]
        except (OSError, ValueError, KeyError):
            script = None
        if script and script.startswith("node "):
            return with_lcov_reporter(script, lcov_path), None
    return cmd, (os.environ.get("NODE_OPTIONS", "") + " --experimental-test-coverage").strip()


def run_command(project, cmd, timeout, flag, env=None):
    """The project's own command (`flag` names which option gave it), split
    like a shell would, its program resolved on PATH, run without a shell.
    Returns (result, output); the result's `passed` is exit 0 in time."""
    argv = shlex.split(cmd)
    if not argv:
        raise SystemExit(f"FAIL  {flag} is empty" + chr(10) + "validation gate: FAIL")
    program = shutil.which(argv[0])
    if not program:
        raise SystemExit(f"FAIL  {flag}: {argv[0]} is not on PATH" + chr(10) + "validation gate: FAIL")
    try:
        # The operator's own command, resolved above and run without a shell.
        proc = subprocess.run([program, *argv[1:]], cwd=project, capture_output=True, text=True,  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
                              env=env or dict(os.environ), encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as e:
        out = ((e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")) + \
              ((e.stderr or b"").decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or ""))
        return {"passed": False, "command": cmd, "exit_code": None, "timed_out": True, "timeout": timeout,
                "output_tail": out[-2000:]}, out
    out = proc.stdout + proc.stderr
    return {"passed": proc.returncode == 0, "command": cmd, "exit_code": proc.returncode, "timed_out": False,
            "output_tail": out[-2000:]}, out


def run_tests(project, cmd, coverage, timeout, lcov_path=None):
    env = dict(os.environ)
    if coverage:
        cmd, node_options = coverage_command(project, cmd, lcov_path)
        if node_options:
            env["NODE_OPTIONS"] = node_options
    result, out = run_command(project, cmd, timeout, "--test-cmd", env)
    fails = re.findall(r"ℹ fail (\d+)", out)
    summary_green = fails[-1] == "0" if fails else None
    result["passed"] = result["passed"] and summary_green is not False
    result["summary_fail_count"] = fails[-1] if fails else None
    return result, out


def manifest_script(project, name):
    try:
        return json.load(open(os.path.join(project, "package.json"), encoding="utf-8"))["scripts"][name]
    except (OSError, ValueError, KeyError, TypeError):
        return None


def script_runner(test_cmd):
    """The package runner the test command names, so typecheck and lint run
    the way the project runs its tests."""
    argv = shlex.split(test_cmd)
    if argv[:2] == ["corepack", "pnpm"]:
        return "corepack pnpm"
    if argv and argv[0] in ("npm", "pnpm", "yarn", "bun"):
        return argv[0]
    return "npm"


def run_script(project, name, explicit_cmd, test_cmd, timeout):
    """`--typecheck-cmd`/`--lint-cmd` as given, else the manifest's script
    through the test command's runner, else a skip."""
    if explicit_cmd:
        return run_command(project, explicit_cmd, timeout, f"--{name}-cmd")
    if manifest_script(project, name) is None:
        return {"passed": True, "skipped": True, "reason": f"no {name} script in package.json"}, ""
    return run_command(project, f"{script_runner(test_cmd)} run {name}", timeout, f"--{name}-cmd")


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


def parse_lcov(path, project):
    """Node's lcov report as {project-relative file: {"line": %, "branch": %,
    "uncovered": set of lines, "exact": True}}: `DA:line,hits` gives every
    instrumented line, `BRDA:line,block,branch,taken` every branch (`-` is
    never reached). {} when the file is missing or empty."""
    rows = {}
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return rows
    for record in text.split("end_of_record"):
        lines, uncovered, branches, taken = 0, set(), 0, 0
        name = None
        for entry in record.splitlines():
            if entry.startswith("SF:"):
                name = entry[3:].strip()
            elif entry.startswith("DA:"):
                ln, hits = entry[3:].split(",")[:2]
                lines += 1
                if hits.strip() in ("0", "-"):
                    uncovered.add(int(ln))
            elif entry.startswith("BRDA:"):
                branches += 1
                if entry.split(",")[-1].strip() not in ("0", "-"):
                    taken += 1
        if not name or not lines:
            continue
        rel = os.path.relpath(name, project).replace(os.sep, "/") if os.path.isabs(name) else name.replace(os.sep, "/")
        rows[rel] = {"line": round(100.0 * (lines - len(uncovered)) / lines, 2),
                     "branch": round(100.0 * taken / branches, 2) if branches else 100.0,
                     "uncovered": uncovered, "exact": True}
    return rows


SOURCE = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
TEST_DIRS = {"test", "tests", "__tests__", "spec"}
TEST_NAME = re.compile(r"\.(test|spec)\.[cm]?[jt]sx?$")


def is_test_file(path):
    parts = path.split("/")
    return any(p in TEST_DIRS for p in parts[:-1]) or bool(TEST_NAME.search(parts[-1]))


# ---- report-only metrics: comment density, size, nesting ---------------------

METRIC_SOURCE = SOURCE + (".py",)
LONG_FILE = 300
LONG_FUNCTION = 40
DEEP = 4

STRING_OR_COMMENT = re.compile(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"|`(?:\\.|[^`\\])*`|//.*$|/\*.*?\*/")
JS_FUNCTION = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*(?P<f>[A-Za-z_$][\w$]*)?\s*(?:<[^>]*>)?\s*\("
    r"|^\s*(?:export\s+)?(?:const|let|var)\s+(?P<v>[A-Za-z_$][\w$]*)\s*(?::[^=]*)?=\s*(?:async\s*)?(?:function\b|\([^)]*\)[^=]*=>|[A-Za-z_$][\w$]*\s*=>)"
    r"|^\s*(?:(?:public|private|protected|static|async|override|readonly|get|set)\s+)*\*?(?P<m>[A-Za-z_$][\w$]*)\s*(?:<[^>]*>)?\s*\([^)]*\)\s*(?::[^{;=]*)?\{\s*$")
JS_KEYWORDS = {"if", "for", "while", "switch", "catch", "function", "return", "else", "do", "with"}
PY_FUNCTION = re.compile(r"^(?P<indent>\s*)(?:async\s+)?def\s+(?P<name>\w+)")


def source_lines(project, path):
    try:
        with open(os.path.join(project, path), encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    except OSError:
        return None


def comment_flags(lines, python):
    """One flag per line: is it a comment line? Block comments and Python
    docstrings opened at the start of a statement carry over lines; strings
    are not parsed."""
    flags, in_block, in_doc = [], False, False
    for raw in lines:
        s = raw.strip()
        if python:
            if in_doc:
                flags.append(True)
                if '"""' in s or "'''" in s:
                    in_doc = False
            elif s.startswith(("'''", '"""')):
                flags.append(True)
                quote = s[:3]
                if s.count(quote) == 1:
                    in_doc = True
            else:
                flags.append(s.startswith("#"))
            continue
        if in_block:
            flags.append(True)
            if "*/" in s:
                in_block = False
        elif s.startswith("//"):
            flags.append(True)
        elif s.startswith(("/*", "{/*")):
            flags.append(True)
            in_block = "*/" not in s
        else:
            flags.append(False)
    return flags


def brace_depths(lines):
    """(depth at the start of the line after its leading closers, depth
    after it) per line, braces inside strings and comments stripped line by
    line (a block comment spanning lines is tracked)."""
    out, depth, in_block = [], 0, False
    for raw in lines:
        s = raw
        if in_block:
            end = s.find("*/")
            if end < 0:
                out.append((depth, depth))
                continue
            s, in_block = s[end + 2:], False
        start = s.find("/*")
        while start >= 0:
            end = s.find("*/", start + 2)
            if end < 0:
                s, in_block = s[:start], True
                break
            s = s[:start] + s[end + 2:]
            start = s.find("/*")
        s = STRING_OR_COMMENT.sub(" ", s)
        leading = len(s) - len(s.lstrip(" \t}"))
        closers_first = s[:leading].count("}")
        before = max(0, depth - closers_first)
        depth = max(0, depth + s.count("{") - s.count("}"))
        out.append((before, depth))
    return out


def js_functions(lines, depths):
    """[(name, start, end)] for bodies that open a brace; a header whose
    brace is on a later line opens at that line."""
    found, i = [], 0
    while i < len(lines):
        code = STRING_OR_COMMENT.sub(" ", lines[i])
        m = JS_FUNCTION.match(code)
        name = m and (m.group("f") or m.group("v") or m.group("m"))
        if m and name not in JS_KEYWORDS:
            base = depths[i][0]
            j = i
            # A header without its brace continues only when the line is
            # visibly unfinished (`=>`, an open parameter list); otherwise a
            # one-line arrow function would claim the next block as its body.
            while (j < len(lines) and "{" not in STRING_OR_COMMENT.sub(" ", lines[j]) and j - i < 3
                   and STRING_OR_COMMENT.sub(" ", lines[j]).rstrip().endswith(("=>", ",", "("))):
                j += 1
            if j < len(lines) and "{" in STRING_OR_COMMENT.sub(" ", lines[j]) and depths[j][1] > base:
                k = j
                while k < len(lines) and depths[k][1] > base:
                    k += 1
                found.append((name or "<anonymous>", i + 1, min(k, len(lines) - 1) + 1))
        i += 1
    return found


def py_functions(lines):
    found = []
    for i, line in enumerate(lines):
        m = PY_FUNCTION.match(line)
        if not m:
            continue
        indent = len(m.group("indent").expandtabs(4))
        end = i
        for j in range(i + 1, len(lines)):
            if not lines[j].strip():
                continue
            if len(lines[j][:len(lines[j]) - len(lines[j].lstrip())].expandtabs(4)) <= indent:
                break
            end = j
        found.append((m.group("name"), i + 1, end + 1))
    return found


def py_depths(lines):
    indents = [len(l[:len(l) - len(l.lstrip())].expandtabs(4)) for l in lines if l.strip()]
    unit = min([i for i in indents if i > 0], default=4)
    return [(i // unit, i // unit) for i in (len(l[:len(l) - len(l.lstrip())].expandtabs(4)) for l in lines)]


def file_metrics(path, lines):
    python = path.endswith(".py")
    nonblank = [i for i, l in enumerate(lines) if l.strip()]
    comments = comment_flags(lines, python)
    depths = py_depths(lines) if python else brace_depths(lines)
    functions = py_functions(lines) if python else js_functions(lines, depths)
    return {
        "nonblank": len(nonblank),
        "comment": sum(1 for i in nonblank if comments[i]),
        "deep": sum(1 for i in nonblank if depths[i][0] >= DEEP),
        "max_depth": max((depths[i][0] for i in nonblank), default=0),
        "functions": [(n, e - s + 1) for n, s, e in functions],
    }


def tree_source_files(project, roots):
    files = []
    for root in roots:
        top = os.path.join(project, root.rstrip("/"))
        for dirpath, dirnames, filenames in os.walk(top):
            dirnames[:] = [d for d in dirnames if d not in ("node_modules", ".git", "dist", "build", "coverage", "__pycache__")]
            for name in filenames:
                rel = os.path.relpath(os.path.join(dirpath, name), project).replace(os.sep, "/")
                if rel.endswith(METRIC_SOURCE) and not is_test_file(rel):
                    files.append(rel)
    return sorted(files)


def pct(part, whole):
    return round(100.0 * part / whole, 1) if whole else 0.0


def metrics(project, changed, module_dirs):
    """Comment density and size over the changed source files, plus the
    comment share across `src/` (else the module directories)."""
    sources = [f for f in changed if f.endswith(METRIC_SOURCE) and not is_test_file(f)]
    per_file = {}
    for f in sources:
        lines = source_lines(project, f)
        if lines is not None:
            per_file[f] = file_metrics(f, lines)
    nonblank = sum(m["nonblank"] for m in per_file.values())
    comment = sum(m["comment"] for m in per_file.values())
    deep = sum(m["deep"] for m in per_file.values())
    result = {
        "changed_source_files": sorted(per_file),
        "comment_lines": comment, "nonblank_lines": nonblank, "comment_pct": pct(comment, nonblank),
        "files_over_300": [f for f, m in per_file.items() if m["nonblank"] > LONG_FILE],
        "functions_over_40": [f"{f}:{n} ({ln})" for f, m in per_file.items() for n, ln in m["functions"] if ln > LONG_FUNCTION],
        "deep_lines": deep, "deep_pct": pct(deep, nonblank),
        "max_depth": max((m["max_depth"] for m in per_file.values()), default=0),
    }
    roots = ["src/"] if os.path.isdir(os.path.join(project, "src")) else list(module_dirs)
    if roots:
        tree_nonblank = tree_comment = 0
        for f in tree_source_files(project, roots):
            lines = source_lines(project, f)
            if lines is None:
                continue
            flags = comment_flags(lines, f.endswith(".py"))
            idx = [i for i, l in enumerate(lines) if l.strip()]
            tree_nonblank += len(idx)
            tree_comment += sum(1 for i in idx if flags[i])
        result["tree"] = {"roots": roots, "comment_lines": tree_comment, "nonblank_lines": tree_nonblank,
                          "comment_pct": pct(tree_comment, tree_nonblank)}
    return result


def metric_lines(m):
    if m["changed_source_files"]:
        comments = f"{m['comment_pct']:g}% of non-blank lines in the changed source files ({m['comment_lines']}/{m['nonblank_lines']})"
    else:
        comments = "no changed source files"
    tree = m.get("tree")
    if tree:
        comments += f"; {tree['comment_pct']:g}% across {', '.join(tree['roots'])}"
    size = (f"files over {LONG_FILE} non-blank lines: {json.dumps(m['files_over_300'])}; "
            f"functions over {LONG_FUNCTION} lines: {json.dumps(m['functions_over_40'])}; "
            f"lines at depth >= {DEEP}: {m['deep_pct']:g}% (max {m['max_depth']})")
    return [f"INFO  comments: {comments}", f"INFO  size: {size}"]


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


def check_coverage(output, files, min_line, min_branch, project, lcov_path=None):
    """`files`: the changed files that exist. Node lists every file the tests
    loaded, so a changed source file with no row was never loaded: that is
    zero coverage, not nothing to check. Except a file with no runtime code
    (types only), which nothing can load: exempt, and named as such. For a
    loaded file, uncovered lines that hold no runtime code (erased type
    declarations, counted against the file under transform mode) are taken
    out of both sides of the line percentage. With the lcov report the
    counted lines are known exactly; from the table alone, its own numbers
    give them (`uncovered / (1 - line%)`), unless the `uncovered lines`
    column was truncated, in which case there is no discount and the
    result says so."""
    rows = parse_coverage(output)
    if not rows:
        return {"passed": False, "reason": "no coverage table in the test output", "files": {}}
    for f, exact in (parse_lcov(lcov_path, project) if lcov_path else {}).items():
        rows[f] = exact  # the same files, with every line listed
    runtime = runtime_lines(project, [f for f in files if not is_test_file(f)])
    checked, low, unmeasured, type_only, undiscounted = {}, [], [], [], []
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
        if f in runtime and line < 100:
            if uncovered is None:
                undiscounted.append(f)  # the table's column was cut short
            else:
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
            "not_measured": unmeasured, "type_only": type_only, "undiscounted": undiscounted,
            "exact": bool(lcov_path) and any(r.get("exact") for r in rows.values()),
            "min_line": min_line, "min_branch": min_branch}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", default=".")
    p.add_argument("--base", default="HEAD")
    p.add_argument("--baseline", help="baseline file written by --record-baseline (overrides --base)")
    p.add_argument("--record-baseline", metavar="FILE", help="write the baseline for later runs and exit")
    p.add_argument("--accept-protected", metavar="PATH",
                   help="with --baseline: record this file's current content as the baseline's and exit "
                        "(a protected document the user amended mid-flow)")
    p.add_argument("--allow", action="append", default=[], help="path the change may touch: dir/ or exact file (repeatable)")
    p.add_argument("--module-dir", action="append", default=[],
                   help="a design module directory: a changed file inside it but off --allow is a reported deviation, not a failure (repeatable)")
    p.add_argument("--protect", action="append", default=[], help="file that must be unchanged (repeatable)")
    p.add_argument("--test-cmd", default="npm test")
    p.add_argument("--typecheck-cmd", help="typecheck command; default: package.json's typecheck script through the test command's runner")
    p.add_argument("--lint-cmd", help="lint command; default: package.json's lint script through the test command's runner")
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
    if a.accept_protected:
        if not a.baseline:
            print("--accept-protected needs --baseline")
            return 1
        return accept_protected(project, a.baseline, a.accept_protected.replace("\\", "/"),
                                [p.replace("\\", "/") for p in a.protect])

    baseline, base = None, a.base
    if a.baseline:
        with open(a.baseline, encoding="utf-8") as f:
            baseline = json.load(f)
        base = baseline["base"]
    git(project, "rev-parse", "--verify", "--quiet", base + "^{commit}")

    report = {"base": base, "baseline": a.baseline, "checks": {}}
    outputs = {}
    # The lcov report goes to the temp directory, never into the tree.
    lcov_dir = tempfile.mkdtemp(prefix="kad-gate-") if a.coverage else None
    lcov_path = os.path.join(lcov_dir, "coverage.lcov") if lcov_dir else None
    try:
        report["checks"]["suite"], output = run_tests(project, a.test_cmd, a.coverage, a.timeout, lcov_path)
        outputs["suite"] = output
        for name, explicit in (("typecheck", a.typecheck_cmd), ("lint", a.lint_cmd)):
            report["checks"][name], outputs[name] = run_script(project, name, explicit, a.test_cmd, a.timeout)
        # After the tests, so a test command that edits the tree is seen.
        files = changed_files(project, base, baseline)
        if a.coverage:
            present = [f for f in files if os.path.isfile(os.path.join(project, f))]
            report["checks"]["coverage"] = check_coverage(output, present, a.min_line, a.min_branch,
                                                          project, lcov_path)
    finally:
        if lcov_dir:
            shutil.rmtree(lcov_dir, ignore_errors=True)
    report["checks"]["changes"] = {"passed": bool(files), "count": len(files),
                                   "files": sorted(files)}
    module_dirs = [d.replace("\\", "/") for d in a.module_dir]
    if a.allow:
        report["checks"]["scope"] = check_scope(files, a.allow, module_dirs)
    if a.protect:
        report["checks"]["protected"] = check_protected(project, a.protect, files)
    report["passed"] = all(c["passed"] for c in report["checks"].values())
    report["metrics"] = metrics(project, [f for f in files if os.path.isfile(os.path.join(project, f))], module_dirs)

    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    for name, c in report["checks"].items():
        detail = ""
        if c.get("skipped"):
            print(f"SKIP  {name}: {c['reason']}")
            continue
        if name == "scope" and c["outside"]:
            detail = " outside: " + ", ".join(c["outside"])
        elif name == "scope" and c["deviations"]:
            detail = " deviations: " + json.dumps(c["deviations"])
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
            if c.get("undiscounted"):
                detail += (" (uncovered-lines column truncated, no discount possible: "
                           + ", ".join(c["undiscounted"]) + ")")
        elif name == "suite" and not c["passed"]:
            detail = (f" timed out after {c['timeout']:g}s" if c["timed_out"]
                      else f" exit {c['exit_code']}, summary fail count {c['summary_fail_count']}")
        elif name in ("typecheck", "lint"):
            detail = f" ({c['command']})" if c["passed"] else (
                f" timed out after {c['timeout']:g}s ({c['command']})" if c["timed_out"]
                else f" exit {c['exit_code']} ({c['command']})")
        print(f"{'PASS' if c['passed'] else 'FAIL'}  {name}{detail}")
    for name in ("suite", "typecheck", "lint"):
        if not report["checks"][name]["passed"]:
            tail = "\n".join(outputs[name].splitlines()[-30:])
            print(f"--- {name} output, last 30 lines ---\n" + tail + "\n---")
    for line in metric_lines(report["metrics"]):
        print(line)
    print("validation gate:", "PASS" if report["passed"] else "FAIL")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
