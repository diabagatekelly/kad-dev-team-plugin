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
