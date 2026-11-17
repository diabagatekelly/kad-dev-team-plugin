#!/usr/bin/env python3
"""The map's changes section against a prior map written by hand (B9),
without a model.

- A prior row with no backticks (names split by commas or semicolons, a
  dash or `none` for nothing) is read: an edge and an export it already
  listed are not reported as new, and a real addition still is.
- A prior row that cannot be read (prose in a cell, too few cells) is
  named in the changes section, keeps its tier, and nothing is diffed
  against it.
- A prior map in the script's own form still reads as before.
- A new module's tier given with `--tier` is on its row and decides its
  edge's place among the candidates (B10).

Usage: python3 -I evals/tools/extract_map_test.py
"""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "skills", "map-update", "scripts", "extract_map.py")
HEAD = "# Architecture map\n\n## Modules\n\n| Path | Tier | Internal edges | External packages | Exports |\n|---|---|---|---|---|\n"


def run(rows, *args):
    """The script's whole output for the same two-module project."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "lending"))
        os.makedirs(os.path.join(tmp, "docs"))
        with open(os.path.join(tmp, "lending", "a.ts"), "w") as f:
            f.write("export function a() { return 1; }\n")
        with open(os.path.join(tmp, "lending", "b.ts"), "w") as f:
            f.write("import { a } from './a';\nexport const b = a();\nexport const c = 2;\n")
        with open(os.path.join(tmp, "docs", "architecture-map.md"), "w") as f:
            f.write(HEAD + rows)
        r = subprocess.run([sys.executable, "-I", SCRIPT, "--project", tmp, *args], capture_output=True, text=True)
    return r.returncode, r.stdout


def changes(rows):
    """The `## Changes since the prior map` lines for a two-module project
    (`lending/b.ts` imports `lending/a.ts`) and a prior map with `rows`."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "lending"))
        os.makedirs(os.path.join(tmp, "docs"))
        with open(os.path.join(tmp, "lending", "a.ts"), "w") as f:
            f.write("export function a() { return 1; }\n")
        with open(os.path.join(tmp, "lending", "b.ts"), "w") as f:
            f.write("import { a } from './a';\nexport const b = a();\nexport const c = 2;\n")
        with open(os.path.join(tmp, "docs", "architecture-map.md"), "w") as f:
            f.write(HEAD + rows)
        out = subprocess.run([sys.executable, "-I", SCRIPT, "--project", tmp], capture_output=True, text=True).stdout
    section = out.split("## Changes since the prior map\n", 1)[1].split("\n## ", 1)[0]
    table = out.split("## Modules\n", 1)[1].split("\n## ", 1)[0]
    return [l for l in section.splitlines() if l.strip()], table


class PriorMap(unittest.TestCase):
    def test_a_bare_cell_row_is_read_and_only_the_real_addition_is_new(self):
        lines, _ = changes("| lending/a.ts | 1 | none | — | a |\n| lending/b.ts | 2 | lending/a.ts | - | b |\n")
        self.assertEqual(lines, ["- `lending/b.ts`: new exports: `c`"])

    def test_commas_and_semicolons_both_split_a_bare_cell(self):
        for cell in ("b, c", "b; c"):
            lines, _ = changes(f"| lending/a.ts | 1 | - | - | a |\n| lending/b.ts | 2 | lending/a.ts | - | {cell} |\n")
            self.assertEqual(lines, ["No change in modules, edges or exports."], cell)

    def test_the_scripts_own_form_reads_as_before(self):
        lines, _ = changes("| `lending/a.ts` | 1 | — | — | `a` |\n| `lending/b.ts` | 2 | `lending/a.ts` | — | `b`; `c` |\n")
        self.assertEqual(lines, ["No change in modules, edges or exports."])

    def test_a_row_of_prose_is_named_and_nothing_is_diffed_against_it(self):
        lines, table = changes("| lending/a.ts | 1 | - | - | a |\n| lending/b.ts | 2 | imports the a module | - | b |\n")
        self.assertEqual(len(lines), 1)
        self.assertIn("`lending/b.ts`: the prior map's row could not be read", lines[0])
        self.assertIn("internal edges cell is not a list of names", lines[0])
        self.assertNotIn("new exports", "\n".join(lines))
        self.assertIn("| `lending/b.ts` | 2 |", table)  # the tier is still carried

    def test_a_row_with_too_few_cells_is_named(self):
        lines, _ = changes("| lending/a.ts | 1 | - | - | a |\n| lending/b.ts | 2 | lending/a.ts |\n")
        self.assertIn("3 cells, five expected", lines[0])


class TierFromTheDesign(unittest.TestCase):
    """B10: a new module's tier is given to the script, so the row and the
    wrong-direction list agree (runs patched the map by hand, and one in
    three left the module untiered and its edge "direction unknown")."""
    PRIOR = "| `lending/a.ts` | tier 3 | — | — | `a` |\n"

    def test_without_a_tier_the_new_module_is_untiered_and_the_last_line_says_so(self):
        code, out = run(self.PRIOR)
        self.assertEqual(code, 0)
        self.assertIn("| `lending/b.ts` | untiered |", out)
        self.assertIn("Untiered, direction unknown:", out)
        self.assertRegex(out.strip().splitlines()[-1], r"^new and untiered: lending/b\.ts .*--tier")

    def test_a_given_tier_is_on_the_row_and_the_edge_is_a_wrong_direction_candidate(self):
        code, out = run(self.PRIOR, "--tier", "lending/b.ts=1")
        self.assertEqual(code, 0)
        self.assertIn("| `lending/b.ts` | tier 1 |", out)
        wrong = out.split("## Wrong-direction candidates\n", 1)[1]
        self.assertRegex(wrong.split("Untiered, direction unknown")[0], r"`lending/b\.ts` \(tier 1\) → `lending/a\.ts` \(tier 3\) — new")
        self.assertNotIn("new and untiered", out)

    def test_a_tier_for_a_path_that_is_no_module_is_refused(self):
        code, out = run(self.PRIOR, "--tier", "lending/nope.ts=1")
        self.assertEqual(code, 1)
        self.assertIn("names no module", out)

    def test_a_tier_that_is_not_a_number_is_refused(self):
        code, out = run(self.PRIOR, "--tier", "lending/b.ts=important")
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
