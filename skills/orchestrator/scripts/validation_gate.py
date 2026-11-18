"""Mechanical checks on an implementation change, before any reviewer reads it.

Run inside a project after a chunk (or a fix) has been committed. It
answers eight questions that need no judgment, and prints a JSON verdict so
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
   With the lcov report the same check also reads the **changed lines**:
   of the lines this change added to those files (`git diff -U0` against
   the base; every line of a new file) that hold runtime code, the share
   a test ran must reach `--min-line` too. A file can stay above its
   minimum while thirty new lines in it are never run; this is the
   figure that says so, and the output names the lines.
2b. gate checks: the project's own checks, from `gate-checks.json` at the
   project root (written when `technology-bootstrap`'s gate checks are
   wired; the skill names the eight categories and how a tool is picked
   per stack). The file is `{"checks": [...]}`, one entry per category
   (`CATEGORIES` below), each in one of three forms:
   `{"category", "name", "cmd"}` runs the command the way the test
   command is run and passes on exit 0, for a tool that keeps its own
   baseline (ESLint's suppressions file, a gitleaks baseline);
   `{"category", "name", "cmd", "count": "<regex>", "baseline": <n>}`
   counts violations in the command's output (the number of matches, or,
   when the regex has a group, the number its last match captured) and
   fails only when there are more than `baseline`: the existing code is
   the baseline, a new violation fails, and the tool's own exit code is
   not read except that a non-zero exit with nothing counted is a tool
   that did not run, which fails; `{"category", "covered_by": "suite" |
   "typecheck" | "lint" | "coverage", "note"}` says the category is held
   by a check above (flags in the test script, rules in the linter's
   configuration) and fails if that check did not run;
   `{"category", "not_picked": "<reason>"}` is the owner's recorded
   choice to leave one out. A category with no entry, an unknown
   category, a malformed entry: `FAIL  gate-checks`. No file: one `SKIP`
   line. `--record-gate-baselines` runs every counted check, writes what
   it counted as that entry's `baseline` and exits: the step that takes
   the existing code as the baseline, and the one that lowers it after a
   clean-up (a count under its baseline is an `INFO` line saying so,
   never a failure). The last `INFO  gate covers:` line lists what ran,
   by category: the chunk reviewer reads it and reports none of it.
3. changes: the change set is not empty. A build that changed nothing is
   not an implementation, whatever the suite says.
4. scope: every file changed since the baseline is inside one of the
   `--allow` entries: an entry ending in `/` allows everything under that
   directory, any other entry allows exactly that file. A changed file on
   no `--allow` entry but inside a `--module-dir` (repeatable; the design's
   module directories) is a **deviation**: the chunk plan did not name it,
   the design's structure does, so it is listed on the `scope` line and in
   the JSON (`scope.deviations`) for the orchestrator's C line, and the
   check still passes; the builder's report names why. Two more kinds of
   change are deviations, never failures: a test source file (a `.ts`,
   `.js` or `.py` file under `test/`, `tests/`, `__tests__/` or `spec/`,
   or named `*.test.*`/`*.spec.*`; a `test/config.json` is not one and
   stays outside) the Files line did not name, since a builder that adds
   a test it needs is doing its job; and a file under a `--deviation-zone` entry (repeatable;
   the design's composition root and entry points, `src/compose.ts`,
   `src/main.ts`, `src/start.ts` or their equivalents, which almost every
   chunk wires into). The flow's own records are never in question:
   `orchestrator-log.md` directly in the target directory (`--planning`,
   or `planning/` under the project), and a rounds sidecar
   (`rounds-<anything>.jsonl`) anywhere under it, are the orchestrator's,
   appended to at every step and committed outside the chunk, so they are
   in scope whether or not an `--allow` names them (listed in the JSON as
   `scope.records`). A file of either name anywhere else is judged like
   any other file.
   A changed file under none of these is `outside` and
   fails the check: that is the one the fixer moves. Untracked files
   count as changed; so do both sides of a rename. Claude Code's own
   placeholders are not: an untracked path under a `.claude/` directory,
   or named `.mcp.json`, that is not a regular file with content (the
   `Agent` tool keeps worktree-isolated agents' trees under
   `.claude/worktrees/` inside the real project, and the session's sandbox
   mounts empty placeholder settings into every directory a command runs
   from, both of which git lists as untracked). A settings file a
   change that actually wrote one there has content and stays in the set.
5. protected: every `--protect` file is byte-identical to the baseline.
6. tests: with `--expect-tests-from <report> --chunk <k>` (the names quoted
   on that chunk's Done when line, read from the implementation report so
   plan text never crosses a shell command line; `--expect-test <name>`
   adds one by hand), every name
   is registered in some test file: the title of a `test(`, `it(` or
   `describe(` call, or a `def <name>(`, never a mention in a comment or
   a fixture. A Done-when test a fix renamed or dropped (a mangled
   seam-test name, run 3's chunk 8) fails here, at the gate. What counts
   as a name on the Done when line: a double-quoted string, or a
   backticked string with whitespace in it; a backticked single word
   (`POST`, `npm test`'s `test`) is a word of the prose, never a test
   name. Both sides are compared after NFC normalisation, case folded,
   whitespace folded, with a `seam "…"` wrapper stripped from either side
   (a builder that titled its test `seam "cancels…"` and a plan that
   wrote `seam "cancels…"` name the same test). Slice 2 failed this check
   three times on exactly those three shapes.
7. sources: when the planning directory (`--planning <target directory>`;
   without the flag, `planning/` under the project) has a `sources.md`,
   the files the owner provided by location, no changed file holds a
   value of one of them. `source_scan.py` beside this script reads each
   source where it is and looks for its text and numeric cells in the
   files this change touched; its docstring says what is matched, what is
   not, and what is matched and not counted. The `FAIL` line names the
   files, `hit:` lines the line, column span and cell of each place, and
   `INFO  sources:` lines what was read and not counted: never a value,
   since this output is saved in the records directory and committed. A
   listed source that cannot be read fails too (`not readable`): a scan
   that could not run is not a pass, and no fixer can mend it. No
   `sources.md`: a `SKIP` line. Slice 2's builders inherited a real
   merchant and its fee from the plan and wrote them into thirteen test
   files; the security reviewer found them at D, two and a half hours
   after the first commit.
8. transcript (report-only, with `--agent-transcript <path>` or `--agent
   <id>`): the builder's or fixer's own transcript, replayed. Counts the
   **shell edits**: every Bash command that wrote a file inside the tree
   (`>` and `>>` redirections, `tee`, `sed -i`, `perl -i`, `cp`, `mv`,
   `rm` on a tracked file, and a `python3 -`/`python3 -c`/`node -e`
   script that opens a path for writing), one per file per command;
   plus, as the catch-all, every tracked file that changed between the
   agent's first and last commit on the branch without an `Edit` or
   `Write` call naming it. A formatter run (`prettier --write`, `eslint
   --fix`, the manifest's `format` script through its runner) is not a
   shell edit, and a write outside the tree (the scratchpad) is not one.
   Prints `shell edits <n> (reported <m>)`, `m` being the number the
   agent's own hand-back claimed (`shell edits <m>` in its last message,
   `?` when it claimed none), and one `shell edit: <file> (<command>)`
   line per count. Then the **commit rule**: a Bash command that runs
   `git commit` in the same command line as the test command (`npm test
   … && git commit`, `test | grep … && commit`) is printed as `commit
   chained to its test run: <sha>`; when the command's recorded output
   shows a failing summary (`ℹ fail <n>`, n > 0), `committed on a red
   run: <sha> (fail <n>)`. Slice 2's chunk 2 builder reported 1 shell
   edit and made 9; its chunk 4 builder committed on a red run through a
   grep chain and reported green. Neither fails the gate (the suite check
   judges the tree as it is); both reach the C line. When `sources.md`
   lists a source, one more line: `source values <n> in <m> entries` of
   the agent's transcript (an agent that opened the owner's file has its
   cells in its tool results, whatever it then wrote); a transcript that
   holds one is a copy the owner decides about, and the audit sync
   withholds it.

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
`tdd-implementation-lite-*` eval cases prove with trace regexes; this is the
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
           [--record-gate-baselines]
           [--planning DIR] [--agent-transcript PATH | --agent ID [--projects-dir DIR] [--session ID]]
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


def project_relative(project, path):
    """A path handed on the command line as the gate compares it: relative
    to the project, `/`-separated, its trailing `/` kept. An absolute path
    inside the project is read as the path relative to it (a runner once
    passed the records directory as it was handed, absolute, and the gate
    failed scope on the run's own records); one outside the project is left
    as it is and matches nothing."""
    text = path.replace("\\", "/")
    if not os.path.isabs(path):
        return text
    try:
        rel = os.path.relpath(os.path.realpath(path), os.path.realpath(project))
    except ValueError:  # another drive on Windows
        return text
    if rel == os.curdir or rel == os.pardir or rel.startswith(os.pardir + os.sep):
        return text
    rel = rel.replace(os.sep, "/")
    return rel + "/" if text.endswith("/") else rel


def allowed(path, entry):
    return path.startswith(entry) if entry.endswith("/") else path == entry


def under(path, directory):
    return path.startswith(directory.rstrip("/") + "/")


SIDECAR = re.compile(r"rounds-[\w.-]+\.jsonl$")


def flow_record(path, planning):
    """Is this the flow's own log (directly in the target directory) or a
    rounds sidecar (anywhere under it)? `planning` is the target directory
    relative to the project, `/`-separated."""
    if not planning or planning.startswith(".."):
        return False
    root = "" if planning in (".", "") else planning.rstrip("/") + "/"
    if not path.startswith(root):
        return False
    inside = path[len(root):]
    return inside == "orchestrator-log.md" or bool(SIDECAR.fullmatch(inside.rsplit("/", 1)[-1]))


def check_scope(files, allow, module_dirs=(), zones=(), planning=None):
    """Three-way: on an `--allow` entry, fine; off the list but inside a
    `--module-dir`, a test file, or under a `--deviation-zone` entry, a
    deviation the chunk plan did not foresee (reported, not failed); under
    none of these, outside the slice, which fails. The flow's own log and
    sidecar, inside the target directory, are in scope without an `--allow`."""
    records = [f for f in files if flow_record(f, planning) and not any(allowed(f, e) for e in allow)]
    unlisted = [f for f in files if f not in records and not any(allowed(f, e) for e in allow)]
    deviations = [f for f in unlisted
                  if any(under(f, d) for d in module_dirs)
                  or (is_test_file(f) and f.endswith(METRIC_SOURCE))
                  or any(allowed(f, z) for z in zones)]
    outside = [f for f in unlisted if f not in deviations]
    return {"passed": not outside, "changed": files, "deviations": deviations, "outside": outside,
            "records": records}


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


# ---- the project's own gate checks (gate-checks.json) ------------------------

GATE_CHECKS_FILE = "gate-checks.json"
CATEGORIES = ("type-aware lint", "stricter compiler flags", "complexity and length limits", "duplication",
              "unused code", "changed-line coverage", "test timeouts and random order",
              "secret and workflow scans")
COVERED_BY = ("suite", "typecheck", "lint", "coverage")
CHECK_NAME = re.compile(r"[a-z0-9][a-z0-9-]*$")


def load_gate_checks(project):
    """(entries, problems) from the project's `gate-checks.json`, or (None,
    []) when there is none. Every problem is a sentence for the FAIL line:
    the file is the owner's approved set, so a category it does not hold
    is a gap in the gate, not a default."""
    path = os.path.join(project, GATE_CHECKS_FILE)
    if not os.path.isfile(path):
        return None, []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        return [], [f"{GATE_CHECKS_FILE} cannot be read as JSON ({e})"]
    entries = data.get("checks") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return [], [f'{GATE_CHECKS_FILE} holds no "checks" list']
    problems, names, seen = [], set(), set()
    for i, e in enumerate(entries, 1):
        if not isinstance(e, dict):
            problems.append(f"entry {i} is not an object")
            continue
        category = e.get("category")
        if category not in CATEGORIES:
            problems.append(f"entry {i}: unknown category {category!r}")
            continue
        seen.add(category)
        forms = [k for k in ("cmd", "covered_by", "not_picked") if k in e]
        if len(forms) != 1:
            problems.append(f"{category}: one of cmd, covered_by or not_picked, not {len(forms)}")
            continue
        if "cmd" in e:
            name = e.get("name")
            if not isinstance(name, str) or not CHECK_NAME.match(name) or name in names:
                problems.append(f"{category}: a cmd entry needs its own name (lowercase, digits, hyphens), got {name!r}")
            names.add(name)
            if not isinstance(e["cmd"], str) or not e["cmd"].strip():
                problems.append(f"{category}: cmd is empty")
            if "count" in e:
                try:
                    re.compile(e["count"])
                except (re.error, TypeError) as err:
                    problems.append(f"{category}: count is not a regular expression ({err})")
                base = e.get("baseline", 0)
                if isinstance(base, bool) or not isinstance(base, int) or base < 0:
                    problems.append(f"{category}: baseline must be a whole number, got {base!r}")
            elif "baseline" in e:
                problems.append(f"{category}: a baseline needs a count regex to compare with")
        elif "covered_by" in e and e["covered_by"] not in COVERED_BY:
            problems.append(f"{category}: covered_by must be one of {', '.join(COVERED_BY)}")
        elif "not_picked" in e and not (isinstance(e["not_picked"], str) and e["not_picked"].strip()):
            problems.append(f"{category}: not_picked needs its reason")
    problems += [f"no entry for the category {c!r}" for c in CATEGORIES if c not in seen]
    return entries, problems


def count_violations(pattern, output):
    """The number a `count` regex reads from a check's output: with a group,
    the integer its last match captured (None when nothing matched, or the
    capture is not a number); without one, how many times it matched."""
    rx = re.compile(pattern, re.M)
    if not rx.groups:
        return len(rx.findall(output))
    last = None
    for m in rx.finditer(output):
        last = m
    if last is None:
        return None
    try:
        return int(next(g for g in last.groups() if g is not None))
    except (StopIteration, ValueError):
        return None


def run_gate_check(project, entry, timeout):
    """One `cmd` entry: (result, output). Never raises: a tool that is not
    installed is this check's failure, not the gate's crash."""
    cmd = entry["cmd"]
    result = {"category": entry["category"], "command": cmd}
    try:
        ran, out = run_command(project, cmd, timeout, "gate-checks.json")
    except SystemExit as e:
        return {**result, "passed": False, "reason": str(e).splitlines()[0].replace("FAIL  ", "")}, ""
    result.update(exit_code=ran["exit_code"], timed_out=ran["timed_out"])
    if ran["timed_out"]:
        return {**result, "passed": False, "reason": f"timed out after {timeout:g}s"}, out
    if "count" not in entry:
        return {**result, "passed": ran["passed"]}, out
    baseline = entry.get("baseline", 0)
    found = count_violations(entry["count"], out)
    result.update(found=found, baseline=baseline)
    if found is None:
        return {**result, "passed": False, "reason": f"no count read from its output (exit {ran['exit_code']})"}, out
    if found == 0 and ran["exit_code"] != 0 and not re.compile(entry["count"]).groups:
        return {**result, "passed": False,
                "reason": f"exit {ran['exit_code']} and nothing counted: the tool did not run"}, out
    return {**result, "passed": found <= baseline}, out


def run_gate_checks(project, entries, checks, timeout):
    """Every entry of the file against the checks already run (`checks`, the
    report's own dict, for `covered_by`). Returns ({key: result}, {key:
    output}, the categories the gate held on this run)."""
    results, outputs, covered = {}, {}, []
    for e in entries:
        category = e["category"]
        if "cmd" in e:
            key = "check:" + e["name"]
            results[key], outputs[key] = run_gate_check(project, e, timeout)
            covered.append(category)
        elif "covered_by" in e:
            by = checks.get(e["covered_by"])
            ran = bool(by) and not by.get("skipped")
            results["covered:" + category] = {
                "category": category, "covered_by": e["covered_by"], "note": e.get("note", ""), "passed": ran,
                **({} if ran else {"reason": f"the {e['covered_by']} check did not run"})}
            if ran:
                covered.append(category)
        else:
            results["not-picked:" + category] = {"category": category, "passed": True, "skipped": True,
                                                 "reason": f"not picked: {e['not_picked']}"}
    return results, outputs, covered


def record_gate_baselines(project, timeout):
    """`--record-gate-baselines`: every counted check run once, its count
    written as its baseline. The file is rewritten whole through a
    sibling, with the entries in the order they were in."""
    entries, problems = load_gate_checks(project)
    if entries is None:
        print(f"no {GATE_CHECKS_FILE} in {project}")
        return 1
    if problems:
        for p in problems:
            print(f"FAIL  gate-checks: {p}")
        return 1
    failed = False
    for e in entries:
        if "cmd" not in e or "count" not in e:
            continue
        probe = dict(e, baseline=10 ** 9)
        r, _ = run_gate_check(project, probe, timeout)
        if not r["passed"]:
            print(f"FAIL  check {e['name']} [{e['category']}]: {r['reason']} ({e['cmd']})")
            failed = True
            continue
        print(f"baseline {e['name']} [{e['category']}]: {e.get('baseline', 0)} -> {r['found']}")
        e["baseline"] = r["found"]
    if failed:
        print("gate baselines: not recorded")
        return 1
    path = os.path.join(project, GATE_CHECKS_FILE)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data["checks"] = entries
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)
    print("gate baselines: recorded")
    return 0


def script_line(name, c):
    """The printed line of the typecheck or the lint."""
    if c.get("skipped"):
        return f"SKIP  {name}: {c['reason']}"
    detail = f" ({c['command']})" if c["passed"] else (
        f" timed out after {c['timeout']:g}s ({c['command']})" if c["timed_out"]
        else f" exit {c['exit_code']} ({c['command']})")
    return f"{'PASS' if c['passed'] else 'FAIL'}  {name}{detail}"


def checks_only(project, a):
    """`--checks-only`: the typecheck, the lint and every command of
    `gate-checks.json`, and nothing else (no suite, no scope, no
    transcript). What a builder or a fixer runs before it commits, so a
    count one over its baseline is its own to clear and not a gate fixer's:
    on one slice a gate fixer ran after five builds of six, and wrote a
    sixth of the lines the slice added. The last line is `checks: PASS` or
    `checks: FAIL`; a category the file leaves to the suite or the coverage
    is named as left to the gate."""
    checks, outputs = {}, {}
    for name, explicit in (("typecheck", a.typecheck_cmd), ("lint", a.lint_cmd)):
        checks[name], outputs[name] = run_script(project, name, explicit, a.test_cmd, a.timeout)
        print(script_line(name, checks[name]))
    entries, problems = load_gate_checks(project)
    if entries is None:
        print(f"SKIP  gate-checks: no {GATE_CHECKS_FILE} in the project")
    elif problems:
        checks["gate-checks"] = {"passed": False}
        print("FAIL  gate-checks: " + "; ".join(problems))
    else:
        for e in entries:
            if "cmd" in e:
                key = "check:" + e["name"]
                checks[key], outputs[key] = run_gate_check(project, e, a.timeout)
                print(gate_check_line(key, checks[key]))
            elif "covered_by" in e:
                print(f"INFO  {e['category']}: left to the gate's {e['covered_by']} check")
    for name, c in checks.items():
        if not c["passed"] and outputs.get(name):
            print(f"--- {name} output, last 30 lines ---\n" + "\n".join(outputs[name].splitlines()[-30:]) + "\n---")
    passed = all(c["passed"] for c in checks.values())
    print("checks:", "PASS" if passed else "FAIL")
    return 0 if passed else 1


def gate_check_line(key, c):
    """The printed line of one gate-checks result."""
    category = c["category"]
    if key.startswith("covered:"):
        note = f" ({c['note']})" if c.get("note") else ""
        return (f"PASS  {category}: covered by {c['covered_by']}{note}" if c["passed"]
                else f"FAIL  {category}: {c['reason']}, and {GATE_CHECKS_FILE} says it covers this")
    name = key.split(":", 1)[1]
    if c.get("reason"):
        return f"FAIL  check {name} [{category}]: {c['reason']} ({c['command']})"
    if "found" in c:
        verdict = "PASS" if c["passed"] else "FAIL"
        return f"{verdict}  check {name} [{category}]: {c['found']} found, baseline {c['baseline']} ({c['command']})"
    return (f"PASS  check {name} [{category}]: exit 0 ({c['command']})" if c["passed"]
            else f"FAIL  check {name} [{category}]: exit {c['exit_code']} ({c['command']})")


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
        instrumented = set()
        name = None
        for entry in record.splitlines():
            if entry.startswith("SF:"):
                name = entry[3:].strip()
            elif entry.startswith("DA:"):
                ln, hits = entry[3:].split(",")[:2]
                lines += 1
                instrumented.add(int(ln))
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
                     "uncovered": uncovered, "instrumented": instrumented, "exact": True}
    return rows


HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", re.M)


def added_lines(project, base, files):
    """{file: set of 1-based lines this change added or rewrote}: the `+`
    side of `git diff -U0 <base>` for a tracked file, every line of an
    untracked one. A file git cannot diff is left out."""
    out = {}
    try:
        untracked = set(git(project, "ls-files", "--others", "--exclude-standard").stdout.splitlines())
    except SystemExit:
        untracked = set()
    for f in files:
        if f in untracked:
            lines = source_lines(project, f)
            if lines is not None:
                out[f] = set(range(1, len(lines) + 1))
            continue
        # An argument list and no shell: `base` and `f` reach git as single arguments, after `--` for the path.
        proc = subprocess.run([find_git(), "diff", "-U0", "--no-renames", base, "--", f], cwd=project,  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
                              capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode != 0:
            continue
        added = set()
        for start, count in HUNK.findall(proc.stdout):
            added.update(range(int(start), int(start) + int(count or 1)))
        out[f] = added
    return out


def changed_line_coverage(rows, runtime, added, files, min_line):
    """The changed-lines figure of docstring point 2: over the source files
    of the change that the lcov report lists, the added lines Node
    instrumented (and, where the helper answered, that hold runtime
    code), and which of them no test ran. None when no file has exact
    data or the change added no such line."""
    instrumented = uncovered = 0
    per_file = {}
    for f in files:
        row = rows.get(f)
        if not row or not row.get("exact") or f not in added:
            continue
        lines = added[f] & row["instrumented"]
        if f in runtime:
            lines &= runtime[f]
        missed = sorted(lines & row["uncovered"])
        instrumented += len(lines)
        uncovered += len(missed)
        if missed:
            per_file[f] = missed
    if not instrumented:
        return None
    line = round(100.0 * (instrumented - uncovered) / instrumented, 2)
    return {"passed": line >= min_line, "instrumented": instrumented, "uncovered": uncovered, "line": line,
            "files": per_file}


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


TEST_NAME_LIMIT = 2 * 1024 * 1024  # bytes of a test file read for registered names


def test_key(name):
    """A test title as the gate compares it: NFC-normalised, case folded,
    whitespace folded, surrounding quotes and a `seam "…"`/`seam …`
    wrapper stripped. The same function runs over the plan's name and the
    registered title, so either side may carry the wrapper or differ in
    case or encoding (slice 2's three false FAILs)."""
    import unicodedata
    n = unicodedata.normalize("NFC", name).strip()
    n = re.sub(r"^\s*seam\s*:?\s*", "", n, flags=re.I)
    n = n.strip().strip("\"'`“”‘’").strip()
    return re.sub(r"\s+", " ", n).casefold()


TITLE_CALLS = re.compile(r"\b(?:test|it|describe)\s*\(\s*(['\"`])((?:\\.|(?!\1).)*)\1", re.S)
PY_DEFS = re.compile(r"\bdef\s+(\w+)\s*\(")


def registered_titles(text):
    """Every title registered in a test file: `test(`, `it(` and `describe(`
    call titles (JS/TS; a template literal is taken as written) and
    `def <name>(` names (Python), as comparison keys."""
    keys = {test_key(m.group(2).replace("\\'", "'").replace('\\"', '"')) for m in TITLE_CALLS.finditer(text)}
    keys |= {test_key(m.group(1)) for m in PY_DEFS.finditer(text)}
    return keys


def registered(name, text):
    """Is `name` a registered test in this file: the title of a `test(`, `it(` or
    `describe(` call (JS/TS), or a `def <name>(` (Python)? A mention in a
    comment, a fixture or another test's title does not count. Compared
    through `test_key` on both sides."""
    return test_key(name) in registered_titles(text)


DONE_WHEN_QUOTED = re.compile(r'"([^"\n]+)"|`([^`\n]+)`')


RENAMED_TEST = re.compile(r"renamed test\s+[\"“`](.+?)[\"”`]\s*(?:→|->)\s*[\"“`](.+?)[\"”`]")


def done_when_names(line):
    """The test names a Done when line quotes: every double-quoted string,
    and a backticked string that holds whitespace. A backticked single
    word (`POST`, `npm`) is prose, never a test name; the `seam` word
    before a quote is the plan's marker, not part of the name."""
    names = []
    for a, b in DONE_WHEN_QUOTED.findall(line):
        if a:
            names.append(a)
        elif b and re.search(r"\s", b.strip()):
            names.append(b)
    return [n for n in names if test_key(n)]


def done_when_tests(report_path, chunk):
    """The test names quoted on the chunk plan's Done when line for chunk <k>
    (double quotes, or backticks around more than one word), read from the
    implementation report so no plan text ever passes through a shell
    command line."""
    try:
        with open(report_path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as e:
        raise SystemExit(f"--expect-tests-from: cannot read {report_path}: {e.strerror}")
    section = re.search(r"^###\s+Chunk\s+" + re.escape(str(chunk)) + r"\b[^\n]*\n(.*?)(?=^###\s|\Z)", text, re.M | re.S)
    if not section:
        raise SystemExit(f"--expect-tests-from: no `### Chunk {chunk}` section in {report_path}")
    line = re.search(r"^\s*[-*]\s*\*\*Done when\*\*\s*:?\s*(.+)$", section.group(1), re.M)
    if not line:
        raise SystemExit(f"--expect-tests-from: chunk {chunk} has no Done when line in {report_path}")
    names = done_when_names(line.group(1))
    # A fix that changes what a test checks renames it, and says so on its
    # `Fix` line: `renamed test "<old>" → "<new>"`. The plan's name is then
    # the old one, and the test the gate looks for is the new one. Without
    # this a fixer either left a title that no longer said what the test
    # did, or renamed it and failed the gate.
    renames = {test_key(old): new for old, new in RENAMED_TEST.findall(text) if test_key(old) and test_key(new)}
    out = []
    for name in names:
        seen = set()
        while test_key(name) in renames and test_key(name) not in seen:
            seen.add(test_key(name))
            name = renames[test_key(name)]
        out.append(name)
    return out


def check_expected_tests(project, names):
    """Every `--expect-test` name is registered in some test file of the tree.
    A Done-when test that a fix renamed or dropped fails here, at the gate,
    not three rounds later. Symlinks and non-regular files are skipped and a
    file is read up to TEST_NAME_LIMIT bytes."""
    found = set()
    for dirpath, dirnames, filenames in os.walk(project):
        dirnames[:] = [d for d in dirnames if d not in SKIP_WALK and not d.startswith(".")]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, project).replace("\\", "/")
            if not is_test_file(rel) or os.path.islink(full) or not os.path.isfile(full):
                continue
            try:
                with open(full, encoding="utf-8", errors="replace") as fh:
                    text = fh.read(TEST_NAME_LIMIT)
            except OSError:
                continue
            titles = registered_titles(text)
            for n in names:
                if n not in found and test_key(n) in titles:
                    found.add(n)
    missing = [n for n in names if n not in found]
    return {"passed": not missing, "names": list(names), "missing": missing}


# ---- the agent's transcript: shell edits and the commit rule -----------------

FORMATTER = re.compile(r"\b(?:prettier\b[^|;&\n]*\s(?:--write|-w)\b|eslint\b[^|;&\n]*--fix\b|(?:npm|pnpm|yarn|bun)\s+run\s+format\b|"
                       r"corepack\s+pnpm\s+run\s+format\b|gofmt\s+-w\b|black\s|ruff\s+format\b)")
REDIRECT = re.compile(r"(?<![0-9&<>=\-])>{1,2}\s*(?!&)([^\s;&|)`'\"]+|'[^']+'|\"[^\"]+\")")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n")
INPLACE = re.compile(r"\b(?:sed|gsed)\s+(?:-[a-zA-Z]*i\S*|--in-place\S*)|\bperl\s+-[a-zA-Z]*i\S*|\bawk\s+-i\b")
SCRIPT_WRITE = re.compile(r"\bopen\s*\(\s*[^)]*,\s*['\"][wax]b?\+?['\"]|\.write_text\(|\.write_bytes\(|writeFileSync\(|writeFile\(|appendFileSync\(|appendFile\(|fs\.promises\.writeFile")
PATH_LITERAL = re.compile(r"^\s*(?:const|let|var)?\s*\w+\s*=\s*['\"]([^'\"\n]+)['\"]\s*;?\s*$|\bopen\s*\(\s*['\"]([^'\"\n]+)['\"]|write(?:File(?:Sync)?|_text|_bytes)\s*\(\s*['\"]([^'\"\n]+)['\"]", re.M)
TEST_CMDS = re.compile(r"\b(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?test\b|\bnode\s+[^|;&\n]*--test\b|\bpytest\b|\bvitest\b|\bjest\b|\bcorepack\s+pnpm\s+test\b")
SHA_LINE = re.compile(r"^\s*([0-9a-f]{7,40})\s*$", re.M)
REPORTED = re.compile(r"shell edits?\W{0,6}(\d+)", re.I)


def tool_calls_of(path):
    """(calls, results, last_text) of one agent transcript: each tool_use once
    by id (the audit hook records every Bash call twice, once with a `cd`
    prefix), the tool_result text by tool_use id, and the agent's last
    text (its hand-back)."""
    calls, results, last_text = [], {}, ""
    seen = set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            content = (row.get("message") or {}).get("content") or []
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if row.get("type") == "assistant" and block.get("type") == "tool_use" and block.get("id") not in seen:
                    seen.add(block.get("id"))
                    calls.append(block)
                    if block.get("name") == "SubagentHandback":
                        text = json.dumps(block.get("input") or {})
                        last_text = text
                elif row.get("type") == "assistant" and block.get("type") == "text" and block.get("text", "").strip():
                    last_text = block["text"]
                elif row.get("type") == "user" and block.get("type") == "tool_result":
                    c = block.get("content")
                    if isinstance(c, list):
                        c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
                    results[block.get("tool_use_id")] = c or ""
    return calls, results, last_text


def split_heredocs(command):
    """(the command text with heredoc bodies removed, [body, ...])."""
    bodies, out, i = [], [], 0
    lines = command.split("\n")
    while i < len(lines):
        line = lines[i]
        m = HEREDOC.search(line + "\n")
        out.append(line)
        i += 1
        if m:
            delim, body = m.group(2), []
            while i < len(lines) and lines[i].strip() != delim:
                body.append(lines[i])
                i += 1
            i += 1  # the delimiter line
            bodies.append("\n".join(body))
    return "\n".join(out), bodies


def tree_path(project, token, tracked):
    """The project-relative path a shell token names, when it is inside the
    tree (relative, or absolute under the project); None for the
    scratchpad, /dev/null, a variable or a flag."""
    token = token.strip().strip("'\"")
    if not token or token.startswith(("-", "$", "/dev/")) or "$(" in token:
        return None
    full = token if os.path.isabs(token) else os.path.join(project, token)
    try:
        rel = os.path.relpath(os.path.abspath(full), project).replace(os.sep, "/")
    except ValueError:
        return None
    if rel.startswith("..") or rel in (".", ""):
        return None
    if rel.split("/")[0] in SKIP_WALK or rel.endswith((".bak", ".tmp", ".orig", "~")):
        return None
    if tracked is not None and rel not in tracked and not os.path.isfile(os.path.join(project, rel)):
        return None  # a path that never existed in the tree
    return rel


def shell_writes(project, command, tracked):
    """The tree files one Bash command wrote through the shell, distinct, or
    [] when the command is a formatter run or writes nothing."""
    text, bodies = split_heredocs(command)
    files = set()
    for segment in re.split(r"&&|\|\||;|\n", text):
        if FORMATTER.search(segment):
            continue
        for m in REDIRECT.finditer(segment):
            rel = tree_path(project, m.group(1), tracked)
            if rel:
                files.add(rel)
        if INPLACE.search(segment):
            for tok in re.findall(r"(?<=\s)(?!-)[\w./@-]+\.[A-Za-z0-9]+(?=\s|$)", segment):
                rel = tree_path(project, tok, tracked)
                if rel:
                    files.add(rel)
        m = re.match(r"\s*(?:cp|mv)\s+(?:-\w+\s+)*(?:\S+\s+)+(\S+)\s*$", segment)
        if m:
            rel = tree_path(project, m.group(1), tracked)
            if rel:
                files.add(rel)
        m = re.match(r"\s*rm\s+(?:-\w+\s+)*(.+)$", segment)
        if m:
            for tok in m.group(1).split():
                rel = tree_path(project, tok, tracked)
                if rel and tracked is not None and rel in tracked:
                    files.add(rel)
        m = re.search(r"\b(?:python3?|node)\s+-[ce]\s+(['\"])(.*)\1", segment, re.S)
        if m:
            bodies.append(m.group(2))
    for body in bodies:
        if not SCRIPT_WRITE.search(body):
            continue
        for m in PATH_LITERAL.finditer(body):
            rel = tree_path(project, m.group(1) or m.group(2) or m.group(3) or "", tracked)
            if rel and ("/" in rel or "." in rel):
                files.add(rel)
    return sorted(files)


def source_scanner():
    """`source_scan.py`, beside this script; `-I` leaves the script's own
    directory off `sys.path`."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import source_scan
    return source_scan


def check_sources(project, planning, files):
    """(check, catalog): docstring point 7. Nothing in the check holds a
    value of a source."""
    scan = source_scanner()
    planning = os.path.abspath(planning) if planning else os.path.join(project, "planning")
    cat = scan.load(planning, project)
    if cat is None:
        where = os.path.relpath(planning, project).replace(os.sep, "/")
        return {"passed": True, "skipped": True, "reason": f"no sources.md under {where}"}, None
    found, scanned = scan.scan_tree(cat, project, planning, only=files)
    hits, not_counted = cat.judge(found)
    by = scan.by_file(hits)
    return {"passed": not hits and not cat.problems, "scanned": scanned, "hits": scan.public(hits),
            "files": {name: len(h) for name, h in by.items()}, "problems": list(cat.problems),
            "lines": scan.hit_lines(hits), "info": scan.exclusion_lines(cat, not_counted)}, cat


def check_transcript(project, path, base, test_cmd, catalog=None):
    """The report-only replay of one agent transcript (docstring point 8)."""
    calls, results, last_text = tool_calls_of(path)
    try:
        tracked = set(git(project, "ls-files").stdout.splitlines())
    except SystemExit:
        tracked = None
    edits, named = [], set()
    for call in calls:
        name, inp = call.get("name"), call.get("input") or {}
        if name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
            fp = inp.get("file_path") or inp.get("path") or inp.get("notebook_path") or ""
            rel = tree_path(project, fp, None)
            if rel:
                named.add(rel)
        elif name == "Bash":
            cmd = inp.get("command") or ""
            for rel in shell_writes(project, cmd, tracked):
                head = cmd.strip().split("\n")[0]
                edits.append((rel, head[:60] + ("…" if len(head) > 60 else "")))
    counted = {rel for rel, _ in edits}
    catch_all = []
    if base and base != "HEAD":
        try:
            changed = git(project, "diff", "--name-only", f"{base}..HEAD").stdout.splitlines()
        except SystemExit:
            changed = []
        catch_all = [f for f in changed if f and f not in named and f not in counted]
    m = REPORTED.search(last_text or "")
    reported = m.group(1) if m else "?"
    commits = []
    for call in calls:
        if call.get("name") != "Bash":
            continue
        cmd = (call.get("input") or {}).get("command") or ""
        text, _ = split_heredocs(cmd)
        if not re.search(r"\bgit\s+commit\b", text):
            continue
        chained = bool(TEST_CMDS.search(text) or (test_cmd and test_cmd.strip() in text))
        out = results.get(call.get("id"), "")
        fails = re.findall(r"ℹ fail (\d+)", out)
        sha_m = SHA_LINE.search(out)
        sha = sha_m.group(1)[:7] if sha_m else "sha unknown"
        red = fails and fails[-1] != "0"
        if chained or red:
            commits.append({"sha": sha, "chained": chained, "red": bool(red), "fail": fails[-1] if fails else None,
                            "command": text.strip().split("\n")[0][:80]})
    source_values = None
    if catalog is not None:
        counted, entries = source_scanner().scan_transcript(catalog, path)
        source_values = {"hits": len(counted), "entries": entries} if counted is not None else {"unreadable": True}
    return {"passed": True, "report_only": True, "transcript": path, "shell_edits": len(edits) + len(catch_all),
            "edits": edits, "catch_all": catch_all, "reported": reported, "commits": commits,
            "source_values": source_values}


def transcript_lines(c):
    lines = [f"INFO  transcript: shell edits {c['shell_edits']} (reported {c['reported']})"]
    for rel, head in c["edits"]:
        lines.append(f"INFO  shell edit: {rel} ({head})")
    for rel in c["catch_all"]:
        lines.append(f"INFO  shell edit: {rel} (changed in the range with no Edit or Write naming it)")
    for k in c["commits"]:
        if k["red"]:
            lines.append(f"INFO  committed on a red run: {k['sha']} (fail {k['fail']}; {k['command']})")
        else:
            lines.append(f"INFO  commit chained to its test run: {k['sha']} ({k['command']})")
    sv = c.get("source_values")
    if sv and sv.get("unreadable"):
        lines.append("INFO  transcript: could not be read for source values; not a clean transcript")
    elif sv and sv["hits"]:
        lines.append(f"INFO  transcript: source values {sv['hits']} in {sv['entries']} entries of the agent's transcript; "
                     "a copy the owner decides about")
    elif sv:
        lines.append("INFO  transcript: no value of a listed source in the agent's transcript")
    return lines


def agent_transcript_path(agent_id, project, projects_dir, session):
    """`<projects dir>/<project key>/<session>/subagents/agent-<id>.jsonl`, the
    file Claude Code writes for a subagent of this session."""
    key = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(project))
    aid = agent_id if agent_id.startswith("agent-") else f"agent-{agent_id}"
    if not aid.endswith(".jsonl"):
        aid += ".jsonl"
    return os.path.join(projects_dir, key, session or "", "subagents", aid)


SKIP_WALK = {"node_modules", "dist", "build", "coverage", "__pycache__", ".venv", "venv"}


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


def capture_file(path):
    """A file of the screen-change check's capture (`screens/`): CI's
    pinned browser runs it and no test loads it, so it has no row in any
    coverage table. The loop's own capture fixer writes it at delivery."""
    return path.replace("\\", "/").split("/")[0] == "screens"


def check_coverage(output, files, min_line, min_branch, project, lcov_path=None, added=None):
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
    changed = changed_line_coverage(rows, runtime, added or {}, [f for f in checked], min_line)
    return {"passed": not low and not unmeasured and (changed is None or changed["passed"]),
            "changed_lines": changed, "files": checked, "below_minimum": low,
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
    p.add_argument("--deviation-zone", action="append", default=[],
                   help="a composition root or entry point (dir/ or exact file): a change there off --allow is a deviation, not a failure (repeatable); test files are one by default")
    p.add_argument("--expect-test", action="append", default=[],
                   help="a test name from the chunk plan's Done when (repeatable); the `tests` check fails when one is registered in no test file")
    p.add_argument("--expect-tests-from", metavar="REPORT",
                   help="read the Done when test names from this implementation report's `### Chunk <k>` section (with --chunk); plan text never crosses a shell")
    p.add_argument("--chunk", type=int, help="the chunk whose Done when line --expect-tests-from reads")
    p.add_argument("--protect", action="append", default=[], help="file that must be unchanged (repeatable)")
    p.add_argument("--test-cmd", default="npm test")
    p.add_argument("--typecheck-cmd", help="typecheck command; default: package.json's typecheck script through the test command's runner")
    p.add_argument("--lint-cmd", help="lint command; default: package.json's lint script through the test command's runner")
    p.add_argument("--timeout", type=float, default=600, help="seconds the test command may take")
    p.add_argument("--coverage", action="store_true")
    p.add_argument("--min-line", type=float, default=90)
    p.add_argument("--min-branch", type=float, default=80)
    p.add_argument("--planning", metavar="DIR", help="the target directory, whose sources.md lists the owner's files for the `sources` check (default: planning/ under the project)")
    p.add_argument("--agent-transcript", metavar="PATH", help="the builder's or fixer's transcript, replayed for shell edits and the commit rule (report-only)")
    p.add_argument("--agent", metavar="ID", help="the agent id instead of its path: resolved under --projects-dir / this project / $CLAUDE_CODE_SESSION_ID / subagents/")
    p.add_argument("--projects-dir", default=os.path.expanduser("~/.claude/projects"))
    p.add_argument("--session", default=os.environ.get("CLAUDE_CODE_SESSION_ID"), help="the session whose subagent --agent names (default: CLAUDE_CODE_SESSION_ID)")
    p.add_argument("--record-gate-baselines", action="store_true",
                   help="run every counted check of gate-checks.json, write its count as that entry's baseline, and exit")
    p.add_argument("--checks-only", action="store_true",
                   help="run the typecheck, the lint and gate-checks.json's commands only, and exit: for a builder or a fixer, before its commit")
    p.add_argument("--json")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    project = os.path.abspath(a.project)
    if a.record_baseline:
        record_baseline(project, a.record_baseline)
        return 0
    if a.record_gate_baselines:
        return record_gate_baselines(project, a.timeout)
    if a.checks_only:
        return checks_only(project, a)
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
            present = [f for f in files if os.path.isfile(os.path.join(project, f)) and not capture_file(f)]
            report["checks"]["coverage"] = check_coverage(output, present, a.min_line, a.min_branch,
                                                          project, lcov_path, added_lines(project, base, present))
            exempt = sorted(f for f in files if capture_file(f))
            if exempt:
                report["checks"]["coverage"]["capture_files"] = exempt
    finally:
        if lcov_dir:
            shutil.rmtree(lcov_dir, ignore_errors=True)
    gate_entries, gate_problems = load_gate_checks(project)
    covered = []
    if gate_entries is None:
        report["checks"]["gate-checks"] = {"passed": True, "skipped": True,
                                           "reason": f"no {GATE_CHECKS_FILE} in the project"}
    elif gate_problems:
        report["checks"]["gate-checks"] = {"passed": False, "problems": gate_problems}
    else:
        results, gate_outputs, covered = run_gate_checks(project, gate_entries, report["checks"], a.timeout)
        report["checks"].update(results)
        outputs.update(gate_outputs)
    report["checks"]["changes"] = {"passed": bool(files), "count": len(files),
                                   "files": sorted(files)}
    module_dirs = [project_relative(project, d) for d in a.module_dir]
    if a.allow:
        target = os.path.abspath(a.planning) if a.planning else os.path.join(project, "planning")
        report["checks"]["scope"] = check_scope(files, [project_relative(project, e) for e in a.allow], module_dirs,
                                                [project_relative(project, z) for z in a.deviation_zone],
                                                os.path.relpath(os.path.realpath(target), os.path.realpath(project)).replace(os.sep, "/"))
    if a.protect:
        report["checks"]["protected"] = check_protected(project, [project_relative(project, p) for p in a.protect], files)
    expected = list(a.expect_test)
    if a.expect_tests_from:
        if a.chunk is None:
            raise SystemExit("--expect-tests-from needs --chunk <k>")
        expected += [n for n in done_when_tests(a.expect_tests_from, a.chunk) if n not in expected]
    if expected:
        report["checks"]["tests"] = check_expected_tests(project, expected)
    report["checks"]["sources"], catalog = check_sources(project, a.planning, sorted(files))
    transcript = a.agent_transcript or (agent_transcript_path(a.agent, project, a.projects_dir, a.session) if a.agent else None)
    if transcript:
        if os.path.isfile(transcript):
            report["transcript"] = check_transcript(project, transcript, base, a.test_cmd, catalog)
        else:
            report["transcript"] = {"missing": transcript}
    report["passed"] = all(c["passed"] for c in report["checks"].values())
    report["metrics"] = metrics(project, [f for f in files if os.path.isfile(os.path.join(project, f))], module_dirs)

    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    for name, c in report["checks"].items():
        detail = ""
        if name.startswith(("check:", "covered:")):
            print(gate_check_line(name, c))
            continue
        if name == "gate-checks" and not c["passed"]:
            print("FAIL  gate-checks: " + "; ".join(c["problems"]))
            continue
        if c.get("skipped"):
            print(f"SKIP  {c['category'] if name.startswith('not-picked:') else name}: {c['reason']}")
            continue
        if name == "tests":
            detail = (f" registered in no test file: {json.dumps(c['missing'])}" if not c["passed"]
                      else f" every expected Done-when test name registered ({len(c['names'])})")
        elif name == "scope" and c["outside"]:
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
            if not c["passed"] and (c.get("reason") or c["below_minimum"] or c["not_measured"]):
                detail = " " + (c.get("reason") or "below minimum: " + ", ".join(
                    c["below_minimum"] + [f + " (not in the coverage table)" for f in c["not_measured"]]))
            cl = c.get("changed_lines")
            if cl:
                detail += (f" changed lines {cl['line']:g}% ({cl['uncovered']} of {cl['instrumented']} not run"
                           + ("".join(f"; {f}:{','.join(str(n) for n in lines[:12])}{',…' if len(lines) > 12 else ''}"
                                      for f, lines in cl["files"].items())) + ")")
            if c.get("type_only"):
                detail += " (types only, exempt: " + ", ".join(c["type_only"]) + ")"
            if c.get("capture_files"):
                detail += " (capture files, run by CI's browser alone, exempt: " + ", ".join(c["capture_files"]) + ")"
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
            print(script_line(name, c))
            continue
        elif name == "sources":
            if c["passed"]:
                detail = f" no value of a listed source in the {c['scanned']} changed file(s) scanned"
            else:
                parts = []
                if c["files"]:
                    parts.append(f"{len(c['hits'])} place(s) in {len(c['files'])} changed file(s) hold a value of a listed source: "
                                 + ", ".join(f"{f} ({n})" for f, n in c["files"].items()))
                parts += c["problems"]
                detail = " " + "; ".join(parts)
        print(f"{'PASS' if c['passed'] else 'FAIL'}  {name}{detail}")
        if name == "sources":
            for line in ([] if c["passed"] else c["lines"]) + c["info"]:
                print(line if line.startswith("hit:") or line.startswith("in:") else f"INFO  sources: {line}")
    for name in ["suite", "typecheck", "lint"] + [k for k in report["checks"] if k.startswith("check:")]:
        if not report["checks"][name]["passed"] and outputs.get(name):
            tail = "\n".join(outputs[name].splitlines()[-30:])
            print(f"--- {name} output, last 30 lines ---\n" + tail + "\n---")
    ran = [n for n in ("suite", "typecheck", "lint", "coverage", "scope", "protected", "tests", "sources")
           if n in report["checks"] and not report["checks"][n].get("skipped")]
    print("INFO  gate covers: " + ", ".join(ran) + ("; " + ", ".join(dict.fromkeys(covered)) if covered else ""))
    for line in metric_lines(report["metrics"]):
        print(line)
    if "transcript" in report:
        if "missing" in report["transcript"]:
            print(f"INFO  transcript: not found at {report['transcript']['missing']}; shell edits stay the agent's reported number")
        else:
            for line in transcript_lines(report["transcript"]):
                print(line)
    print("validation gate:", "PASS" if report["passed"] else "FAIL")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
