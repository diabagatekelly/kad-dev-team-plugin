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


if __name__ == "__main__":
    unittest.main(verbosity=1)
