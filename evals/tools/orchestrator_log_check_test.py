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

    def test_first_seen_findings_are_part_of_the_split(self):
        # `first <k>`: a reviewer that first looked after the fix; with reg and pre it makes the counts
        line = "review `co tq` r0 `0/0/2`; smoke `PASS`; r1 fix `2222222` → `0/1/2` (reg 1, pre 1, first 1); r2 fix `3333333` gate PASS; standing `0/0/2`"
        findings = []
        check.check_rounds("entry 9", "chunk 1", line, findings, v4=True)
        self.assertEqual([t for level, _, t in findings if "splits" in t], [])
        self.assertEqual(check.rounds_of(line)[0], (1, "2222222", (0, 1, 2, 0), 1, 2))

    def test_the_cadence_is_read_from_the_a_line(self):
        self.assertEqual(check.cadence_of("- **A. Start:** sandbox — `PASS`; cadence — `light` (owner, 2026-11-17)"), "light")
        self.assertEqual(check.cadence_of("- **A. Start:** sandbox — `PASS`; cadence — `loop`"), "loop")
        self.assertIsNone(check.cadence_of("- **A. Start:** sandbox — `PASS`; branch — `slice-001-x`"))


A_LINE = ("- **A. Start:** sandbox — `PASS (macOS Seatbelt; Chrome)`; session — `s1`; audit — `off`; transcript — `kept`; "
          "delegation — `docs/x/delegation.md`; autopilot — `none`; cadence — `{cadence}`; budget — `8h, 2 reviews/chunk`; "
          "branch — `slice-004-holds`; base — `aaaaaaa`; records — `docs/x/implementation/`; readiness — `PASS`; gate checks — `present`")
LIGHT_C = ("- **C. Chunk {k}/2:** `Cancel a hold`; sonnet `?`t `4`m; commits `{sha}`; gate `PASS`; deviations `0`; shell edits `0`; "
           "review `none`; smoke `none`; standing `0/0/0`; builder `b{k}`; budget `0.5`h `0`r; records `ccccccc`; audit `off`; data `unchanged`")
D_LINE = ("- **D. Slice review:** map `docs/architecture-map.md` (`ddddddd`); done `standing: comment-density 7.5% (Medium)` "
          "(comments review `slice004-slice-comments-review.md`: 2 rewrites, folded into the fix round); "
          "mutation `40 mutants, 37 caught, 3 survived`; reviewers `tq co ar se re ac`; r0 `0/3/19/7` nd `1`; walk `28/0/7`; "
          "cold `5 confirmed, 2 verify`; fixes builders `6` opus `1` (`1111111 2222222 3333333`, gate fixer `4444444`); "
          "r1 `0/2/5` (reg 5, pre 2); r2 fix `5555555` gate PASS; last `0/0/3`; standing `0/0/5`; records `6666666`; "
          "audit `off`; data `unchanged`")
E_LINE = ("- **E. Delivery:** CI `present`; pushed `7777777`; PR `#92`; checks `CI green 9999999`; ci r1 fix `8888888`; "
          "screens — states fix `abcdef1 abcdef2`; baselines `9999999` (`28` changed, `9` new, `0` removed); issues `#85` (M `1`, deferred `0`); "
          "deferrals `7` listed; Lows `10` in body; `clean r0`; last `0/0/1`; consults `0`; cost `$89.77`; audit `off`")


def loop_findings(*lines):
    entry = {"n": 125, "body": "\n".join(lines) + "\n", "subs": check.re.findall(r"^- \*\*([A-E])\.", "\n".join(lines), check.re.M)}
    findings = []
    check.check_chunk_loop(entry, findings)
    return findings


class TheSlice4Log(unittest.TestCase):
    """S8 (the slice 4 review, F14): four shapes of a real 0.17.0 log the
    check reported as errors."""

    def test_a_cadence_changed_after_a_is_the_cadence_of_the_chunks_it_names(self):
        b = ("- **B. Plan:** `2` chunks — `Cancel a hold`; `List my holds` (`docs/x/implementation/report.md`, commit `bbbbbbb`)\n"
             '  - Owner 2026-11-18, word for word: "Yes light cadence please"; taken as: cadence `light` from chunk 2 onward '
             "(build and gate per chunk). Chunk 1's runner was already launched under `loop`.")
        loop_c1 = LIGHT_C.format(k=1, sha="1111111").replace("review `none`; smoke `none`", "review `co tq` r0 `0/0/0`; smoke `PASS`")
        found = loop_findings(A_LINE.format(cadence="loop"), b, loop_c1, LIGHT_C.format(k=2, sha="2222222"))
        self.assertEqual([t for level, _, t in found if level == "ERROR"], [])
        self.assertIn("cadence light from chunk 2 (changed after the A line)", [t for _, _, t in found])
        # with no such statement, an unreviewed chunk under `loop` is still an error
        found = loop_findings(A_LINE.format(cadence="loop"), b.split("\n")[0], loop_c1, LIGHT_C.format(k=2, sha="2222222"))
        self.assertTrue(any("`review none` under cadence `loop`" in t for level, _, t in found if level == "ERROR"))
        # and the change does not reach back to the chunks before it
        found = loop_findings(A_LINE.format(cadence="loop"), b, LIGHT_C.format(k=1, sha="1111111"), LIGHT_C.format(k=2, sha="2222222"))
        self.assertEqual([t for level, _, t in found if level == "ERROR"],
                         ["C chunk 1: `review none` under cadence `loop`; only `light` leaves a chunk unreviewed"])

    def test_the_d_lines_reviewers_are_read_from_the_reviewers_field(self):
        # `comments review <file>` stood before it and was read as one reviewer named "slice"
        self.assertEqual(check.reviewers_of(D_LINE), ["tq", "co", "ar", "se", "re", "ac"])
        self.assertEqual(check.reviewers_of("gate `PASS`; review `co tq` r0 `0/0/2`"), ["co", "tq"])
        found = loop_findings(A_LINE.format(cadence="light"), D_LINE)
        self.assertEqual([t for _, _, t in found if "reviewers;" in t], [])

    def test_a_light_fix_round_by_the_builders_is_round_one(self):
        # under light the first fix is several builders' commits: `fixes builders <n> opus <m> (<shas>)`, then `r1 <counts>`
        rounds = check.rounds_of(D_LINE)
        self.assertEqual([(n, sha) for n, sha, *_ in rounds], [(1, "1111111"), (2, "5555555")])
        self.assertEqual(rounds[0][2:], ((0, 2, 5, 0), 5, 2))
        found = loop_findings(A_LINE.format(cadence="light"), D_LINE)
        self.assertEqual([t for level, _, t in found if level == "ERROR"], [])

    def test_checks_green_on_the_baselines_commit_is_green_on_the_line(self):
        found = loop_findings(A_LINE.format(cadence="light"), E_LINE)
        self.assertEqual([t for level, _, t in found if level == "ERROR"], [])
        other = E_LINE.replace("CI green 9999999", "CI green 0000000")
        self.assertTrue(any("neither the pushed commit" in t for _, _, t in loop_findings(A_LINE.format(cadence="light"), other)))

    def test_the_summary_line_does_not_call_a_current_log_the_0_7_0_loop(self):
        found = loop_findings(A_LINE.format(cadence="light"), LIGHT_C.format(k=1, sha="1111111"), LIGHT_C.format(k=2, sha="2222222"))
        summary = [t for level, _, t in found if level == "INFO" and "chunks logged" in t]
        self.assertEqual(len(summary), 1)
        self.assertTrue(summary[0].startswith("chunk loop (0.7.0 form or later): 2 chunks logged"), summary[0])


if __name__ == "__main__":
    unittest.main(verbosity=1)
