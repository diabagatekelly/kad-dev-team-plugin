#!/usr/bin/env python3
"""A mutation pass over a clone: scripted exact-string breaks, one at a time,
each run against the whole suite, the tree restored after each.

Two uses. A review writes its own mutants (below). The chunk loop's slice
review (the orchestrator's D step) has them written for it: `changed`
reads the lines a range added to the source files and writes one mutant
per operator it finds there (a comparison's boundary, an equality, a
logical connective, a boolean literal), nothing a person chose, so what
survives is a line of the slice's own that no test holds; the
test-quality reviewer reads the survivors and says which matter.

The slice 2 review (2026-11-08) ran forty such breaks by hand through a
scratch script; this is that script as a tool, so the next review and the
slice review's measures run it the same way. Nothing here invents a
mutant: the reviewer writes them, one per module or two per module of the
slice's subject, as a JSON list, and the runner applies them.

The mutants file (JSON, a list; or JSON lines, one object per line):

    [{"file": "src/ledger/category-rules.ts",
      "old": "amountRuleFor(rules, t) ?? generalRuleFor(rules, t)",
      "new": "generalRuleFor(rules, t) ?? amountRuleFor(rules, t)",
      "note": "ruleFor: general rule first instead of the exact-amount rule",
      "area": "categorization"}]

`old` must occur exactly once in `file` (`check` says so without running
anything); `note` is the break in words, as the table prints it; `area`
is free text for grouping (the subject modules against the rest).

`run`, in order: refuses a tree that is not clean; runs the test command
(split as a shell would, run without one; a command that needs a shell's
features is written `sh -c '…'`) once as the baseline and refuses if it
fails; then for each mutant applies
the replacement, runs the typecheck command if given, runs the test
command, reads the result (the failing tests' names where the runner
prints them: node's `not ok … - name`, jest's `✕ name`, vitest's `× name`
and `FAIL file > name`, pytest's `FAILED path::name`, unittest's `FAIL:
name`; colour escapes are stripped first, so a forced-colour run reads
the same; a `✖` or `not ok` line indented less than the result line
before it is the summary of a suite or a parent test, not a test, and is
not named; a non-zero exit with no names read is still a catch, reported
as `exit <code>`; a run that times out after naming a failure is a catch
too, since the tests caught the break before the hang), restores the file with `git checkout --` and checks that
`git status --porcelain` is empty again, stopping if it is not. Every
mutant's outcome goes to the JSON-lines log as it finishes, and the
markdown report is written at the end: the table (number, file:line, the
break, CAUGHT (n failed) by the first three test names | SURVIVED, in the
slice's diff or not), the summary (kill rate overall, over the diff's
files, per area; mutants also caught by the typecheck; kills that hang on
one test), and the survivors with their notes. Counts and test names
only: the report never prints `old` or `new`, so a mutant written over a
line that holds a value the owner's data gave never carries it into the
review (the note is the reviewer's own words).

`changed`, in order: lists the source files `git diff --name-only
<base>...HEAD` names (`.ts .tsx .js .jsx .mjs .cjs .py`, test files left
out), reads the lines the range added to each (`git diff -U0`), blanks
strings and comments on a line before looking for an operator, and
writes one mutant per operator kind per line: `old` is the whole line
(the line before it too when the line alone occurs more than once; a
line that is still not unique is skipped and counted), `new` the line
with the first such operator replaced, `note` the line and the
replacement in words (`line 41: <= to <`), never the code. With more
than `--max` mutants (40) it keeps every k-th in file and line order, so
the cap thins the pass evenly instead of dropping the last files. The
mutants file holds lines of the source: write it outside the tree.

`run --allow-dirty` is for the slice review's own tree, where the
orchestrator's log is modified and never committed inside the loop: the
tree's tracked changes must be the same after every mutant as before the
run, and no mutant's file may be among them.

Usage:
  python3 -I <scripts>/mutation_pass.py check --repo DIR --mutants FILE
  python3 -I <scripts>/mutation_pass.py changed --repo DIR --base REF --out FILE [--max 40]
  python3 -I <scripts>/mutation_pass.py run --repo DIR --mutants FILE --test 'CMD'
      [--typecheck 'CMD'] [--base origin/main] [--out REPORT.md] [--log LOG.jsonl]
      [--timeout SECONDS] [--title TEXT] [--allow-dirty]
  (from this repository: python3 -I skills/orchestrator/scripts/mutation_pass.py ...)
Exit codes: 0 ran (survivors are findings, not failures); 1 usage, a
mutant that does not match once, or a tree that is not clean; 2 the
baseline fails; 3 the tree could not be restored after a mutant (the
run stops there, the log says which).
"""
import argparse
import datetime as dt
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import time

FAIL_LINE = re.compile(
    r"^\s*(?:"
    r"not ok \d+ - (?P<node>.+?)(?: # .*)?"          # node --test (TAP)
    r"|✖ (?P<nodespec>.+?) \(\d+(?:\.\d+)?ms\)"       # node --test (spec, the default off a TTY since Node 20)
    r"|[✕✗×] (?P<jest>.+?)(?: \(\d+ ?ms\))?"          # jest, vitest
    r"|FAIL +\S+ > (?P<vitest>.+)"                     # vitest's file > name
    r"|FAILED (?P<pytest>\S+::\S+)"                   # pytest
    r"|FAIL: (?P<unittest>\S+(?: \([^)]*\))?)"        # unittest
    r")\s*$")
COUNT_LINES = [
    re.compile(r"^# fail (\d+)", re.M),                           # node --test (TAP)
    re.compile(r"^ℹ fail (\d+)", re.M),                            # node --test (spec)
    re.compile(r"^Tests:\s+(\d+) failed", re.M),                   # jest
    re.compile(r"^\s*Tests\s+(\d+) failed", re.M),                 # vitest
    re.compile(r"(\d+) failed", re.M),                             # pytest's summary
    re.compile(r"FAILED \((?:[^)]*?)(?:failures|errors)=(\d+)", re.M),  # unittest
]


def say(msg):
    print(msg, flush=True)


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def load_mutants(path):
    text = open(path, encoding="utf-8").read()
    try:
        data = json.loads(text)
    except ValueError:
        data = [json.loads(line) for line in text.splitlines() if line.strip()]
    if not isinstance(data, list):
        raise SystemExit(f"mutation_pass: {path} must hold a list of mutants")
    for i, m in enumerate(data, 1):
        for key in ("file", "old", "new"):
            if not isinstance(m.get(key), str) or (key != "new" and not m[key]):
                raise SystemExit(f"mutation_pass: mutant {i} has no `{key}`")
        m.setdefault("note", "")
        m.setdefault("area", "")
    return data


def mutant_path(repo, m):
    """The mutant's file, resolved, or None and why: it must be inside the
    clone (no absolute path, no `..`, no symlink out) and tracked by git,
    since `git checkout --` is what restores it."""
    if os.path.isabs(m["file"]):
        return None, f"{m['file']} is an absolute path; name the file relative to the clone"
    if os.path.islink(os.path.join(repo, m["file"])):
        return None, f"{m['file']} is a symlink; name its target"
    path = os.path.realpath(os.path.join(repo, m["file"]))
    root = os.path.realpath(repo)
    if path != root and not path.startswith(root + os.sep):
        return None, f"{m['file']} resolves outside the clone"
    if git(repo, "ls-files", "--error-unmatch", "--", m["file"]).returncode != 0:
        return None, f"{m['file']} is not tracked by git, so it could not be restored"
    return path, None


def locate(repo, m):
    """(line number, problem): where `old` is in the file, once."""
    path, problem = mutant_path(repo, m)
    if problem:
        return None, problem
    try:
        text = open(path, encoding="utf-8").read()
    except OSError as e:
        return None, f"cannot read {m['file']}: {e.strerror}"
    n = text.count(m["old"])
    if n != 1:
        return None, f"`old` occurs {n} times in {m['file']}, not once"
    return text[: text.index(m["old"])].count("\n") + 1, None


def check(repo, mutants):
    bad = 0
    for i, m in enumerate(mutants, 1):
        line, problem = locate(repo, m)
        if problem:
            bad += 1
            say(f"{i:>3}  PROBLEM  {m['file']}: {problem}")
        else:
            say(f"{i:>3}  ok       {m['file']}:{line}  {m['note']}")
    say(f"{len(mutants)} mutants, {bad} with a problem")
    return 1 if bad else 0


TIMED_OUT, NOT_RUN = -1, -2  # exit codes of the runner's own, never a test's


def run_cmd(cmd, repo, timeout):
    """(exit code, output, seconds); TIMED_OUT and NOT_RUN (the command
    could not start) are the runner's failures and never a kill."""
    start = time.monotonic()
    try:
        # Split as a shell would and run without one: no shell settings
        # propagate, and nothing in the mutants file reaches a shell.
        # Accepted 2026-11-10: `cmd` is the test or typecheck command the
        # reviewer gave on this tool's own command line, nothing read from a
        # file or the network; the mutants file never reaches a command.
        r = subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
            shlex.split(cmd), cwd=repo, capture_output=True, text=True, errors="replace", timeout=timeout)
        return r.returncode, r.stdout + r.stderr, time.monotonic() - start
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"") if isinstance(e.stdout, bytes) else (e.stdout or "")
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        return TIMED_OUT, out + f"\n[timed out after {timeout} s]", time.monotonic() - start
    except (OSError, ValueError) as e:
        return NOT_RUN, f"[could not run `{cmd}`: {e}]", time.monotonic() - start


def read_result(code, output):
    """(verdict, failing count or None, failing test names): `caught` when
    the output names a failing test or counts one, `survived` on exit 0
    with none, `error` on a non-zero exit with no test failure read (the
    runner itself failed: a timeout, a missing module, a broken install),
    which is neither a kill nor a survivor."""
    names = []
    for line in output.splitlines():
        m = FAIL_LINE.match(line)
        if m:
            name = next(v for v in m.groupdict().values() if v)
            if name not in names:
                names.append(name)
    count = None
    for rx in COUNT_LINES:
        m = rx.search(output)
        if m:
            count = int(m.group(1))
            break
    if count is None and names:
        count = len(names)
    if count:
        return "caught", count, names
    if code in (TIMED_OUT, NOT_RUN):
        return "error", count, names
    return ("survived" if code == 0 else "error"), count, names


def diff_files(repo, base):
    r = git(repo, "diff", "--name-only", f"{base}...HEAD")
    if r.returncode != 0:
        return None
    return set(r.stdout.split())


SOURCE = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py")
TEST_DIRS = {"test", "tests", "__tests__", "spec"}
TEST_NAME = re.compile(r"(?:\.(?:test|spec)\.[cm]?[jt]sx?|(?:^|/)test_[^/]*\.py|_test\.py)$")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", re.M)
JS_BLANK = re.compile(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"|`(?:\\.|[^`\\])*`|//.*$|/\*.*?\*/")
PY_BLANK = re.compile(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"|#.*$")
# (the operator as it stands in formatted code, its replacement, the words for the note)
JS_OPERATORS = [(" <= ", " < ", "<= to <"), (" >= ", " > ", ">= to >"), (" < ", " <= ", "< to <="),
                (" > ", " >= ", "> to >="), (" === ", " !== ", "=== to !=="), (" !== ", " === ", "!== to ==="),
                (" == ", " != ", "== to !="), (" != ", " == ", "!= to =="), (" && ", " || ", "&& to ||"),
                (" || ", " && ", "|| to &&")]
JS_WORDS = [("true", "false"), ("false", "true")]
PY_OPERATORS = [(" <= ", " < ", "<= to <"), (" >= ", " > ", ">= to >"), (" < ", " <= ", "< to <="),
                (" > ", " >= ", "> to >="), (" == ", " != ", "== to !="), (" != ", " == ", "!= to =="),
                (" and ", " or ", "and to or"), (" or ", " and ", "or to and")]
PY_WORDS = [("True", "False"), ("False", "True")]
NOT_CODE = re.compile(r"^\s*(?:import\b|from\b.*\bimport\b|export\s+(?:type|interface)\b|type\s+\w|interface\s+\w|\*|/\*|//|#)")


def is_test_file(path):
    parts = path.split("/")
    return any(p in TEST_DIRS for p in parts[:-1]) or bool(TEST_NAME.search(path))


def blanked(line, python):
    """The line with every string and comment replaced by spaces of the
    same length, so an operator's position in it is its position in the
    line."""
    return (PY_BLANK if python else JS_BLANK).sub(lambda m: " " * len(m.group(0)), line)


def line_mutants(line, python):
    """[(the mutated line, the replacement in words)]: one per operator kind
    found in the line's code, the first occurrence of each."""
    if NOT_CODE.match(line):
        return []
    code = blanked(line, python)
    out = []
    for old, new, words in (PY_OPERATORS if python else JS_OPERATORS):
        at = code.find(old)
        if at >= 0:
            out.append((line[:at] + new + line[at + len(old):], words))
    for old, new in (PY_WORDS if python else JS_WORDS):
        m = re.search(r"\b" + old + r"\b", code)
        if m:
            out.append((line[:m.start()] + new + line[m.end():], f"{old} to {new}"))
    return out


def added_lines(repo, base, path):
    """The 1-based numbers of the lines `<base>...HEAD` added to `path`."""
    r = git(repo, "diff", "-U0", "--no-renames", f"{base}...HEAD", "--", path)
    lines = set()
    for start, count in HUNK.findall(r.stdout):
        lines.update(range(int(start), int(start) + int(count if count != "" else 1)))
    return lines


def changed(a):
    """`changed`: the mutants of the lines a range added (module docstring)."""
    repo = os.path.abspath(a.repo)
    names = git(repo, "diff", "--name-only", "--no-renames", "--diff-filter=AM", f"{a.base}...HEAD")
    if names.returncode != 0:
        say(f"mutation_pass: `{a.base}` is not a ref in {repo}")
        return 1
    files = sorted(f for f in names.stdout.splitlines() if f.endswith(SOURCE) and not is_test_file(f))
    mutants, skipped, lines_read = [], 0, 0
    for path in files:
        try:
            text = open(os.path.join(repo, path), encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        rows = text.split("\n")
        for n in sorted(added_lines(repo, a.base, path)):
            if n > len(rows) or not rows[n - 1].strip():
                continue
            lines_read += 1
            line = rows[n - 1]
            for mutated, words in line_mutants(line, path.endswith(".py")):
                old, new = line, mutated
                if text.count(old) != 1 and n > 1:
                    old, new = rows[n - 2] + "\n" + line, rows[n - 2] + "\n" + mutated
                if text.count(old) != 1:
                    skipped += 1
                    continue
                mutants.append({"file": path, "old": old, "new": new, "note": f"line {n}: {words}",
                                "area": path.split("/")[0] if "/" in path else ""})
    total = len(mutants)
    if a.max and total > a.max:
        step = total / a.max
        mutants = [mutants[int(i * step)] for i in range(a.max)]
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(mutants, f, indent=1)
        f.write("\n")
    say(f"mutants: {len(mutants)} written to {a.out} ({lines_read} added lines in {len(files)} source files; "
        f"{total} found{', capped at ' + str(a.max) if total > len(mutants) else ''}; {skipped} skipped, line not unique)")
    return 0


def tracked_changes(repo):
    return git(repo, "status", "--porcelain", "--untracked-files=no").stdout


def run(a, mutants):
    repo = os.path.abspath(a.repo)
    dirty = git(repo, "status", "--porcelain").stdout.strip()
    if dirty and not a.allow_dirty:
        say("mutation_pass: the tree is not clean; commit or stash first (every mutant is restored with git checkout)")
        return 1
    if a.allow_dirty:
        modified = {line[3:].strip().strip('"') for line in tracked_changes(repo).splitlines()}
        hit = sorted({m["file"] for m in mutants} & modified)
        if hit:
            say(f"mutation_pass: {', '.join(hit)} has uncommitted changes and a mutant; restoring it would lose them")
            return 1
    problems = [(i, locate(repo, m)[1]) for i, m in enumerate(mutants, 1)]
    problems = [(i, p) for i, p in problems if p]
    if problems:
        for i, p in problems:
            say(f"mutation_pass: mutant {i}: {p}")
        return 1
    head = git(repo, "rev-parse", "--short", "HEAD").stdout.strip()
    changed = diff_files(repo, a.base) if a.base else None
    if a.base and changed is None:
        say(f"mutation_pass: `{a.base}` is not a ref in {repo} (a clone of one branch has no origin/main); the report will carry no in-diff column")
    log = open(a.log, "a", encoding="utf-8") if a.log else None

    def record(obj):
        if log:
            log.write(json.dumps(obj) + "\n")
            log.flush()

    lock = os.path.join(repo, ".git", "mutation-pass.lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
    except FileExistsError:
        say(f"mutation_pass: another run holds {lock}; one run per clone at a time (remove it if that run is gone)")
        return 1
    except OSError as e:
        say(f"mutation_pass: cannot create {lock}: {e}")
        return 1
    try:
        return run_locked(a, repo, mutants, head, changed, log, record)
    finally:
        try:
            os.unlink(lock)
        except OSError:
            pass


def run_locked(a, repo, mutants, head, changed, log, record):
    if a.typecheck:
        tcode, tout, _ = run_cmd(a.typecheck, repo, a.timeout)
        if tcode != 0:
            say(f"mutation_pass: the typecheck fails on the baseline (exit {tcode}); nothing mutated")
            say(tout.strip().splitlines()[-1] if tout.strip() else "")
            return 2
    say(f"mutation_pass: baseline `{a.test}` in {repo} at {head}")
    code, out, secs = run_cmd(a.test, repo, a.timeout)
    verdict, count, names = read_result(code, out)
    if verdict != "survived":
        why = out.strip().splitlines()[-1] if code in (TIMED_OUT, NOT_RUN) and out.strip() else ""
        say(f"mutation_pass: the baseline fails (exit {code}{', ' + str(count) + ' failed' if count else ''}){': ' + why if why else ''}; nothing mutated")
        record({"mutant": 0, "baseline": True, "exit": code, "failed": count, "names": names[:3]})
        return 2
    base_count = None
    m = re.search(r"^# (?:pass|tests) (\d+)|^ℹ (?:pass|tests) (\d+)|^Tests:\s+(\d+) passed|^\s*Tests\s+(\d+) passed|(\d+) passed|Ran (\d+) tests?", out, re.M)
    if m:
        base_count = next(g for g in m.groups() if g)
    say(f"mutation_pass: baseline passes ({base_count or 'count not read'} tests, {secs:.0f} s)")
    record({"mutant": 0, "baseline": True, "exit": 0, "tests": base_count, "seconds": round(secs, 1)})

    results = []
    before = tracked_changes(repo) if a.allow_dirty else ""
    # A termination (Ctrl-C, a kill) raises through the `finally` below, so
    # the mutant in flight is restored before the runner exits.
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    for i, m in enumerate(mutants, 1):
        line, _ = locate(repo, m)
        path, _ = mutant_path(repo, m)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        try:
            # the write is inside the block, so an interrupted write is restored too
            with open(path, "w", encoding="utf-8") as f:
                f.write(text.replace(m["old"], m["new"], 1))
            type_caught = False
            if a.typecheck:
                tcode, _, _ = run_cmd(a.typecheck, repo, a.timeout)
                type_caught = tcode not in (0, TIMED_OUT, NOT_RUN)
            code, out, secs = run_cmd(a.test, repo, a.timeout)
        finally:
            git(repo, "checkout", "--", m["file"])
        verdict, count, names = read_result(code, out)
        after = tracked_changes(repo) if a.allow_dirty else git(repo, "status", "--porcelain").stdout.strip()
        if after != before:
            say(f"mutation_pass: the tree is not clean after mutant {i} ({m['file']}); stopped")
            record({"mutant": i, "file": m["file"], "line": line, "restored": False})
            return 3
        res = {"mutant": i, "file": m["file"], "line": line, "note": m["note"], "area": m["area"],
               "verdict": verdict, "caught": verdict == "caught", "failed": count, "names": names[:3], "exit": code,
               "typecheck_caught": type_caught,
               "in_diff": (m["file"] in changed) if changed is not None else None, "seconds": round(secs, 1)}
        results.append(res)
        record(res)
        shown = {"caught": f"CAUGHT ({count} failed)", "survived": "SURVIVED",
                 "error": f"ERROR (exit {code}, no test failure read)"}[verdict]
        say(f"{i:>3}  {shown:<36} {m['file']}:{line}  {m['note']}")
    if log:
        log.close()
    report = render(a, repo, head, base_count, results, changed is not None)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(report)
        say(f"mutation_pass: report written to {a.out}")
    else:
        say(report)
    counted = [r for r in results if r["verdict"] != "error"]
    say(f"mutation: {len(counted)} mutants, {sum(1 for r in counted if r['caught'])} caught, "
        f"{sum(1 for r in counted if not r['caught'])} survived"
        + (f", {len(results) - len(counted)} not counted" if len(results) != len(counted) else ""))
    return 0


def render(a, repo, head, base_count, results, have_diff):
    errors = [r for r in results if r["verdict"] == "error"]
    results = [r for r in results if r["verdict"] != "error"]
    n = len(results)
    caught = [r for r in results if r["caught"]]
    rate = f"{100 * len(caught) / n:.1f}%" if n else "n/a"
    lines = [f"# Mutation pass: {a.title or os.path.basename(repo)} at {head}", "",
             f"Clone: `{repo}`. Baseline `{a.test}`: passes ({base_count or 'count not read'} tests)."
             + (f" Typecheck `{a.typecheck}` run on every mutant." if a.typecheck else ""), "",
             "## Method", "",
             "Each mutant is an exact string replacement that matched once in its file, applied by "
             "`mutation_pass.py`; then the typecheck (if given) and the full suite ran once, "
             "`git checkout --` restored the file, and `git status --porcelain` was empty after every mutant. "
             "Test names are listed as the runner prints them; the first three failures are shown with the "
             "total in brackets. \"In the diff\" means the file is in `git diff --name-only <base>...HEAD`.", "",
             "## Results", "",
             "| # | file:line | the break | result | in the diff? |", "|---|---|---|---|---|"]
    for r in sorted(results + errors, key=lambda r: r["mutant"]):
        if r["verdict"] == "caught":
            by = "; ".join(r["names"]) if r["names"] else "the runner's failure count"
            verdict = f"CAUGHT ({r['failed']} failed) by {by}" + (" [typecheck also fails]" if r["typecheck_caught"] else "")
        elif r["verdict"] == "survived":
            verdict = "SURVIVED" + (" [typecheck fails]" if r["typecheck_caught"] else "")
        else:
            verdict = f"ERROR (exit {r['exit']}, no test failure read; not counted)"
        in_diff = "yes" if r["in_diff"] else "no" if r["in_diff"] is False else "n/a"
        lines.append(f"| {r['mutant']} | {r['file']}:{r['line']} | {r['note']} | {verdict} | {in_diff} |")
    lines += ["", "## Summary", "",
              f"- Mutants: **{n}**. Caught: **{len(caught)}**. Survived: **{n - len(caught)}**. Kill rate **{rate}**."
              + (f" Not counted, the runner itself failed: {', '.join(str(r['mutant']) for r in errors)}." if errors else "")]
    if have_diff:
        d = [r for r in results if r["in_diff"]]
        dc = [r for r in d if r["caught"]]
        lines.append(f"- In the diff against `{a.base}`: {len(d)} mutants, {len(dc)} caught"
                     + (f", **{100 * len(dc) / len(d):.1f}%**." if d else "."))
    for area in sorted({r["area"] for r in results if r["area"]}):
        g = [r for r in results if r["area"] == area]
        gc = [r for r in g if r["caught"]]
        lines.append(f"- Area `{area}`: {len(g)} mutants, {len(gc)} caught, **{100 * len(gc) / len(g):.1f}%**.")
    both = [str(r["mutant"]) for r in results if r["typecheck_caught"] and r["caught"]]
    only_type = [str(r["mutant"]) for r in results if r["typecheck_caught"] and not r["caught"]]
    if a.typecheck:
        lines.append(f"- Also caught by the typecheck: {', '.join(both) or 'none'}; caught by the typecheck alone: {', '.join(only_type) or 'none'}.")
    single = [str(r["mutant"]) for r in results if r["caught"] and r["failed"] == 1]
    lines.append(f"- Kills that hang on a single test: {', '.join(single) or 'none'}.")
    lines += ["", "## Survivors", ""]
    survivors = [r for r in results if not r["caught"]]
    if not survivors:
        lines.append("None.")
    for r in survivors:
        lines.append(f"- **#{r['mutant']} `{r['file']}:{r['line']}`: {r['note']}.** No test fails. Gap: a missing assertion or a missing test; the reviewer names which.")
    lines += ["", f"Written {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} by `mutation_pass.py`"
              + (f"; log `{a.log}`" if a.log else "") + "."]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="verify every mutant matches once; run nothing")
    c.add_argument("--repo", required=True)
    c.add_argument("--mutants", required=True)
    r = sub.add_parser("run", help="apply each mutant, run the suite, restore, report")
    r.add_argument("--repo", required=True)
    r.add_argument("--mutants", required=True)
    r.add_argument("--test", required=True, help="the test command, split as a shell would and run in the repo without one (wrap one that needs a shell in sh -c '…')")
    r.add_argument("--typecheck", help="a typecheck command, the same way, run before the suite on every mutant")
    r.add_argument("--base", default="origin/main", help="the diff base for the 'in the diff' column ('' for none)")
    r.add_argument("--out", help="the markdown report (default: printed)")
    r.add_argument("--log", help="a JSON-lines log, one line per mutant as it finishes")
    r.add_argument("--timeout", type=int, default=1800, help="seconds per command (1800)")
    r.add_argument("--title", help="the report's title (default: the repo's basename)")
    r.add_argument("--allow-dirty", action="store_true",
                   help="run on a tree with uncommitted changes to other tracked files (the loop's log); they must be the same after every mutant")
    g = sub.add_parser("changed", help="write one mutant per operator on the lines a range added to the source files")
    g.add_argument("--repo", required=True)
    g.add_argument("--base", required=True, help="the range is <base>...HEAD")
    g.add_argument("--out", required=True, help="the mutants file to write (outside the tree: it holds source lines)")
    g.add_argument("--max", type=int, default=40, help="at most this many mutants, thinned evenly (40; 0 for all)")
    a = ap.parse_args()
    if a.cmd == "changed":
        return changed(a)
    mutants = load_mutants(a.mutants)
    if a.cmd == "check":
        return check(os.path.abspath(a.repo), mutants)
    return run(a, mutants)


if __name__ == "__main__":
    sys.exit(main())
