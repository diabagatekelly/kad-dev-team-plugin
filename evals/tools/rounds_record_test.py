#!/usr/bin/env python3
"""`rounds_record.py --last`, without a model (TODO.md's F5): the review of
a scope's last fix has no fixer after it, so what it raises stands. Its
Critical, High and Medium are class `last-fix`, printed as `standing:`
lines, listed by `--standing` (so delivery files the Mediums), and the
fragment reads `last <C>/<H>/<M>`; a round recorded without the flag is
as it was.

Usage: python3 -I evals/tools/rounds_record_test.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "skills", "orchestrator", "scripts", "rounds_record.py")
REPORT = """# Review

## Findings

### The rejection reason is built twice

**Severity:** High
**Location:** lending/cancel-hold.ts:14
**Category:** behaviour

### A name that says less than the code

**Severity:** Medium
**Location:** lending/cancel-hold.ts:20
**Category:** naming
"""


class TheLastFixReview(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.sidecar = os.path.join(self.tmp, "rounds-slice-001.jsonl")
        self.report = os.path.join(self.tmp, "chunk-1-last-review.md")
        with open(self.report, "w", encoding="utf-8") as f:
            f.write(REPORT)

    def run_tool(self, *args):
        r = subprocess.run([sys.executable, "-I", SCRIPT, "--sidecar", self.sidecar, *args], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout.strip().splitlines()

    def test_what_it_raises_stands_and_is_listed(self):
        out = self.run_tool("--report", self.report, "--chunk", "1", "--round", "2", "--last", "--fix", "abc1234")
        self.assertEqual(out[-1], "last 0/1/1")
        self.assertEqual([l for l in out if l.startswith("standing: ")],
                         ["standing: High — The rejection reason is built twice (lending/cancel-hold.ts:14)",
                          "standing: Medium — A name that says less than the code (lending/cancel-hold.ts:20)"])
        with open(self.sidecar, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f]
        self.assertEqual({r["class"] for r in rows}, {"last-fix"})
        self.assertEqual({r["round"] for r in rows}, {2})
        listed = self.run_tool("--standing")
        self.assertEqual(listed[-1], "standing 0/1/1")
        self.assertEqual(len(listed), 3)

    def test_a_round_without_the_flag_is_as_it_was(self):
        out = self.run_tool("--report", self.report, "--chunk", "1", "--round", "0")
        self.assertEqual(out[-1], "r0 0/1/1")
        self.assertEqual(self.run_tool("--standing")[-1], "standing 0/0/0")


def finding(title, where, severity="Medium"):
    return f"### {title}\n\n**Severity:** {severity}\n**Location:** {where}\n**Category:** behaviour\n\n"


class WhatAFixWrote(unittest.TestCase):
    """The regression rule on a real diff: a fix that writes one line and
    moves a helper into another file."""

    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(os.path.join(self.repo, "lending"))
        self.records = os.path.join(self.tmp, "records")
        os.makedirs(self.records)
        self.sidecar = os.path.join(self.records, "rounds-slice-001.jsonl")
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "T")
        helper = "export function reasonFor(hold) {\n  return hold.cancelled ? 'cancelled by the member' : 'expired';\n}\n"
        self.write("lending/cancel-hold.ts", "export function cancel(hold) {\n  hold.cancelled = true;\n}\n\n" + helper)
        self.write("lending/reasons.ts", "// reasons\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "the chunk")
        self.before = self.git("rev-parse", "HEAD").strip()
        # the fix: one new line in cancel-hold.ts, and the helper carried into reasons.ts as it was
        self.write("lending/cancel-hold.ts", "export function cancel(hold) {\n  hold.cancelled = true;\n  hold.cancelledAt = Date.now();\n}\n")
        self.write("lending/reasons.ts", "// reasons\n" + helper)
        self.git("add", "-A")
        self.git("commit", "-qm", "the fix")

    def git(self, *args):
        return subprocess.run(["git", "-C", self.repo, *args], capture_output=True, text=True, check=True).stdout

    def write(self, rel, text):
        with open(os.path.join(self.repo, rel), "w", encoding="utf-8") as f:
            f.write(text)

    def report(self, name, body):
        path = os.path.join(self.records, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Review\n\n## Findings\n\n" + body)
        return path

    def record(self, *args):
        r = subprocess.run([sys.executable, "-I", SCRIPT, "--sidecar", self.sidecar, "--project", self.repo,
                            "--range", f"{self.before}..HEAD", *args], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(self.sidecar, encoding="utf-8") as f:
            return r.stdout.strip().splitlines(), {row["title"]: row["class"] for row in map(json.loads, f) if "title" in row}

    def test_a_line_the_fix_moved_is_not_its_regression(self):
        self.report("chunk-1-r0-review.md", finding("An older finding", "lending/cancel-hold.ts:2"))
        r1 = self.report("chunk-1-r1-review.md",
                         finding("The timestamp uses the wall clock", "lending/cancel-hold.ts:3")
                         + finding("The reason is a bare string", "lending/reasons.ts:3")
                         + finding("The reasons file has no test", "lending/reasons.ts"))
        out, classes = self.record("--report", r1, "--chunk", "1", "--round", "1", "--fix", "abc1234")
        self.assertEqual(classes["The timestamp uses the wall clock"], "regression")   # the line the fix wrote
        self.assertEqual(classes["The reason is a bare string"], "pre-existing")       # the helper, carried over as it was
        self.assertEqual(classes["The reasons file has no test"], "pre-existing")      # a file that only had lines moved into it
        self.assertEqual(out[-1], "r1 0/0/3 (reg 1, pre 2)")

    def test_a_reviewer_that_first_looks_after_the_fix_is_first_seen(self):
        # no round-0 report of this reviewer beside it: what it finds is new to the scope, not the fixer's doing
        r1 = self.report("slice-r1-stranger.md", finding("The README's start command is wrong", "README.md:12", "High"))
        out, classes = self.record("--report", r1, "--reviewer", "stranger", "--chunk", "D", "--round", "1", "--fix", "abc1234")
        self.assertEqual(classes["The README's start command is wrong"], "first-seen")
        self.assertEqual(out[-1], "r1 0/1/0 (reg 0, pre 0, first 1)")
        self.assertEqual([l for l in out if l.startswith("standing: ")], [])
        # with its round-0 report beside it, the usual rule applies
        self.report("slice-r0-stranger.md", finding("Something else", "README.md:1"))
        out, classes = self.record("--report", r1, "--reviewer", "stranger", "--chunk", "D", "--round", "1", "--fix", "abc1234")
        self.assertEqual(classes["The README's start command is wrong"], "pre-existing")

    def test_a_line_past_the_end_of_its_file_is_classed_by_the_file(self):
        # S1 (the slice 4 review, F2): a re-reviewer read the tests through a truncated diff and cited positions
        # in the diff's output. The file the fix changed has 4 lines; line 305 of it was filed as pre-existing,
        # so a regression stood and became an issue after it was fixed.
        self.report("chunk-1-r0-review.md", finding("An older finding", "lending/cancel-hold.ts:2"))
        r1 = self.report("chunk-1-r1-review.md",
                         finding("The fix loosened the test", "lending/cancel-hold.ts:305-371")
                         + finding("A helper nobody reads", "lending/reasons.ts:300"))
        out, classes = self.record("--report", r1, "--chunk", "1", "--round", "1", "--fix", "abc1234")
        self.assertEqual(classes["The fix loosened the test"], "regression")     # the fix wrote lines in that file
        self.assertEqual(classes["A helper nobody reads"], "pre-existing")       # that file only had lines moved into it
        notes = [l for l in out if l.startswith("location: ")]
        self.assertEqual(len(notes), 2, out)
        self.assertIn("lending/cancel-hold.ts:305 is past the end of the file (4 lines", notes[0])
        self.assertEqual(out[-1], "r1 0/0/2 (reg 1, pre 1)")


class WhatBecameOfAFinding(unittest.TestCase):
    """S2 (the slice 4 review, F3): a round's findings are marked fixed or
    declined after its fixer, so a High the fixer declined stands and a
    pre-existing finding a later fixer cleared does not."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.sidecar = os.path.join(self.tmp, "rounds-slice-004.jsonl")
        self.report = os.path.join(self.tmp, "slice-r0-cold.md")
        with open(self.report, "w", encoding="utf-8") as f:
            f.write(REPORT)

    def run_tool(self, *args, code=0):
        r = subprocess.run([sys.executable, "-I", SCRIPT, "--sidecar", self.sidecar, *args], capture_output=True, text=True)
        self.assertEqual(r.returncode, code, r.stdout + r.stderr)
        return r.stdout.strip().splitlines()

    def rows(self):
        with open(self.sidecar, encoding="utf-8") as f:
            return {row["title"]: row for row in map(json.loads, f)}

    def test_a_declined_high_stands_and_a_fixed_one_does_not(self):
        self.run_tool("--report", self.report, "--chunk", "D", "--round", "0")
        self.assertEqual(self.run_tool("--standing")[-1], "standing 0/0/0")  # nothing resolved yet: as it was
        out = self.run_tool("--resolve", "--chunk", "D", "--round", "0", "--fixed", "46cedf0",
                            "--declined", "The rejection reason", "needs the owner's decision")
        self.assertEqual(out[-1], "resolved D r0: fixed 1, declined 1")
        self.assertIn("declined: High — The rejection reason is built twice (lending/cancel-hold.ts:14): needs the owner's decision", out)
        rows = self.rows()
        self.assertEqual(rows["A name that says less than the code"]["resolution"], "fixed")
        self.assertEqual(rows["A name that says less than the code"]["fix"], "46cedf0")
        self.assertEqual(rows["The rejection reason is built twice"]["resolution"], "declined")
        self.assertEqual(rows["The rejection reason is built twice"]["declined"], "needs the owner's decision")
        self.assertIsNone(rows["The rejection reason is built twice"]["fix"])
        listed = self.run_tool("--standing")
        self.assertEqual(listed[-1], "standing 0/1/0")
        self.assertIn("declined: needs the owner's decision", listed[0])

    def test_a_standing_finding_a_later_fixer_cleared_no_longer_stands(self):
        self.run_tool("--report", self.report, "--chunk", "D", "--round", "2", "--last")
        self.assertEqual(self.run_tool("--standing")[-1], "standing 0/1/1")
        self.run_tool("--resolve", "--chunk", "D", "--round", "2", "--fixed", "b06af99")
        self.assertEqual(self.run_tool("--standing")[-1], "standing 0/0/0")

    def test_a_title_that_names_no_finding_or_two_changes_nothing(self):
        self.run_tool("--report", self.report, "--chunk", "D", "--round", "0")
        with open(self.sidecar, encoding="utf-8") as f:
            before = f.read()
        out = self.run_tool("--resolve", "--chunk", "D", "--round", "0", "--fixed", "46cedf0",
                            "--declined", "No such finding", "why", code=1)
        self.assertTrue(any("names no finding" in l for l in out), out)
        out = self.run_tool("--resolve", "--chunk", "D", "--round", "0", "--fixed", "46cedf0", "--declined", "the", "why", code=1)
        self.assertTrue(any("names 2 findings" in l for l in out), out)
        with open(self.sidecar, encoding="utf-8") as f:
            self.assertEqual(f.read(), before)
        out = self.run_tool("--resolve", "--chunk", "D", "--round", "7", "--fixed", "46cedf0", code=1)
        self.assertTrue(any("no finding recorded" in l for l in out), out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
