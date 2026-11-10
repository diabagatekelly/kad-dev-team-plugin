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
SCRIPT = os.path.join(ROOT, "evals", "tools", "mutation_pass.py")
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

    def test_run_refuses_a_dirty_tree_and_a_failing_baseline(self):
        with open(os.path.join(self.repo, "scratch.txt"), "w") as f:
            f.write("x")
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", TEST_CMD, "--base", "", expect=1)
        self.assertIn("not clean", out)
        os.remove(os.path.join(self.repo, "scratch.txt"))
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", f"{sys.executable} -c 'raise SystemExit(1)'", "--base", "", expect=2)
        self.assertIn("baseline fails", out)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_run_reports_caught_and_survived_and_restores(self):
        report = os.path.join(self.tmp, "report.md")
        log = os.path.join(self.tmp, "log.jsonl")
        out = self.run_tool("run", "--repo", self.repo, "--mutants", self.mutants, "--test", TEST_CMD,
                            "--base", "", "--out", report, "--log", log, "--title", "fees")
        self.assertIn("CAUGHT (1 failed)", out)
        self.assertIn("SURVIVED", out)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")
        text = open(report, encoding="utf-8").read()
        self.assertIn("| 1 | calc/fees.py:4 | late_fee: the daily rate | CAUGHT (1 failed) by test_charges_per_day (tests.test_calc.Fees) | n/a |", text)
        self.assertIn("| 2 | calc/fees.py:8 | label: always due | SURVIVED | n/a |", text)
        self.assertIn("Kill rate **50.0%**", text)
        self.assertIn("Area `fees`: 1 mutants, 1 caught, **100.0%**", text)
        self.assertIn("Kills that hang on a single test: 1.", text)
        self.assertIn("**#2 `calc/fees.py:8`: label: always due.**", text)
        for secret in ("days * 20", "'due'"):
            self.assertNotIn(secret, text)
            self.assertNotIn(secret, open(log, encoding="utf-8").read())
        rows = [json.loads(l) for l in open(log, encoding="utf-8")]
        self.assertEqual([r.get("caught") for r in rows], [None, True, False])


if __name__ == "__main__":
    unittest.main(verbosity=1)
