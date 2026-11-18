"""The mutation runner, without a model: on a scratch git repository with a
Python module and a unittest suite,

1. `check` reports each mutant's line and refuses one that does not match
   once;
2. `run` refuses a dirty tree and a failing baseline;
3. a mutant the suite catches is CAUGHT with the failing test's name, one
   it does not is SURVIVED, the file is restored after each and the tree
   is clean at the end; the report and the log carry counts and names,
   never the replaced text.

Usage: python3 -I evals/tools/mutation_pass_test.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "skills", "orchestrator", "scripts", "mutation_pass.py")
TEST_CMD = f"{sys.executable} -B -m unittest -q tests.test_calc"  # no -I (the scratch repo is the import root); -B so no stale bytecode survives a same-size mutant


def git(cwd, *args):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, check=True).stdout


class MutationPass(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(os.path.join(self.repo, "calc"))
        os.makedirs(os.path.join(self.repo, "tests"))
        for d in ("calc", "tests"):
            open(os.path.join(self.repo, d, "__init__.py"), "w").close()
        with open(os.path.join(self.repo, "calc", "fees.py"), "w") as f:
            f.write("def late_fee(days):\n    if days <= 0:\n        return 0\n    return days * 25\n\n\n"
                    "def label(days):\n    return 'none' if days <= 0 else 'due'\n")
        with open(os.path.join(self.repo, "tests", "test_calc.py"), "w") as f:
            f.write("import unittest\nfrom calc.fees import late_fee, label\n\n\nclass Fees(unittest.TestCase):\n"
                    "    def test_charges_per_day(self):\n        self.assertEqual(late_fee(3), 75)\n\n"
                    "    def test_nothing_before_the_due_date(self):\n        self.assertEqual(late_fee(0), 0)\n")
        git(self.tmp, "init", "-q", "-b", "main", self.repo)
        git(self.repo, "config", "user.email", "t@example.invalid")
        git(self.repo, "config", "user.name", "T")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "start")
        self.mutants = os.path.join(self.tmp, "mutants.json")
        with open(self.mutants, "w") as f:
            json.dump([
                {"file": "calc/fees.py", "old": "days * 25", "new": "days * 20", "note": "late_fee: the daily rate", "area": "fees"},
                {"file": "calc/fees.py", "old": "'none' if days <= 0 else 'due'", "new": "'due'", "note": "label: always due", "area": "labels"},
            ], f)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_tool(self, *args, expect=0):
        r = subprocess.run([sys.executable, "-I", SCRIPT, *args], capture_output=True, text=True)
        self.assertEqual(r.returncode, expect, r.stdout + r.stderr)
        return r.stdout

    def test_check_lists_lines_and_refuses_a_bad_match(self):
        out = self.run_tool("check", "--repo", self.repo, "--mutants", self.mutants)
        self.assertIn("calc/fees.py:4  late_fee: the daily rate", out)
        self.assertIn("2 mutants, 0 with a problem", out)
        with open(self.mutants, "w") as f:
            json.dump([{"file": "calc/fees.py", "old": "days", "new": "d", "note": "many"}], f)
        out = self.run_tool("check", "--repo", self.repo, "--mutants", self.mutants, expect=1)
        self.assertIn("occurs 5 times", out)
        # a path outside the clone, and an untracked file, are refused
        with open(os.path.join(self.repo, "notes.txt"), "w") as f:
            f.write("untracked\n")
        with open(self.mutants, "w") as f:
            json.dump([{"file": "../outside.py", "old": "x", "new": "y"}, {"file": "/etc/hosts", "old": "x", "new": "y"},
                       {"file": "notes.txt", "old": "untracked", "new": "changed"}], f)
        out = self.run_tool("check", "--repo", self.repo, "--mutants", self.mutants, expect=1)
        self.assertIn("resolves outside the clone", out)
        self.assertIn("is an absolute path", out)
        self.assertIn("not tracked by git", out)
        os.remove(os.path.join(self.repo, "notes.txt"))
        # a tracked symlink is refused: git checkout restores the link, not its target
        os.symlink("calc/fees.py", os.path.join(self.repo, "fees-link.py"))
        git(self.repo, "add", "fees-link.py")
        git(self.repo, "commit", "-qm", "link")
        with open(self.mutants, "w") as f:
            json.dump([{"file": "fees-link.py", "old": "days * 25", "new": "days * 20"}], f)
        out = self.run_tool("check", "--repo", self.repo, "--mutants", self.mutants, expect=1)
        self.assertIn("is a symlink", out)

    def test_run_refuses_a_dirty_tree_and_a_failing_baseline(self):
        with open(os.path.join(self.repo, "scratch.txt"), "w") as f:
            f.write("x")
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", TEST_CMD, "--base", "", expect=1)
        self.assertIn("not clean", out)
        os.remove(os.path.join(self.repo, "scratch.txt"))
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", f"{sys.executable} -c 'raise SystemExit(1)'", "--base", "", expect=2)
        self.assertIn("baseline fails", out)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")
        # a command that cannot start is a runner error, said plainly, not a traceback
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", "no-such-runner-here --quiet", "--base", "", expect=2)
        self.assertIn("could not run", out)
        self.assertNotIn("Traceback", out)
        # a typecheck that fails on the baseline refuses the run
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", TEST_CMD, "--typecheck", f"{sys.executable} -c 'raise SystemExit(3)'", "--base", "", expect=2)
        self.assertIn("typecheck fails on the baseline", out)
        self.assertFalse(os.path.exists(os.path.join(self.repo, ".git", "mutation-pass.lock")))

    def test_run_reports_caught_and_survived_and_restores(self):
        report = os.path.join(self.tmp, "report.md")
        log = os.path.join(self.tmp, "log.jsonl")
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", TEST_CMD,
                            "--base", "", "--out", report, "--log", log, "--title", "fees")
        self.assertIn("CAUGHT (1 failed)", out)
        self.assertIn("SURVIVED", out)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")
        with open(report, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("| 1 | calc/fees.py:4 | late_fee: the daily rate | CAUGHT (1 failed) by test_charges_per_day (tests.test_calc.Fees) | n/a |", text)
        self.assertIn("| 2 | calc/fees.py:8 | label: always due | SURVIVED | n/a |", text)
        self.assertIn("Kill rate **50.0%**", text)
        self.assertIn("Area `fees`: 1 mutants, 1 caught, **100.0%**", text)
        self.assertIn("Kills that hang on a single test: 1.", text)
        self.assertIn("**#2 `calc/fees.py:8`: label: always due.**", text)
        with open(log, encoding="utf-8") as f:
            logged = f.read()
        for secret in ("days * 20", "'due'"):
            self.assertNotIn(secret, text)
            self.assertNotIn(secret, logged)
        with open(log, encoding="utf-8") as f:
            rows = [json.loads(l) for l in f]
        self.assertEqual([r.get("caught") for r in rows], [None, True, False])

    def add_a_slice(self):
        """A branch whose one commit adds a guarded rule and an unguarded one."""
        git(self.repo, "checkout", "-q", "-b", "slice")
        with open(os.path.join(self.repo, "calc", "fees.py"), "a") as f:
            f.write("\n\ndef capped(days):\n    # days >= 40 is the cap, in words\n    if days >= 40 and days > 0:\n        return 900\n"
                    "    return late_fee(days)\n\n\ndef waived(member):\n    return member == 'staff'\n")
        with open(os.path.join(self.repo, "tests", "test_calc.py"), "a") as f:
            f.write("\n    def test_cap(self):\n        from calc.fees import capped\n"
                    "        self.assertEqual(capped(40), 900)\n        self.assertEqual(capped(39), 975)\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "cap and waiver")

    def test_changed_writes_mutants_for_the_added_lines_only(self):
        self.add_a_slice()
        out_file = os.path.join(self.tmp, "changed.json")
        out = self.run_tool("changed", "--repo", self.repo, "--base", "main", "--out", out_file)
        mutants = json.load(open(out_file))
        notes = sorted(m["note"] for m in mutants)
        # the cap line has three operators, the waiver line one; the comment's `>=`, the older
        # `days <= 0` lines and the test file give none
        self.assertEqual(notes, ["line 13: > to >=", "line 13: >= to >", "line 13: and to or", "line 19: == to !="], out)
        self.assertTrue(all(m["file"] == "calc/fees.py" for m in mutants))
        self.assertIn("4 written", out)
        self.run_tool("check", "--repo", self.repo, "--mutants", out_file)

    def test_changed_survivor_is_the_unguarded_rule(self):
        self.add_a_slice()
        out_file = os.path.join(self.tmp, "changed.json")
        self.run_tool("changed", "--repo", self.repo, "--base", "main", "--out", out_file)
        report = os.path.join(self.tmp, "report.md")
        out = self.run_tool("run", "--repo", self.repo, "--mutants", out_file, "--test", TEST_CMD, "--base", "main", "--out", report)
        text = open(report).read()
        self.assertRegex(text, r"calc/fees\.py:19 \| line 19: == to != \| SURVIVED")
        self.assertRegex(text, r"calc/fees\.py:13 \| line 13: >= to > \| CAUGHT")
        self.assertNotIn("staff", text)  # the report never carries the line
        self.assertRegex(out, r"mutation: 4 mutants, \d caught, \d survived")

    def test_changed_caps_evenly_and_skips_a_line_that_is_not_unique(self):
        git(self.repo, "checkout", "-q", "-b", "slice")
        with open(os.path.join(self.repo, "calc", "more.py"), "w") as f:
            f.write("".join(f"def f{i}(a):\n    return a == {i}\n" for i in range(10)) + "def g(a):\n    return a > 1\ndef g(a):\n    return a > 1\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "more")
        out_file = os.path.join(self.tmp, "changed.json")
        out = self.run_tool("changed", "--repo", self.repo, "--base", "main", "--out", out_file, "--max", "5")
        mutants = json.load(open(out_file))
        self.assertEqual([m["note"] for m in mutants], [f"line {n}: == to !=" for n in (2, 6, 10, 14, 18)], out)
        self.assertIn("10 found, capped at 5", out)
        self.assertIn("2 skipped, line not unique", out)

    def test_allow_dirty_runs_beside_an_uncommitted_log_and_refuses_a_dirty_target(self):
        with open(os.path.join(self.repo, "log.md"), "w") as f:
            f.write("entry 1\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "log")
        with open(os.path.join(self.repo, "log.md"), "a") as f:
            f.write("entry 2\n")
        self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", TEST_CMD, "--base", "", expect=1)
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", TEST_CMD, "--base", "", "--allow-dirty",
                            "--out", os.path.join(self.repo, "report.md"), "--log", os.path.join(self.repo, "pass.jsonl"))
        self.assertIn("mutation: 2 mutants, 1 caught, 1 survived", out)
        self.assertEqual(open(os.path.join(self.repo, "log.md")).read(), "entry 1\nentry 2\n")
        with open(os.path.join(self.repo, "calc", "fees.py"), "a") as f:
            f.write("# an edit nobody committed\n")
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", TEST_CMD, "--base", "", "--allow-dirty", expect=1)
        self.assertIn("calc/fees.py has uncommitted changes and a mutant", out)

    def dirty_tree(self):
        """The slice review's tree: a tracked log with an uncommitted line,
        an untracked note, and an ignored dependency directory."""
        with open(os.path.join(self.repo, "log.md"), "w") as f:
            f.write("entry 1\n")
        with open(os.path.join(self.repo, ".gitignore"), "w") as f:
            f.write("deps/\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "log")
        with open(os.path.join(self.repo, "log.md"), "a") as f:
            f.write("entry 2\n")
        with open(os.path.join(self.repo, "note.txt"), "w") as f:
            f.write("untracked\n")
        os.makedirs(os.path.join(self.repo, "deps"))
        with open(os.path.join(self.repo, "deps", "marker.txt"), "w") as f:
            f.write("installed\n")

    def suite_script(self, kill_on=None):
        """A test command that says where it ran and what it found there,
        then runs the suite; with `kill_on`, it kills the runner (its
        parent) the moment that text is in the mutated file."""
        script = os.path.join(self.tmp, "suite.py")
        self.cwds = os.path.join(self.tmp, "cwds.txt")
        with open(script, "w") as f:
            f.write("import os, signal, subprocess, sys\n"
                    f"open({self.cwds!r}, 'a').write(os.path.realpath(os.getcwd()) + '|' + open('log.md').read().replace('\\n', ' ')"
                    " + '|' + str(os.path.exists('deps/marker.txt')) + '|' + str(os.path.exists('note.txt')) + '\\n')\n"
                    + (f"if {kill_on!r} in open('calc/fees.py').read():\n    os.kill(os.getppid(), signal.SIGKILL)\n" if kill_on else "")
                    + "sys.exit(subprocess.run([sys.executable, '-B', '-m', 'unittest', '-q', 'tests.test_calc']).returncode)\n")
        return f"{sys.executable} -B {script}"

    def test_allow_dirty_runs_in_a_disposable_clone_as_the_tree_stands(self):
        self.dirty_tree()
        before = git(self.repo, "status", "--porcelain")
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", self.suite_script(), "--base", "", "--allow-dirty")
        self.assertIn("mutation: 2 mutants, 1 caught, 1 survived", out)
        self.assertIn("disposable clone", out)
        rows = [line.split("|") for line in open(self.cwds).read().splitlines()]
        self.assertEqual(len(rows), 3)  # the baseline and two mutants
        for cwd, log, deps, note in rows:
            self.assertNotEqual(cwd, self.repo)                 # never the project's tree
            self.assertEqual(log, "entry 1 entry 2 ")            # the uncommitted line came along
            self.assertEqual((deps, note), ("True", "True"))     # so did what is ignored and what is untracked
            self.assertFalse(os.path.exists(cwd), cwd)           # and the clone is gone
        self.assertEqual(git(self.repo, "status", "--porcelain"), before)

    @unittest.skipIf(os.name == "nt", "kills the runner with SIGKILL")
    def test_a_run_killed_mid_mutant_leaves_no_mutant_in_the_project(self):
        self.dirty_tree()
        source = open(os.path.join(self.repo, "calc", "fees.py")).read()
        before = git(self.repo, "status", "--porcelain")
        r = subprocess.run([sys.executable, "-I", SCRIPT, "run", "--repo", self.repo, "--mutants", self.mutants,
                            "--test", self.suite_script(kill_on="days * 20"), "--base", "", "--allow-dirty"], capture_output=True, text=True)
        self.assertEqual(r.returncode, -9, r.stdout + r.stderr)  # killed between the write and the restore
        self.assertEqual(open(os.path.join(self.repo, "calc", "fees.py")).read(), source)
        self.assertEqual(git(self.repo, "status", "--porcelain"), before)
        clone = open(self.cwds).read().splitlines()[-1].split("|")[0]
        self.addCleanup(shutil.rmtree, os.path.dirname(clone), True)
        self.assertIn("days * 20", open(os.path.join(clone, "calc", "fees.py")).read())  # the mutant stayed in the clone

    @unittest.skipIf(os.name == "nt", "POSIX permission bits")
    def test_changed_writes_a_private_mutants_file(self):
        self.add_a_slice()
        dest = os.path.join(self.tmp, "changed.json")
        with open(dest, "w") as f:
            f.write("[]")
        os.chmod(dest, 0o644)  # a file already there is narrowed too
        for path in (dest, os.path.join(self.tmp, "fresh.json")):
            self.run_tool("changed", "--repo", self.repo, "--base", "main", "--out", path)
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600, path)

    def test_remove_mutants_removes_the_file_when_the_pass_ends_or_fails(self):
        keep = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", TEST_CMD, "--base", "")
        self.assertIn("mutation: 2 mutants", keep)
        self.assertTrue(os.path.exists(self.mutants))  # a reviewer's own file stays without the flag
        copy = os.path.join(self.tmp, "generated.json")
        shutil.copy(self.mutants, copy)
        self.run_tool("run", "--repo", self.repo, "--mutants", copy, "--test", f"{sys.executable} -c 'raise SystemExit(1)'",
                      "--base", "", "--remove-mutants", expect=2)
        self.assertFalse(os.path.exists(copy))  # the baseline failed and the file is gone all the same
        shutil.copy(self.mutants, copy)
        self.run_tool("run", "--repo", self.repo, "--mutants", copy, "--test", TEST_CMD, "--base", "", "--remove-mutants")
        self.assertFalse(os.path.exists(copy))

    def test_a_base_that_is_not_a_ref_is_said_not_swallowed(self):
        report = os.path.join(self.tmp, "report.md")
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", TEST_CMD,
                            "--base", "no-such-ref", "--out", report)
        self.assertIn("`no-such-ref` is not a ref", out)
        self.assertNotIn("In the diff against", open(report, encoding="utf-8").read())

    def test_runner_failure_is_an_error_not_a_kill(self):
        # the second mutant breaks the module's syntax, so the runner fails before any test runs: not a kill
        with open(self.mutants, "w") as f:
            json.dump([{"file": "calc/fees.py", "old": "days * 25", "new": "days * 20", "note": "rate"},
                       {"file": "calc/fees.py", "old": "def late_fee(days):", "new": "def late_fee(days)", "note": "syntax"}], f)
        report = os.path.join(self.tmp, "report.md")
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", TEST_CMD, "--base", "", "--out", report)
        self.assertIn("CAUGHT", out)
        self.assertIn("ERROR (exit", out)
        with open(report, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("Mutants: **1**. Caught: **1**. Survived: **0**. Kill rate **100.0%**. Not counted, the runner itself failed: 2.", text)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")


    def test_a_mutant_that_hangs_the_suite_ends_at_the_timeout_and_is_listed_apart(self):
        # the break makes the rule wait for ever: the suite never ends, and a 30-minute default cost a slice review hours
        with open(self.mutants, "w") as f:
            json.dump([{"file": "calc/fees.py", "old": "days * 25", "new": "__import__('time').sleep(600) or days * 25", "note": "late_fee: waits"},
                       {"file": "calc/fees.py", "old": "'none' if days <= 0 else 'due'", "new": "'due'", "note": "label: always due"}], f)
        report = os.path.join(self.tmp, "report.md")
        started = time.monotonic()
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", TEST_CMD, "--base", "", "--timeout", "3", "--out", report)
        self.assertLess(time.monotonic() - started, 60)
        self.assertIn("HUNG (ended after 3 s)", out)
        self.assertIn("mutation: 2 mutants, 1 caught, 1 survived, 1 of the caught by a hang", out)
        with open(report, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("| 1 | calc/fees.py:4 | late_fee: waits | HUNG (the suite did not end in 3 s; counted as caught) | n/a |", text)
        self.assertIn("Caught by a hang, not by a failing assertion: 1 (`calc/fees.py:4`)", text)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_the_default_timeout_comes_from_the_baseline(self):
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", TEST_CMD, "--base", "")
        self.assertIn("2 mutants, each ended after 60 s", out)  # three times a sub-second baseline, never under the floor

    def test_a_spent_budget_lists_the_rest_as_not_run(self):
        slow = f"sh -c 'sleep 1.5; {TEST_CMD}'"
        report = os.path.join(self.tmp, "report.md")
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", slow, "--base", "", "--budget", "1", "--out", report)
        self.assertIn("mutation: 1 mutants, 1 caught, 0 survived, 1 not run (the 1 s budget)", out)
        with open(report, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("| 2 | calc/fees.py:8 | label: always due | NOT RUN (the pass's time budget ended; not counted) | n/a |", text)
        self.assertIn("Not run, the time budget (1 s) ended first: 2.", text)

    def test_first_failure_drops_the_single_test_list_and_says_so(self):
        report = os.path.join(self.tmp, "report.md")
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", TEST_CMD, "--base", "", "--first-failure", "--out", report)
        self.assertIn("each stopped at its first failing test", out)
        self.assertIn("mutation: 2 mutants, 1 caught, 1 survived", out)
        with open(report, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("ended at its first failing test", text)
        self.assertNotIn("Kills that hang on a single test", text)


class AnUnsteadyTest(unittest.TestCase):
    """A suite with a test that fails on the unchanged tree now and then
    (a real project's did, one baseline run in two)."""

    setUp, tearDown, run_tool = MutationPass.setUp, MutationPass.tearDown, MutationPass.run_tool

    def test_it_does_not_stop_the_pass_and_is_never_a_catch(self):
        # run 1: the unsteady test fails on the unchanged tree; run 2: the baseline passes;
        # run 3 (mutant 1): only the unsteady test fails; run 4 (mutant 2): a real test fails
        counter = os.path.join(self.tmp, "runs")
        script = os.path.join(self.tmp, "suite.py")
        with open(script, "w") as f:
            f.write("import sys\n"
                    f"p = {counter!r}\n"
                    "try:\n    n = int(open(p).read()) + 1\nexcept OSError:\n    n = 1\n"
                    "open(p, 'w').write(str(n))\n"
                    "if n in (1, 3):\n    print('FAIL: test_two_copies_race (t.Race)'); sys.exit(1)\n"
                    "if n == 4:\n    print('FAIL: test_charges_per_day (t.Fees)'); sys.exit(1)\n"
                    "print('OK')\n")
        report = os.path.join(self.tmp, "report.md")
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", f"{sys.executable} {script}",
                            "--base", "", "--first-failure", "--out", report)
        self.assertIn("the baseline failed on attempt 1 (1 failed); trying again", out)
        self.assertIn("1 unsteady test(s) failed on the unchanged tree and will not count as a catch: test_two_copies_race (t.Race)", out)
        self.assertIn("SURVIVED (only an unsteady test failed)", out)
        self.assertIn("mutation: 2 mutants, 1 caught, 1 survived", out)
        with open(report, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("| 1 | calc/fees.py:4 | late_fee: the daily rate | SURVIVED (only an unsteady test failed) | n/a |", text)
        self.assertIn("Unsteady tests, which failed on the unchanged tree before the baseline passed and count as no catch: test_two_copies_race (t.Race).", text)

    def test_a_baseline_that_fails_three_times_is_still_refused(self):
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants,
                            "--test", f"{sys.executable} -c \"print('FAIL: test_x (t.X)'); raise SystemExit(1)\"", "--base", "", expect=2)
        self.assertIn("the baseline fails", out)
        self.assertIn("nothing mutated", out)


def load_script():
    import importlib.util
    spec = importlib.util.spec_from_file_location("mutation_pass", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(hasattr(os, "killpg") and shutil.which("sh") and shutil.which("pgrep"), "needs process groups")
class RunCmd(unittest.TestCase):
    """The command runner, on commands that print and wait."""

    def test_a_timeout_ends_everything_the_command_started(self):
        # a hung suite left 36 test processes behind on a real project, loading every mutant after it
        mp = load_script()
        code, out, secs = mp.run_cmd("sh -c 'sleep 31337 & sleep 31337'", os.getcwd(), 1)
        self.assertEqual(code, mp.TIMED_OUT)
        self.assertLess(secs, 20)
        time.sleep(0.5)
        left = subprocess.run(["pgrep", "-f", "sleep 31337"], capture_output=True, text=True).stdout.split()
        self.assertEqual(left, [])

    def test_changed_leaves_out_code_no_test_loads(self):
        # a 40-mutant cap was being spent on a lint configuration and the capture file CI alone runs
        mp = load_script()
        for path in ("eslint.limits.config.js", "tools/vite.config.ts", "screens/states.mjs", "screens/capture.mjs", ".eslintrc.cjs", "conftest.py"):
            self.assertTrue(mp.outside_the_suite(path), path)
        # a project's own code under a top-level `screens/` is not the capture's
        for path in ("src/web/server.ts", "src/config.ts", "app/screens.py", "src/screens/list.ts", "screens/Home.tsx", "screens/home/index.ts"):
            self.assertFalse(mp.outside_the_suite(path), path)

    def test_first_failure_ends_the_command_at_the_first_failing_test(self):
        mp = load_script()
        cmd = f"{sys.executable} -u -c \"print('✔ adds (1ms)'); print('✖ refuses at open (2ms)'); import time; time.sleep(300)\""
        code, out, secs = mp.run_cmd(cmd, os.getcwd(), 120, first_failure=True)
        self.assertEqual(code, mp.STOPPED_EARLY)
        self.assertLess(secs, 30)
        self.assertEqual(mp.read_result(code, out), ("caught", 1, ["refuses at open"]))
        # without the option the same command runs to its timeout
        code, _, _ = mp.run_cmd(cmd, os.getcwd(), 2)
        self.assertEqual(code, mp.TIMED_OUT)


class ReadResult(unittest.TestCase):
    """The runners' outputs, read without running anything."""

    def read(self, code, output):
        import importlib.util
        spec = importlib.util.spec_from_file_location("mutation_pass", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.read_result(code, output)

    def test_node_spec_reporter_counts_fails_and_names_tests(self):
        # node --test prints the spec reporter off a TTY since Node 20: no `not ok` or `# fail` lines
        output = ("✔ adds (one passes) (0.28ms)\n✖ multiplies, 3 x 3 (0.29ms)\n▶ group\n  ✖ inner fails (4.3ms)\n✖ group (4.4ms)\n"
                  "ℹ tests 3\nℹ suites 1\nℹ pass 1\nℹ fail 2\nℹ cancelled 0\nℹ skipped 0\nℹ todo 0\nℹ duration_ms 51.4\n\n"
                  "✖ failing tests:\n\ntest at s.test.cjs:4:1\n✖ multiplies, 3 x 3 (0.29ms)\n  AssertionError\n")
        self.assertEqual(self.read(1, output), ("caught", 2, ["multiplies, 3 x 3", "inner fails", "group"]))
        self.assertEqual(self.read(0, "✔ adds (0.28ms)\nℹ tests 1\nℹ pass 1\nℹ fail 0\n"), ("survived", 0, []))

    def test_a_timeout_after_a_named_failure_is_a_catch(self):
        # the tests caught the break, then the run hung: a kill, not a runner error
        out = "✖ refuses at open (1ms)\n[timed out after 1800 s]"
        self.assertEqual(self.read(-1, out), ("caught", 1, ["refuses at open"]))
        self.assertEqual(self.read(-1, "✔ adds (1ms)\n[timed out after 1800 s]"), ("error", None, []))

    def test_a_cancelled_test_is_a_catch(self):
        # node counts a test ended by its own timeout as cancelled, not failed: `fail 0, cancelled 1`, exit 1
        out = ("✔ adds (1ms)\n✖ tells me the app is closing (5001ms)\nℹ tests 2\nℹ pass 1\nℹ fail 0\nℹ cancelled 1\n")
        self.assertEqual(self.read(1, out), ("caught", 1, ["tells me the app is closing"]))
        # and one failed with two cancelled beside it is three, the number of names
        out = "✖ a (1ms)\n✖ b (5001ms)\n✖ c (5001ms)\nℹ fail 1\nℹ cancelled 2\n"
        self.assertEqual(self.read(1, out), ("caught", 3, ["a", "b", "c"]))
        self.assertEqual(self.read(1, "not ok 1 - waits\n# fail 0\n# cancelled 1\n"), ("caught", 1, ["waits"]))

    def test_node_tap_reporter_still_reads(self):
        self.assertEqual(self.read(1, "not ok 1 - multiplies\n# tests 2\n# pass 1\n# fail 1\n"), ("caught", 1, ["multiplies"]))


STATE = os.path.join(ROOT, "evals", "fixtures", "library-app", "code-plants", "loop", "state.sh")


def node_major():
    node = shutil.which("node")
    try:
        return int(subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip().lstrip("v").split(".")[0]) if node else 0
    except ValueError:
        return 0


@unittest.skipUnless(shutil.which("bash") and node_major() >= 24, "needs bash and Node 24 for the fixture's suite")
class TheFixturesSlice(unittest.TestCase):
    """TODO.md's B4 "done when", the tool's half: on the library fixture's
    built slice, the rule no test holds comes back as a survivor of the
    changed-lines pass the `slice-review-r0` state runs for real."""

    def test_the_unguarded_rule_survives_and_the_report_says_where(self):
        project = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, project, True)
        r = subprocess.run(["bash", STATE, "slice-review-r0"], cwd=project, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-400:])
        with open(os.path.join(project, "docs", "cancel-hold", "implementation", "slice-mutation.md"), encoding="utf-8") as f:
            report = f.read()
        self.assertRegex(report, r"\| lending/cancel-hold\.ts:\d+ \| line \d+: > to >= \| SURVIVED \| yes \|")
        self.assertRegex(report, r"\| lending/cancel-hold\.ts:\d+ \| line \d+: \|\| to && \| SURVIVED \| yes \|")
        self.assertRegex(report, r"Mutants: \*\*11\*\*\. Caught: \*\*9\*\*\. Survived: \*\*2\*\*")
        self.assertNotIn("cardNumber.length", report)  # counts, lines and test names only
        status = subprocess.run(["git", "-C", project, "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True).stdout
        self.assertEqual(status.strip(), "M docs/cancel-hold/orchestrator-log.md")


if __name__ == "__main__":
    unittest.main(verbosity=1)
