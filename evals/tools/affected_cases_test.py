#!/usr/bin/env python3
"""What a case depends on inside a file it loads (0.16.0), without a model.

- The orchestrator's text, scoped to a case's steps: an edit inside
  another step's section, or on another step's log line, changes nothing
  the case depends on; an edit in the shared text or in its own step
  does; a skill with a section's opening line missing is taken whole.
- A script's siblings are the ones it imports or runs by name, not the
  ones a docstring mentions.
- A case on a loop state depends on its state's entry in the manifest and
  on no file of the loop fixture; the repository's own cases resolve to
  a state, and every state has an entry and a step.

Usage: python3 -I evals/tools/affected_cases_test.py
"""
import json
import os
import sys
import unittest

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import affected_cases as ac  # noqa: E402
import loop_states  # noqa: E402

SKILL = "\n".join([
    "# Orchestrator", "shared words", "**A. Start.** In this order:", "aaa text", "**B. Plan.** Launch", "bbb text",
    "**C. Chunks, one at a time.** For chunk k", "ccc text", "**D. Slice review.** When", "ddd text",
    "**E. Delivery.** No question", "eee text", "**Pausing and resuming.** On a", "pause words",
    "- **A. Start:** a line", "- **B. Plan:** b line", "- **C. Chunk <k>/<n>:** c line", "  - decision bullet",
    "- **D. Slice review:** d line", "- **E. Delivery:** e line", "tail words"])


class Scoped(unittest.TestCase):
    def test_a_case_keeps_the_shared_text_and_its_own_steps(self):
        view = ac.scoped(SKILL, ["C"])
        for kept in ("shared words", "ccc text", "pause words", "- **C. Chunk <k>/<n>:** c line", "  - decision bullet", "tail words"):
            self.assertIn(kept, view)
        for gone in ("aaa text", "bbb text", "ddd text", "eee text", "- **E. Delivery:** e line", "- **A. Start:** a line"):
            self.assertNotIn(gone, view)

    def test_an_edit_in_another_step_changes_nothing_and_one_in_its_own_or_the_shared_text_does(self):
        for old, same in (("eee text", True), ("- **E. Delivery:** e line", True), ("ccc text", False), ("shared words", False),
                          ("pause words", False)):
            edited = SKILL.replace(old, old + " edited")
            self.assertEqual(ac.scoped(edited, ["C"]) == ac.scoped(SKILL, ["C"]), same, old)

    def test_a_routing_case_depends_on_no_step(self):
        view = ac.scoped(SKILL, [])
        self.assertIn("shared words", view)
        self.assertNotIn("aaa text", view)

    def test_a_restructured_skill_is_taken_whole(self):
        moved = SKILL.replace("**D. Slice review.**", "**D. The review.**")
        self.assertEqual(ac.scoped(moved, ["C"]), moved)

    def test_the_real_skill_still_has_every_section_opening(self):
        text = open(os.path.join(ac.ROOT, ac.ORCHESTRATOR), encoding="utf-8").read()
        self.assertLess(len(ac.scoped(text, ["E"])), len(text))
        for step in "ABCDE":
            self.assertNotEqual(ac.scoped(text, [step]), ac.scoped(text, []), step)


class Scripts(unittest.TestCase):
    def test_siblings_are_imported_or_run_by_name_not_mentioned(self):
        files = ac.script_files()
        self.assertEqual(ac.with_siblings(["readiness_check.py"], files), {"readiness_check.py", "screen_check.py", "source_scan.py"})
        self.assertEqual(ac.with_siblings(["source_scan.py"], files), {"source_scan.py"})
        self.assertIn("ts_runtime_lines.mjs", ac.with_siblings(["validation_gate.py"], files))


class States(unittest.TestCase):
    def setUp(self):
        self.reach = ac.Reach()
        self.manifest = json.load(open(os.path.join(ac.EVALS, "loop_states.json"), encoding="utf-8"))
        self.steps = json.load(open(ac.STEPS_FILE, encoding="utf-8"))

    def test_a_loop_case_depends_on_its_states_entry_and_no_fixture_file(self):
        case = "chunk-runner-gate-outside"
        self.assertEqual(self.reach.key(case), "state:chunk1-outside")
        self.assertIsNone(self.reach.view(case, loop_states.LOOP + "state.sh", b"anything"))
        data = json.dumps({"states": {"state:chunk1-outside": "aaa", "state:planned": "bbb"}}).encode()
        other = json.dumps({"states": {"state:chunk1-outside": "aaa", "state:planned": "ccc"}}).encode()
        moved = json.dumps({"states": {"state:chunk1-outside": "zzz", "state:planned": "bbb"}}).encode()
        self.assertEqual(self.reach.view(case, ac.LOOP_MANIFEST, data), self.reach.view(case, ac.LOOP_MANIFEST, other))
        self.assertNotEqual(self.reach.view(case, ac.LOOP_MANIFEST, data), self.reach.view(case, ac.LOOP_MANIFEST, moved))
        self.assertIsNone(self.reach.view("code-review-catalog", ac.LOOP_MANIFEST, data))

    def test_a_case_with_recorded_scripts_depends_on_those_and_no_other(self):
        case = "chunk-runner-gate-outside"
        self.assertIsNotNone(self.reach.view(case, "skills/orchestrator/scripts/validation_gate.py", b"x"))
        self.assertIsNotNone(self.reach.view(case, "skills/orchestrator/scripts/source_scan.py", b"x"))
        self.assertIsNone(self.reach.view(case, "skills/orchestrator/scripts/mutation_pass.py", b"x"))

    def test_every_state_in_use_has_an_entry_and_a_step_and_the_manifest_is_current(self):
        for key in loop_states.keys_in_use():
            self.assertIn(key, self.manifest["states"], key)
            if key.startswith("state:"):
                self.assertIn(key.split(":", 1)[1].split("+", 1)[0], self.steps["states"], key)
        self.assertIsNone(loop_states.check())

    def test_the_whole_file_rule_is_still_there_for_old_evidence(self):
        old = ac.Reach(whole_files=True)
        self.assertEqual(old.view("chunk-runner-gate-outside", loop_states.LOOP + "state.sh", b"anything"), b"anything")


if __name__ == "__main__":
    unittest.main()
