#!/usr/bin/env python3
"""The deferrals list, without a model: the two sections of a slice file
become one markdown section and a count line, each item once, with its
triage sentence; the library fixture's own slice file gives two.

Usage: python3 -I evals/tools/deferrals_test.py
"""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "skills", "orchestrator", "scripts", "deferrals.py")
FIXTURE_SLICE = os.path.join(ROOT, "evals", "fixtures", "library-app", "route-plants", "cancel-hold", "slice-001.md")

SLICE = """# Slice 001

## Acceptance criteria
- Given a hold, when the desk cancels it, then it leaves the queue. Usable without it: not an item.

## Explicitly deferred
Open questions this slice does not resolve.

- The staff route (slice 2). Usable without it: the desk uses the
  console command until the route lands.
- Undoing a cancel. Blocker: a cancelled hold cannot be put back and the
  desk has no other way.

## Still open
1. Whether a notice goes to the member.

## Out of scope
- Fines. Usable without it: nothing.
"""


def run(*args):
    return subprocess.run([sys.executable, "-I", SCRIPT, *args], capture_output=True, text=True)


class Deferrals(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.slice = os.path.join(self.tmp, "slice-001.md")
        with open(self.slice, "w", encoding="utf-8") as f:
            f.write(SLICE)

    def test_each_item_once_with_its_section_and_triage(self):
        r = run("--slice-file", self.slice)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("## Deferred with this slice", out)
        self.assertIn("- (deferred) The staff route (slice 2). **Usable without it: the desk uses the console command until the route lands.**", out)
        self.assertIn("- (deferred) Undoing a cancel. **Blocker: a cancelled hold cannot be put back and the desk has no other way.**", out)
        self.assertIn("- (still open) Whether a notice goes to the member. **no triage sentence**", out)
        # the section's lead sentence is not an item; other sections are not read
        self.assertNotIn("Open questions this slice", out)
        self.assertNotIn("Fines", out)
        self.assertNotIn("leaves the queue", out)
        self.assertEqual(out.count("\n- ("), 3)
        self.assertEqual(out.strip().splitlines()[-1],
                         "deferrals: 3 listed (2 deferred, 1 still open; 1 blocker, 1 without a triage sentence)")

    def test_out_writes_the_section_and_prints_only_the_count(self):
        dest = os.path.join(self.tmp, "pr-deferred.md")
        r = run("--slice-file", self.slice, "--out", dest)
        self.assertEqual(r.stdout.strip(), "deferrals: 3 listed (2 deferred, 1 still open; 1 blocker, 1 without a triage sentence)")
        with open(dest, encoding="utf-8") as f:
            self.assertTrue(f.read().startswith("## Deferred with this slice\n"))

    def test_no_section_and_an_empty_section_say_none(self):
        for body in ("# Slice\n\n## Thin path\n- a step\n", "# Slice\n\n## Explicitly deferred\nNone.\n\n## Still open\n- None\n"):
            with open(self.slice, "w", encoding="utf-8") as f:
                f.write(body)
            r = run("--slice-file", self.slice)
            self.assertIn("\nNone.\n", r.stdout, body)
            self.assertIn("deferrals: 0 listed", r.stdout)

    def test_a_missing_file_is_an_error_not_an_empty_list(self):
        r = run("--slice-file", os.path.join(self.tmp, "absent.md"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("cannot read", r.stdout)

    def test_the_library_fixtures_slice_gives_its_two_deferrals(self):
        r = run("--slice-file", FIXTURE_SLICE)
        self.assertIn("deferrals: 2 listed (2 deferred, 0 still open; 0 blocker, 0 without a triage sentence)", r.stdout)
        self.assertIn("**Usable without it: members ask the desk, as they do today.**", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
