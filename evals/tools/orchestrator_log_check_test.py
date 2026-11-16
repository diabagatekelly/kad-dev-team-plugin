#!/usr/bin/env python3
"""The log checker's reading of a fix round, without a model: a fix of
several commits is one round whether its hashes are written with commas
or with spaces between them (TODO.md's F3: an r2 fix of two commits
written `r2 fix a1b2c3d e4f5a6b gate PASS` was read as no r2 fix, and the
C line reported as "r1 found 1 regression but no `r2 fix` is logged").

Usage: python3 -I evals/tools/orchestrator_log_check_test.py
"""
import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("orchestrator_log_check", os.path.join(HERE, "orchestrator_log_check.py"))
check = importlib.util.module_from_spec(spec)
sys.path.insert(0, HERE)
spec.loader.exec_module(check)

C_LINE = ("`Cancel a hold`; sonnet 41t 6m; commits `1111111`; gate `PASS`; deviations `0`; review `co tq` r0 `0/0/2`; "
          "smoke `PASS`; r1 fix `2222222` → `0/0/1` (reg 1, pre 0); {r2}; standing `0/0/0`")


def errors(line):
    findings = []
    check.check_rounds("entry 9", "chunk 1", line, findings, v4=True)
    return [text for level, _, text in findings if level == "ERROR"]


class AFixOfSeveralCommits(unittest.TestCase):
    def test_r2_with_spaces_between_its_hashes_is_read(self):
        for r2 in ("r2 fix `3333333` `4444444` gate PASS", "r2 fix 3333333 4444444 gate PASS",
                   "r2 fix `3333333` `4444444` `5555555` gate `PASS`", "r2 fix `3333333`, `4444444` gate PASS",
                   "r2 fix `3333333` gate PASS"):
            line = C_LINE.format(r2=r2)
            rounds = check.rounds_of(line)
            self.assertEqual([(n, sha) for n, sha, *_ in rounds], [(1, "2222222"), (2, "3333333")], r2)
            self.assertEqual(errors(line), [], r2)

    def test_r1_with_spaces_between_its_hashes_keeps_its_counts(self):
        line = "review `co tq` r0 `0/0/2`; smoke `PASS`; r1 fix `2222222` `6666666` → `0/0/0` (reg 0, pre 0); standing `0/0/0`"
        self.assertEqual(check.rounds_of(line), [(1, "2222222", (0, 0, 0, 0), 0, 0)])
        self.assertEqual(errors(line), [])

    def test_a_missing_r2_is_still_an_error(self):
        line = C_LINE.format(r2="owed `0`")
        self.assertEqual(len(errors(line)), 1)
        self.assertIn("no `r2 fix` is logged", errors(line)[0])

    def test_a_word_after_the_hash_is_not_a_second_hash(self):
        # `added` and `decade` are hex letters only in part; neither is seven hex characters
        line = "r0 `0/0/1`; smoke `PASS`; r1 fix `2222222` added a guard → `0/0/0` (reg 0, pre 0)"
        self.assertEqual(check.rounds_of(line), [(1, "2222222", (0, 0, 0, 0), 0, 0)])


if __name__ == "__main__":
    unittest.main(verbosity=1)
