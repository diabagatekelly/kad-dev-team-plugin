#!/usr/bin/env python3
"""The Definition of Done's README check, read without running the gate:
the sections it wants, and the "does not" list against the slice's
acceptance criteria (slice 2 round 1, 2026-11-10: the check passed a
README whose not-done list named the criterion the round had built).

Usage: python3 -I evals/tools/done_check_test.py
"""
import importlib.util
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "skills", "orchestrator", "scripts", "done_check.py")

README = """# library-lending

A lending service for a community library.

## Prerequisites

- Node.js 24.

## Clone to running

1. `npm test`.

## Tests and checks

- `npm test`.

## Where things live

- Holds are kept in memory.

## What this slice does and does not

- Cancels one member's hold on one title and says so.
- Turns down a cancel for a hold the member does not have, with a reason.
- Reports a queue that cannot be reached as a failure.
- Not yet: the staff HTTP route, member self-service cancelling{stale}.
"""

SLICE = """# Slice 1: Staff cancel a member's hold on a title

## Thin path

Given a title with a member's hold on it, cancelling removes it.

## Acceptance criteria

- Given a member with a hold on a title, when it is cancelled, the hold is
  gone from that title's queue and the result says cancelled.
- Given a member with no hold on a title, when cancelling is asked for, the
  result is a rejection with a reason, and the queue is unchanged.
- Reliability: if the hold queue can't be reached, the result is a failure
  the caller sees, and nothing is half-removed.

## Explicitly deferred

- The staff HTTP route (slice 2).
- Member self-service cancelling.
"""


def load():
    spec = importlib.util.spec_from_file_location("done_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReadmeCheck(unittest.TestCase):
    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.mkdtemp()
        self.slice = os.path.join(self.tmp, "slice-001.md")
        with open(self.slice, "w", encoding="utf-8") as f:
            f.write(SLICE)

    def readme(self, stale=""):
        with open(os.path.join(self.tmp, "README.md"), "w", encoding="utf-8") as f:
            f.write(README.format(stale=stale))

    def test_a_not_done_list_from_the_deferred_items_passes(self):
        self.readme()
        ok, detail, fix = self.mod.check_readme(self.tmp, self.slice)
        self.assertTrue(ok, detail)
        self.assertIn("names no criterion", detail)

    def test_a_not_done_item_a_criterion_covers_fails_naming_both(self):
        self.readme(stale=", turning down a cancel for a hold the member does not have")
        ok, detail, fix = self.mod.check_readme(self.tmp, self.slice)
        self.assertFalse(ok)
        self.assertIn('"turning down a cancel for a hold the member does not have"', detail)
        self.assertIn("criterion: Given a member with no hold on a title", detail)
        self.assertIn("docs-writer:readme", fix)

    def test_does_not_inside_a_does_bullet_is_the_behaviour_not_the_list(self):
        # "Turns down a cancel for a hold the member does not have" is what the slice does
        self.readme()
        ok, detail, _ = self.mod.check_readme(self.tmp, self.slice)
        self.assertTrue(ok, detail)
        self.readme(stale="")
        with open(os.path.join(self.tmp, "README.md"), "a", encoding="utf-8") as f:
            f.write("- Does not yet turn down a cancel for a hold the member does not have.\n")
        ok, detail, _ = self.mod.check_readme(self.tmp, self.slice)
        self.assertFalse(ok, detail)

    def test_a_deferred_interface_to_a_built_behaviour_is_not_stale(self):
        self.readme(stale=", the staff HTTP route for cancelling a member's hold")
        ok, detail, _ = self.mod.check_readme(self.tmp, self.slice)
        self.assertTrue(ok, detail)

    def test_the_not_done_list_is_found_under_a_later_heading(self):
        with open(os.path.join(self.tmp, "README.md"), "w", encoding="utf-8") as f:
            f.write(README.format(stale="").replace("## What this slice does and does not", "## What this slice does")
                    + "\n## What it does not yet\n\n- Not yet: turning down a cancel for a hold the member does not have.\n")
        ok, detail, _ = self.mod.check_readme(self.tmp, self.slice)
        self.assertFalse(ok, detail)

    def test_the_slice_file_itself_is_preferred_over_a_companion(self):
        with open(os.path.join(self.tmp, "slice-001-with-row.md"), "w", encoding="utf-8") as f:
            f.write("# companion\n\n## Acceptance criteria\n\n- Given nothing, when nothing, then nothing.\n")
        self.assertEqual(self.mod.find_slice(self.tmp, "001"), self.slice)

    def test_a_short_item_fails_only_when_every_word_matches(self):
        self.readme(stale=", a hold queue that cannot be reached")
        ok, detail, _ = self.mod.check_readme(self.tmp, self.slice)
        self.assertFalse(ok, detail)
        self.readme(stale=", queue priorities")  # `queue` alone is one shared word of two
        ok, detail, _ = self.mod.check_readme(self.tmp, self.slice)
        self.assertTrue(ok, detail)

    def test_without_a_slice_document_the_sections_alone_are_checked(self):
        self.readme(stale=", turning down a cancel for a hold the member does not have")
        ok, detail, _ = self.mod.check_readme(self.tmp, None)
        self.assertTrue(ok, detail)
        self.assertNotIn("criterion", detail)

    def test_a_missing_section_is_still_the_first_answer(self):
        with open(os.path.join(self.tmp, "README.md"), "w", encoding="utf-8") as f:
            f.write("# app\n\nA thing.\n\n## Prerequisites\n\n- none\n")
        ok, detail, _ = self.mod.check_readme(self.tmp, self.slice)
        self.assertFalse(ok)
        self.assertIn("lacks sections", detail)


if __name__ == "__main__":
    unittest.main(verbosity=1)
