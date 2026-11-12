#!/usr/bin/env python3
"""The design-readiness gate for an issue fix, and the wait check's reading
of a control's label, without a model. The planning set is the fixture's
`cancel-hold-readiness` (a reliability document that says "a few times"
and names a state with no mockup), committed as the slice was merged; the
fix then revises it.

- Unscoped, the set fails as it always did.
- With `--fix-base`, a fix that adds a sound criterion passes: the older
  gaps are listed as INFO, counted on one line, and never routed.
- A criterion the fix adds that fails, fails, and only it is named.
- An older criterion the fix rewords is the fix's again.
- A base that is not a commit is refused (exit 2), never read as "no gaps".
- A button's label is not a wait; the wait the criterion states still is.

Usage: python3 -I evals/tools/readiness_check_test.py
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "skills", "orchestrator", "scripts", "readiness_check.py")
PLANNING = os.path.join(ROOT, "evals", "fixtures", "library-app", "planning", "cancel-hold-readiness")

spec = importlib.util.spec_from_file_location("readiness_check", SCRIPT)
readiness = importlib.util.module_from_spec(spec)
sys.path.insert(0, os.path.dirname(SCRIPT))
spec.loader.exec_module(readiness)
import source_scan  # noqa: E402  (beside the script; for a git that runs here)

SOUND = ("- R3: Given a cancel the desk asked for is still running after 5 seconds, when\n"
         "  the route answers, then the screen shows the refused state with a reason\n"
         "  and the hold is as it was.\n")
VAGUE = ("- R4: Given the notice cannot be queued, when a cancel succeeds, then the\n"
         "  route retries the notice several times and the hold stays cancelled.\n")


def git(cwd, *args):
    subprocess.run([source_scan.find_git(), "-C", cwd, *args], check=True, capture_output=True)


class Project:
    """A repository whose `docs/cancel-hold/` is the fixture's planning set,
    committed once: the slice as it was merged."""

    def __init__(self, tmp):
        self.root = tmp
        self.planning = os.path.join(tmp, "docs", "cancel-hold")
        shutil.copytree(PLANNING, self.planning)
        git(tmp, "init", "-q")
        git(tmp, "config", "user.name", "t")
        git(tmp, "config", "user.email", "t@example.test")
        git(tmp, "config", "commit.gpgsign", "false")
        git(tmp, "add", "-A")
        git(tmp, "commit", "-qm", "slice 001 as merged")

    def edit(self, name, old, new):
        path = os.path.join(self.planning, name)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        assert old in text, old
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.replace(old, new, 1))

    def add_criterion(self, criterion, quoted_in_design=True):
        self.edit("reliability-slice-001.md", "\n## Decisions", criterion + "\n## Decisions")
        if quoted_in_design:
            ident = criterion.split(":")[0].lstrip("- ")
            self.edit("design-001.md", "- R1, R2 (", f"- {ident} (the fix): placed with R1 in the route.\n- R1, R2 (")

    def gate(self, *args):
        r = subprocess.run([sys.executable, "-I", SCRIPT, "--planning", self.planning, "--slice", "001", *args],
                           capture_output=True, text=True)
        return r.returncode, r.stdout


class ReadinessForAnIssueFix(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Project(os.path.realpath(self.tmp.name))

    def test_unscoped_the_old_slice_fails_on_its_own_gaps(self):
        code, out = self.project.gate()
        self.assertEqual(code, 1)
        self.assertIn("route: numbers-on-waits -> devsecops-engineer:reliability-requirements", out)
        self.assertIn("route: states-have-mockups -> ux-designer:screen-design", out)
        self.assertNotIn("older", out)
        self.assertTrue(out.rstrip().endswith("readiness: FAIL"))

    def test_a_sound_fix_passes_and_the_older_gaps_are_listed_not_routed(self):
        self.project.add_criterion(SOUND)
        code, out = self.project.gate("--fix-base", "HEAD")
        self.assertEqual(code, 0, out)
        self.assertNotIn("route:", out)
        self.assertIn("PASS  numbers-on-waits: nothing the fix revised fails (2 older gap(s)", out)
        self.assertIn("INFO  older-gap: numbers-on-waits: R1: Given the hold queue cannot be reached", out)
        self.assertIn("INFO  older-gap: states-have-mockups: unreachable-queue state -> ux-designer:screen-design", out)
        self.assertIn("older gaps: 3", out)
        self.assertTrue(out.rstrip().endswith("readiness: PASS"))

    def test_the_same_fix_without_the_base_is_failed_on_the_old_slice(self):
        self.project.add_criterion(SOUND)
        code, out = self.project.gate()
        self.assertEqual(code, 1)
        self.assertIn("route: states-have-mockups", out)

    def test_a_criterion_the_fix_adds_fails_and_only_it_is_named(self):
        self.project.add_criterion(SOUND)
        self.project.add_criterion(VAGUE)
        code, out = self.project.gate("--fix-base", "HEAD")
        self.assertEqual(code, 1, out)
        line = next(l for l in out.splitlines() if l.startswith("FAIL  numbers-on-waits"))
        self.assertIn("1 criteria name a wait", line)
        self.assertIn("R4:", line)
        self.assertNotIn("R1:", line)
        self.assertEqual([l for l in out.splitlines() if l.startswith("route:")],
                         ["route: numbers-on-waits -> devsecops-engineer:reliability-requirements"])
        self.assertIn("older gaps: 3", out)

    def test_a_criterion_the_fix_adds_and_the_design_does_not_quote_fails(self):
        self.project.add_criterion(SOUND, quoted_in_design=False)
        code, out = self.project.gate("--fix-base", "HEAD")
        self.assertEqual(code, 1, out)
        self.assertIn("route: criteria-homed -> software-architect:architecture-design", out)

    def test_an_older_criterion_the_fix_rewords_is_the_fixes(self):
        self.project.edit("reliability-slice-001.md", "retries the cancel a few times before",
                          "retries the cancel several times before")
        code, out = self.project.gate("--fix-base", "HEAD")
        self.assertEqual(code, 1, out)
        line = next(l for l in out.splitlines() if l.startswith("FAIL  numbers-on-waits"))
        self.assertIn("R1:", line)
        self.assertNotIn("R2:", line)
        self.assertIn("older gaps: 2", out)

    def test_the_base_is_the_commit_named_not_the_working_tree(self):
        self.project.add_criterion(VAGUE)
        git(self.project.root, "add", "-A")
        git(self.project.root, "commit", "-qm", "Planning: the fix")
        code, out = self.project.gate("--fix-base", "HEAD~1")
        self.assertEqual(code, 1, out)
        self.assertIn("R4:", out)
        code, out = self.project.gate("--fix-base", "HEAD")
        self.assertEqual(code, 0, out)
        self.assertIn("older gaps: 4", out)

    def test_a_base_that_is_not_a_commit_is_refused(self):
        code, out = self.project.gate("--fix-base", "no-such-ref")
        self.assertEqual(code, 2)
        self.assertIn("FAIL  fix-base: no-such-ref is not a commit", out)
        self.assertTrue(out.rstrip().endswith("readiness: FAIL"))

    def test_a_slice_with_no_documents_at_the_base_has_no_older_gap(self):
        git(self.project.root, "rm", "-rq", "--cached", "docs")
        git(self.project.root, "commit", "-qm", "before the slice was planned")
        code, out = self.project.gate("--fix-base", "HEAD")
        self.assertEqual(code, 1, out)
        self.assertIn("INFO  fix-base:", out)
        self.assertIn("route: numbers-on-waits", out)
        self.assertIn("older gaps: 0", out)


class ALabelIsNotAWait(unittest.TestCase):
    def numbers(self, criterion):
        return readiness.check_numbers({"reliability": "## Criteria\n\n" + criterion + "\n"})

    def test_a_buttons_label_names_no_wait(self):
        for criterion in (
            '- R5: Given the queue cannot be reached, when the failure is shown, then the screen offers a "Try again" button and the hold is as it was.',
            "- R5: Given the queue cannot be reached, when the failure is shown, then the screen offers a `Try again` control and the hold is as it was.",
            "- R5: Given the queue cannot be reached, when the failure is shown, then the Try again button is focused and the hold is as it was.",
            "- R5: Given the queue cannot be reached, when the failure is shown, then the screen says “Please wait” and the hold is as it was.",
        ):
            ok, detail, items = self.numbers(criterion)
            self.assertTrue(ok, criterion)
            self.assertEqual(items, [])

    def test_the_wait_beside_the_label_still_needs_its_number(self):
        ok, _, items = self.numbers('- R5: Given the queue cannot be reached, when staff press the "Try again" button, '
                                    "then the route retries a few times and the hold is as it was.")
        self.assertFalse(ok)
        self.assertEqual(len(items), 1)

    def test_a_wait_with_its_number_passes_as_before(self):
        ok, _, _ = self.numbers('- R5: Given the queue cannot be reached, when staff press the "Try again" button, '
                                "then the route retries 3 times, 2 seconds apart.")
        self.assertTrue(ok)

    def test_a_long_quoted_sentence_is_the_criterions_own(self):
        ok, _, _ = self.numbers('- R5: Given the queue cannot be reached, then, as the desk put it, "the route should '
                                'just retry the cancel for a while until it works".')
        self.assertFalse(ok)

    def test_an_unquoted_again_is_still_read(self):
        ok, _, _ = self.numbers("- R5: Given a failed cancel, when staff ask, then the route tries again and the hold is as it was.")
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main(verbosity=1)
