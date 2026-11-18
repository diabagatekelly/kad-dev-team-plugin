#!/usr/bin/env python3
"""The gate's per-project checks (`gate-checks.json`), without a model.

Two halves. The first holds the mechanism on a scratch project whose
checks are one-line Python commands: the file's three entry forms and
what a malformed one says, the count against the baseline (the existing
violations pass, one more fails, fewer is said and passes), a tool that
did not run, and `--record-gate-baselines`.

The second is TODO.md's B1 "done when" on the library fixture, whose
chunk-loop base carries the eight categories (stand-in commands, since
no tool can be installed in the eval sandbox): chunk 1 as the fixture
builds it passes the gate with every category held, and one planted
violation per category fails it on that category's line. Needs `bash`
and a Node that runs the fixture's suite (24); skipped without them.

Usage: python3 -I evals/tools/gate_checks_test.py
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "skills", "orchestrator", "scripts", "validation_gate.py")
STATE = os.path.join(ROOT, "evals", "fixtures", "library-app", "code-plants", "loop", "state.sh")

spec = importlib.util.spec_from_file_location("validation_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
sys.path.insert(0, os.path.dirname(SCRIPT))
spec.loader.exec_module(gate)

PY = sys.executable


def printer(*lines):
    """A command that prints the lines and exits 1 when there is one."""
    return f"{PY} -c \"import sys; ls={list(lines)!r}; print('\\n'.join(ls)); sys.exit(1 if ls else 0)\""


def covered(category, by="suite"):
    return {"category": category, "covered_by": by}


def a_full_file(*entries):
    """`entries` first, then every category they leave out as covered by the suite."""
    named = {e["category"] for e in entries}
    return {"checks": list(entries) + [covered(c) for c in gate.CATEGORIES if c not in named]}


class TheFile(unittest.TestCase):
    def setUp(self):
        self.project = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.project, ignore_errors=True)

    def write(self, data):
        with open(os.path.join(self.project, "gate-checks.json"), "w", encoding="utf-8") as f:
            f.write(data if isinstance(data, str) else json.dumps(data))

    def test_no_file_is_none_and_a_whole_file_has_no_problem(self):
        self.assertEqual(gate.load_gate_checks(self.project), (None, []))
        self.write(a_full_file({"category": "duplication", "name": "dup", "cmd": "x", "count": "^v", "baseline": 3},
                               {"category": "unused code", "not_picked": "one file, nothing to be unused"}))
        entries, problems = gate.load_gate_checks(self.project)
        self.assertEqual(problems, [])
        self.assertEqual(len(entries), len(gate.CATEGORIES))

    def test_a_missing_category_is_a_problem_not_a_default(self):
        self.write({"checks": [covered(c) for c in gate.CATEGORIES if c != "duplication"]})
        self.assertEqual(gate.load_gate_checks(self.project)[1], ["no entry for the category 'duplication'"])

    def test_malformed_entries_each_say_what_is_wrong(self):
        self.write("{not json")
        self.assertIn("cannot be read as JSON", gate.load_gate_checks(self.project)[1][0])
        self.write({"checks": {}})
        self.assertIn('no "checks" list', gate.load_gate_checks(self.project)[1][0])
        cases = [
            ({"category": "speed", "cmd": "x", "name": "x"}, "unknown category 'speed'"),
            ({"category": "duplication", "cmd": "x", "name": "x", "covered_by": "lint"}, "one of cmd, covered_by or not_picked, not 2"),
            ({"category": "duplication"}, "one of cmd, covered_by or not_picked, not 0"),
            ({"category": "duplication", "cmd": "x"}, "needs its own name"),
            ({"category": "duplication", "cmd": "x", "name": "Dup Check"}, "needs its own name"),
            ({"category": "duplication", "cmd": " ", "name": "dup"}, "cmd is empty"),
            ({"category": "duplication", "cmd": "x", "name": "dup", "count": "("}, "count is not a regular expression"),
            ({"category": "duplication", "cmd": "x", "name": "dup", "count": "v", "baseline": -1}, "baseline must be a whole number"),
            ({"category": "duplication", "cmd": "x", "name": "dup", "baseline": 2}, "a baseline needs a count regex"),
            ({"category": "duplication", "covered_by": "the reviewer"}, "covered_by must be one of"),
            ({"category": "duplication", "not_picked": ""}, "not_picked needs its reason"),
        ]
        for entry, said in cases:
            self.write(a_full_file(entry) if entry["category"] in gate.CATEGORIES else {"checks": [entry]})
            problems = gate.load_gate_checks(self.project)[1]
            self.assertTrue(any(said in p for p in problems), (entry, problems))

    def test_two_entries_cannot_share_a_name(self):
        self.write(a_full_file({"category": "duplication", "name": "scan", "cmd": "x"},
                               {"category": "unused code", "name": "scan", "cmd": "y"}))
        self.assertTrue(any("needs its own name" in p for p in gate.load_gate_checks(self.project)[1]))


class TheCount(unittest.TestCase):
    def test_matches_are_counted_and_a_group_is_read_as_the_number(self):
        out = "violation: a\nok\nviolation: b\nTotal: 7 clones\nTotal: 9 clones\n"
        self.assertEqual(gate.count_violations("^violation: ", out), 2)
        self.assertEqual(gate.count_violations(r"Total: (\d+) clones", out), 9)
        self.assertEqual(gate.count_violations("^nothing", out), 0)
        self.assertIsNone(gate.count_violations(r"Found (\d+)", out))
        self.assertIsNone(gate.count_violations(r"Total: (\w+) clones", "Total: many clones"))


class OneCheck(unittest.TestCase):
    def setUp(self):
        self.project = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.project, ignore_errors=True)

    def check(self, **entry):
        return gate.run_gate_check(self.project, {"category": "duplication", "name": "dup", **entry}, 60)[0]

    def test_the_existing_violations_pass_one_more_fails_fewer_passes(self):
        cmd = printer("violation: a", "violation: b")
        self.assertTrue(self.check(cmd=cmd, count="^violation", baseline=2)["passed"])
        r = self.check(cmd=cmd, count="^violation", baseline=1)
        self.assertFalse(r["passed"])
        self.assertEqual((r["found"], r["baseline"]), (2, 1))
        self.assertEqual(gate.gate_check_line("check:dup", r).split(" (")[0],
                         "FAIL  check dup [duplication]: 2 found, baseline 1")
        self.assertTrue(self.check(cmd=cmd, count="^violation", baseline=5)["passed"])
        self.assertFalse(self.check(cmd=cmd, count="^violation")["passed"], "no baseline is a baseline of none")

    def test_without_a_count_the_exit_code_decides(self):
        self.assertTrue(self.check(cmd=printer())["passed"])
        r = self.check(cmd=printer("x"))
        self.assertFalse(r["passed"])
        self.assertIn("exit 1", gate.gate_check_line("check:dup", r))

    def test_a_tool_that_did_not_run_fails_whatever_the_baseline(self):
        r = self.check(cmd="no-such-tool-anywhere --json", count="^violation", baseline=50)
        self.assertFalse(r["passed"])
        self.assertIn("not on PATH", r["reason"])
        r = self.check(cmd=f"{PY} -c \"import sys; sys.exit(2)\"", count="^violation", baseline=50)
        self.assertFalse(r["passed"])
        self.assertIn("the tool did not run", r["reason"])
        r = self.check(cmd=printer("Crashed"), count=r"Found (\d+) clones", baseline=50)
        self.assertFalse(r["passed"])
        self.assertIn("no count read", r["reason"])

    def test_a_clean_tool_with_a_group_regex_reads_zero(self):
        r = self.check(cmd=f"{PY} -c \"print('Found 0 clones')\"", count=r"Found (\d+) clones", baseline=0)
        self.assertTrue(r["passed"], r)

    def test_covered_by_passes_only_when_that_check_ran(self):
        entries = [covered("duplication", "lint"), {"category": "unused code", "not_picked": "why"}]
        results, _, held = gate.run_gate_checks(self.project, entries, {"lint": {"passed": True}}, 60)
        self.assertTrue(results["covered:duplication"]["passed"])
        self.assertEqual(held, ["duplication"])
        self.assertTrue(results["not-picked:unused code"]["skipped"])
        for checks in ({"lint": {"passed": True, "skipped": True, "reason": "no lint script"}}, {}):
            results, _, held = gate.run_gate_checks(self.project, entries[:1], checks, 60)
            self.assertFalse(results["covered:duplication"]["passed"])
            self.assertEqual(held, [])
            self.assertIn("did not run", gate.gate_check_line("covered:duplication", results["covered:duplication"]))


class ChecksOnly(unittest.TestCase):
    """What a builder or a fixer runs before it commits."""

    def setUp(self):
        self.project = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.project, ignore_errors=True)

    def run_checks(self, *entries):
        with open(os.path.join(self.project, "gate-checks.json"), "w") as f:
            json.dump(a_full_file(*entries), f)
        return subprocess.run([PY, "-I", SCRIPT, "--project", self.project, "--checks-only"], capture_output=True, text=True)

    def test_a_count_over_its_baseline_fails_before_any_commit(self):
        r = self.run_checks({"category": "duplication", "name": "dup", "cmd": printer("violation: a", "violation: b"),
                             "count": "^violation", "baseline": 1})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("FAIL  check dup [duplication]: 2 found, baseline 1", r.stdout)
        self.assertEqual(r.stdout.strip().splitlines()[-1], "checks: FAIL")
        self.assertIn("violation: b", r.stdout)  # the tool's own lines, so the count can be cleared

    def test_at_the_baseline_it_passes_and_runs_no_suite(self):
        r = self.run_checks({"category": "duplication", "name": "dup", "cmd": printer("violation: a"), "count": "^violation", "baseline": 1})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.strip().splitlines()[-1], "checks: PASS")
        self.assertIn("left to the gate's suite check", r.stdout)
        self.assertNotIn("suite", [line.split()[1] for line in r.stdout.splitlines() if line.startswith(("PASS", "FAIL"))])

    def test_a_project_with_no_file_still_passes(self):
        r = subprocess.run([PY, "-I", SCRIPT, "--project", self.project, "--checks-only"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("SKIP  gate-checks: no gate-checks.json in the project", r.stdout)


class RecordingTheBaselines(unittest.TestCase):
    def setUp(self):
        self.project = tempfile.mkdtemp()
        self.path = os.path.join(self.project, "gate-checks.json")

    def tearDown(self):
        shutil.rmtree(self.project, ignore_errors=True)

    def record(self):
        return subprocess.run([PY, "-I", SCRIPT, "--project", self.project, "--record-gate-baselines"],
                              capture_output=True, text=True)

    def test_each_counted_check_gets_what_it_counted(self):
        data = a_full_file({"category": "duplication", "name": "dup", "cmd": printer("violation: a", "violation: b"), "count": "^violation"},
                           {"category": "unused code", "name": "unused", "cmd": printer(), "count": "^violation", "baseline": 4},
                           {"category": "secret and workflow scans", "name": "secrets", "cmd": printer()})
        with open(self.path, "w") as f:
            json.dump(data, f)
        r = self.record()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("baseline dup [duplication]: 0 -> 2", r.stdout)
        self.assertIn("baseline unused [unused code]: 4 -> 0", r.stdout)
        with open(self.path) as f:
            after = {e.get("name"): e for e in json.load(f)["checks"]}
        self.assertEqual(after["dup"]["baseline"], 2)
        self.assertEqual(after["unused"]["baseline"], 0)
        self.assertNotIn("baseline", after["secrets"])

    def test_a_tool_that_does_not_run_records_nothing(self):
        data = a_full_file({"category": "duplication", "name": "dup", "cmd": "no-such-tool-anywhere", "count": "^violation", "baseline": 3})
        with open(self.path, "w") as f:
            json.dump(data, f)
        r = self.record()
        self.assertEqual(r.returncode, 1)
        self.assertIn("gate baselines: not recorded", r.stdout)
        with open(self.path) as f:
            self.assertEqual(json.load(f)["checks"][0]["baseline"], 3)

    def test_no_file_and_a_malformed_file_exit_1(self):
        self.assertEqual(self.record().returncode, 1)
        with open(self.path, "w") as f:
            f.write('{"checks": []}')
        r = self.record()
        self.assertEqual(r.returncode, 1)
        self.assertIn("no entry for the category", r.stdout)


def node_major():
    node = shutil.which("node")
    if not node:
        return 0
    try:
        return int(subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip().lstrip("v").split(".")[0])
    except ValueError:
        return 0


CHUNK_FILES = ["lending/hold-queue.ts", "lending/cancel-hold.ts", "infra/memory/in-memory-hold-queue.ts",
               "test/cancel-hold.test.ts", "test/in-memory-hold-queue.test.ts"]
NESTED = "\n".join("  " * i + "if (Date.now() > 0) {" for i in range(5)) + "\n" + "  " * 5 + "void 0;\n" + \
         "\n".join("  " * i + "}" for i in range(4, -1, -1)) + "\n"
BLOCK = "{\n" + "".join(f"  const step{i} = {('step' + str(i - 1) + ' + 1') if i else '1'};\n" for i in range(7)) + "  void step6;\n}\n"
NEVER_RUN = ("function plantedNeverRun(days: number): number {\n  if (days > 30) {\n    return 30;\n  }\n"
             "  if (days < 0) {\n    return 0;\n  }\n  const fee = days * 25;\n  return fee;\n}\nvoid plantedNeverRun;\n")
# One planted violation per category: (the file it is appended to, the text, the line the gate must print).
PLANTS = {
    "type-aware lint": ("lending/cancel-hold.ts", "Promise.resolve(1).then(() => undefined);\n",
                        "FAIL  check floating-promise [type-aware lint]: 1 found, baseline 0"),
    "stricter compiler flags": ("lending/cancel-hold.ts", "const plantedAny: any = 1;\nvoid plantedAny;\n",
                                "FAIL  check any-type [stricter compiler flags]: 1 found, baseline 0"),
    "complexity and length limits": ("lending/cancel-hold.ts", NESTED,
                                     "FAIL  check deep-nesting [complexity and length limits]: 5 found, baseline 4"),
    "duplication": ("lending/cancel-hold.ts", BLOCK + BLOCK, "FAIL  check duplication [duplication]: 2 found, baseline 1"),
    "unused code": ("lending/cancel-hold.ts", "export const plantedUnused = 1;\n",
                    "FAIL  check unused-export [unused code]: 11 found, baseline 10"),
    "changed-line coverage": ("lending/cancel-hold.ts", NEVER_RUN, "FAIL  coverage"),
    "test timeouts and random order": ("test/cancel-hold.test.ts",
                                       "test('planted: a test that never ends', async () => {\n"
                                       "  await new Promise((resolve) => setTimeout(resolve, 7000));\n});\n",
                                       "FAIL  suite"),
    "secret and workflow scans": ("lending/cancel-hold.ts", "const plantedKey = '" + "LIBKEY-" + "0123456789ABCDEF01234567" + "';\nvoid plantedKey;\n",
                                  "FAIL  check secret-scan [secret and workflow scans]: 1 found, baseline 0"),
}


@unittest.skipUnless(shutil.which("bash") and node_major() >= 24, "needs bash and Node 24 for the fixture's suite")
class TheLibraryFixtureCarriesTheChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = os.path.realpath(tempfile.mkdtemp())
        r = subprocess.run(["bash", STATE, "chunk1-built"], cwd=cls.project, capture_output=True, text=True)
        if r.returncode != 0:
            raise unittest.SkipTest("the fixture could not be scaffolded: " + r.stderr[-300:])
        cls.base = subprocess.run([gate.find_git(), "-C", cls.project, "rev-parse", "HEAD~2"],
                                  capture_output=True, text=True).stdout.strip()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.project, ignore_errors=True)

    def tearDown(self):
        subprocess.run([gate.find_git(), "-C", self.project, "checkout", "-q", "--", "lending", "test"], check=True)

    def run_gate(self):
        args = [PY, "-I", SCRIPT, "--project", self.project, "--base", self.base, "--test-cmd", "npm test", "--coverage",
                "--allow", "docs/cancel-hold/implementation/", "--allow", "docs/cancel-hold/orchestrator-log.md",
                "--module-dir", "lending/", "--module-dir", "infra/memory/", "--planning", os.path.join(self.project, "docs/cancel-hold")]
        for f in CHUNK_FILES:
            args += ["--allow", f]
        return subprocess.run(args, capture_output=True, text=True)

    def test_a_clean_chunk_passes_with_every_category_held(self):
        r = self.run_gate()
        self.assertEqual(r.returncode, 0, r.stdout)
        covers = [line for line in r.stdout.splitlines() if line.startswith("INFO  gate covers: ")]
        self.assertEqual(len(covers), 1, r.stdout)
        for category in gate.CATEGORIES:
            self.assertIn(category, covers[0])
        # the older code's violations are the baseline, not a failure
        self.assertIn("PASS  check unused-export [unused code]: 10 found, baseline 10", r.stdout)
        self.assertIn("PASS  check deep-nesting [complexity and length limits]: 4 found, baseline 4", r.stdout)
        self.assertRegex(r.stdout, r"PASS  coverage changed lines 100% \(0 of \d+ not run\)")

    def test_a_planted_violation_of_each_category_fails_the_gate_on_its_line(self):
        self.assertEqual(set(PLANTS), set(gate.CATEGORIES))
        for category, (path, text, line) in PLANTS.items():
            with self.subTest(category=category):
                with open(os.path.join(self.project, path), "a", encoding="utf-8") as f:
                    f.write(text)
                r = self.run_gate()
                self.tearDown()
                self.assertEqual(r.returncode, 1, r.stdout)
                failed = [l for l in r.stdout.splitlines() if l.startswith("FAIL  ")]
                self.assertEqual(len(failed), 1, r.stdout)
                self.assertTrue(failed[0].startswith(line), failed[0])
                if category == "changed-line coverage":
                    self.assertRegex(failed[0], r"changed lines \d+(\.\d+)?% \(\d+ of \d+ not run; lending/cancel-hold\.ts:")
                self.assertEqual(r.stdout.strip().splitlines()[-1], "validation gate: FAIL")


if __name__ == "__main__":
    unittest.main(verbosity=1)
