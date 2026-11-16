"""The skill-mutation tool, without a model: on a scratch repository with
one skill and one case,

1. a reference applies when its removed text occurs exactly once and its
   `fails` are graders of the case; text that is gone, text that occurs
   twice and a grader the case does not have are each named;
2. `apply` writes the edit into a copy (tracked and new files, nothing
   ignored), into the skill text frozen in a copied history too, and
   leaves the tree as it was;
3. `run` on a reference passes when every grader in `fails` failed, and
   fails when one of them passed, when a run was short of the runs asked
   for, and when the reference no longer applies (nothing is run then);
4. a grader fails at one pass in three and not at two; a reference with
   no grader in `fails`, or an edit to any file but its skill's SKILL.md,
   is refused; a mutant short of its runs is INCOMPLETE; a grader already
   failing at its bar catches nothing; `--resume` takes only a result of
   the same deletion on the same case file; the same words in another
   turn of a history are left alone;
5. a known-bad file is not one of its case's inputs, so adding a reference
   leaves the case's evidence current (`affected_cases.Reach`).

Usage: python3 -I evals/tools/skill_mutation_test.py
"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import affected_cases  # noqa: E402
import skill_mutation as sm  # noqa: E402

SKILL = "# Demo\n\nAlways save the output.\nNever widen the list.\nNever widen the door.\n"
CASE = """name: demo-case
graders:
  - type: tool_used
    name: output-saved
  - type: regex
    name: list-not-widened
"""


def reference(old="Always save the output.\n", fails=("output-saved",)):
    return {"skill": "demo", "rule": "the output is saved",
            "edits": [{"file": "skills/demo/SKILL.md", "old": old, "new": ""}],
            "fails": list(fails)}


class SkillMutationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, "repo")
        for path, text in (("skills/demo/SKILL.md", SKILL), ("evals/demo-case/case.yaml", CASE),
                           (".gitignore", "ignored/\n"), ("ignored/big.bin", "x"), ("notes.txt", "new\n")):
            full = os.path.join(self.root, path)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            open(full, "w", encoding="utf-8").write(text)
        subprocess.run(["git", "init", "-q", self.root], check=True)
        subprocess.run(["git", "-C", self.root, "add", "skills", "evals", ".gitignore"], check=True)
        self.saved = (sm.ROOT, sm.EVALS)
        sm.ROOT, sm.EVALS = self.root, os.path.join(self.root, "evals")

    def tearDown(self):
        sm.ROOT, sm.EVALS = self.saved
        self.tmp.cleanup()

    def keep(self, ref, name="output-saved"):
        path = os.path.join(sm.EVALS, "demo-case", "known-bad", name + ".json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(ref, open(path, "w", encoding="utf-8"))

    def test_a_reference_that_applies_has_no_problems(self):
        self.assertEqual(sm.problems("r", "demo-case", reference(), self.root), [])

    def test_removed_text_that_is_gone_or_repeated_is_named(self):
        gone = sm.problems("r", "demo-case", reference(old="Always keep the output.\n"), self.root)
        self.assertIn("occurs 0 times", gone[0])
        twice = sm.problems("r", "demo-case", reference(old="Never widen the"), self.root)
        self.assertIn("occurs 2 times", twice[0])

    def test_a_grader_the_case_does_not_have_is_named(self):
        found = sm.problems("r", "demo-case", reference(fails=("output-saved", "no-such-grader")), self.root)
        self.assertEqual(found, ["not graders of demo-case: no-such-grader"])

    def test_a_second_skill_may_be_edited_only_when_the_reference_names_it(self):
        other = reference()
        other["edits"][0]["file"] = "skills/other/SKILL.md"
        self.assertEqual(sm.problems("r", "demo-case", other, self.root), ["edits skills/other/SKILL.md, not skills/demo/SKILL.md"])
        other["also"] = ["other"]
        self.assertTrue(sm.editable(other, "skills/other/SKILL.md"))
        self.assertTrue(sm.editable(other, "skills/demo/SKILL.md"))
        other["also"] = ["../../evals"]
        self.assertFalse(sm.editable(other, "skills/../../evals/SKILL.md"))

    def test_an_empty_fails_list_and_an_edit_outside_the_skill_are_named(self):
        empty = sm.problems("r", "demo-case", reference(fails=()), self.root)
        self.assertIn("no grader named", empty[0])
        elsewhere = reference()
        elsewhere["edits"][0]["file"] = "evals/demo-case/case.yaml"
        found = sm.problems("r", "demo-case", elsewhere, self.root)
        self.assertEqual(found, ["edits evals/demo-case/case.yaml, not skills/demo/SKILL.md"])
        outside = reference()
        outside["edits"][0]["file"] = os.path.join(self.tmp.name, "host.txt")
        with self.assertRaises(SystemExit):
            sm.apply(outside, os.path.join(self.tmp.name, "copy-outside"), self.root)

    def test_apply_edits_a_copy_and_leaves_the_tree(self):
        dest = os.path.join(self.tmp.name, "copy")
        sm.apply(reference(), dest, self.root)
        self.assertNotIn("Always save", open(os.path.join(dest, "skills/demo/SKILL.md")).read())
        self.assertEqual(open(os.path.join(self.root, "skills/demo/SKILL.md")).read(), SKILL)
        self.assertTrue(os.path.isfile(os.path.join(dest, "notes.txt")))  # new, not ignored
        self.assertFalse(os.path.exists(os.path.join(dest, "ignored")))

    def test_apply_edits_the_skill_text_frozen_in_a_history(self):
        history = os.path.join(self.root, "evals", "demo-case", "history.jsonl")
        entry = {"type": "user", "message": {"content": "Base directory for this skill: <plugin-root>/skills/demo\n\n" + SKILL}}
        prompt = {"type": "user", "message": {"content": "The owner wrote: Always save the output.\n"}}
        open(history, "w", encoding="utf-8").write(json.dumps(entry) + "\n" + json.dumps(prompt) + "\n")
        dest = os.path.join(self.tmp.name, "copy")
        sm.apply(reference(), dest, self.root)
        frozen, said = [json.loads(line) for line in open(os.path.join(dest, "evals", "demo-case", "history.jsonl")) if line.strip()]
        self.assertNotIn("Always save", frozen["message"]["content"])
        self.assertIn("Never widen the list.", frozen["message"]["content"])
        self.assertIn("Always save", said["message"]["content"])  # the same words in another turn stay
        self.assertIn("Always save", open(history).read())  # the tree's own history untouched

    def run_with(self, rates, runs=3, mutants=None):
        """`run` on the kept references, with the model run replaced."""
        calls = []

        def fake(ident, case, ref, n, out_dir, keep, parallel=8):
            calls.append(ident)
            return {"id": ident, "case": case, "runs": runs, "errored": 3 - runs, "rates": rates,
                    "source": "x", "error": None}
        real, sm.run_pair = sm.run_pair, fake
        args = types.SimpleNamespace(mutants=mutants, case=None, rule=None, runs=3, parallel=3,
                                     out=os.path.join(self.tmp.name, "out"), resume=False, keep=False)
        try:
            with contextlib.redirect_stdout(io.StringIO()) as printed:
                code = sm.cmd_run(args)
        finally:
            sm.run_pair = real
        return code, printed.getvalue(), calls

    def test_run_passes_when_the_named_grader_failed(self):
        self.keep(reference())
        code, printed, _ = self.run_with({"output-saved": 0.0, "list-not-widened": 1.0})
        self.assertEqual(code, 0)
        self.assertIn("PASS", printed)

    def test_run_fails_when_the_named_grader_passed(self):
        self.keep(reference())
        code, printed, _ = self.run_with({"output-saved": 1.0, "list-not-widened": 0.0})
        self.assertEqual(code, 1)
        self.assertIn("expected to fail and did not: output-saved", printed)

    def test_run_fails_on_too_few_clean_runs(self):
        self.keep(reference())
        code, printed, _ = self.run_with({"output-saved": 0.0}, runs=2)
        self.assertEqual(code, 1)
        self.assertIn("too few clean runs", printed)

    def test_run_refuses_a_reference_that_no_longer_applies(self):
        self.keep(reference(old="Always keep the output.\n"))
        with self.assertRaises(SystemExit) as stopped:
            self.run_with({"output-saved": 0.0})
        self.assertIn("does not apply", str(stopped.exception))

    def mutants_file(self):
        path = os.path.join(self.tmp.name, "mutants.json")
        json.dump([dict(reference(), id="output-saved", cases=["demo-case"])], open(path, "w"))
        return path

    def test_a_mutant_short_of_its_runs_is_incomplete(self):
        code, printed, _ = self.run_with({"output-saved": 0.0}, runs=2, mutants=self.mutants_file())
        self.assertEqual(code, 1)
        self.assertIn("INCOMPLETE", printed)

    def test_a_grader_failing_at_its_bar_does_not_catch_a_mutant(self):
        json.dump({"demo-case": {"graders": {"output-saved": 0.67, "list-not-widened": 1.0}}},
                  open(os.path.join(sm.EVALS, "thresholds.json"), "w"))
        code, printed, _ = self.run_with({"output-saved": 0.0, "list-not-widened": 1.0}, mutants=self.mutants_file())
        self.assertIn("SURVIVED", printed)
        self.assertIn("failing at the bar already, not counted: output-saved", printed)
        code, printed, _ = self.run_with({"output-saved": 1.0, "list-not-widened": 0.0}, mutants=self.mutants_file())
        self.assertIn("CAUGHT", printed)

    def test_resume_takes_only_a_result_of_the_same_deletion(self):
        out = os.path.join(self.tmp.name, "out")
        os.makedirs(out)
        ref = reference()
        result = {"mutation": sm.key_of("demo-case", ref), "cases": [{"arms": {"with": [{}, {}, {}]}}]}
        json.dump(result, open(os.path.join(out, "r--demo-case.json"), "w"))
        self.assertTrue(sm.done_already("r", "demo-case", ref, 3, out))
        self.assertFalse(sm.done_already("r", "demo-case", reference(old="Never widen the list.\n"), 3, out))

    def test_a_grader_fails_at_one_pass_in_three(self):
        self.assertEqual(sm.failed_graders({"a": 0.0, "b": 1 / 3, "c": 2 / 3, "d": 1.0}), ["a", "b"])

    def test_check_counts_what_no_longer_applies(self):
        self.keep(reference())
        self.keep(reference(old="Always keep the output.\n"), "stale")
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            code = sm.cmd_check(types.SimpleNamespace(mutants=None))
        self.assertEqual(code, 1)
        self.assertIn("2 checked, 1 no longer apply", printed.getvalue())


class KnownBadIsNotACaseInput(unittest.TestCase):
    def test_a_known_bad_file_does_not_reach_its_case(self):
        reach = affected_cases.Reach()
        case = "chunk-runner-gap-handback"
        self.assertFalse(reach.reaches(case, f"evals/{case}/known-bad/needs-decision-ends.json"))
        self.assertTrue(reach.reaches(case, f"evals/{case}/case.yaml"))


if __name__ == "__main__":
    unittest.main()
