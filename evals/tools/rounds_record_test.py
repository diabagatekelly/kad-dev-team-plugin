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


if __name__ == "__main__":
    unittest.main(verbosity=1)
