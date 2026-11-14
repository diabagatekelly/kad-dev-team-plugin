"""The fixture-pattern tool, without a model: on scratch text,

1. the slice pattern passes the fixture's slice with the placeholder line
   replaced by a pointer or by criteria, with its whitespace re-wrapped, and
   fails the slice unchanged, a slice with another line reworded, and a
   slice that keeps the placeholder beside the pointer;
2. the map pattern passes a map that keeps every source row and tier (with
   or without backticks, rows under test/ gone, new rows added) and fails a
   map that drops a row or changes a tier;
3. a pattern is found in a case file by its grader's name, whatever keys
   sit between the name and the pattern.

The patterns are JavaScript regexes without flags; the ones built here use
nothing Python's `re` reads differently.

Usage: python3 -I evals/tools/fixture_patterns_test.py
"""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_patterns as fp  # noqa: E402

SLICE = """# Slice 1: A member pays (a fine)

## Acceptance criteria

- Given a member, when they pay,
  the fine shows as paid.
- [RELIABILITY — placeholder]
%s
""" % fp.PLACEHOLDER

MAP = """## Modules
| Path | Tier | Internal edges (imports) | External packages | Public exports |
|---|---|---|---|---|
| catalog/book.ts | tier 1 | none | none | Book |
| utils/date-utils.ts | untiered | none | date-fns-lite | daysBetween |
| test/book.test.ts | untiered | catalog/book.ts | none | none |
"""


def js(pattern):
    return re.compile(pattern.replace(r"\x60", "`"))


class SlicePattern(unittest.TestCase):
    def setUp(self):
        self.p = js(fp.slice_placeholder(SLICE))

    def test_passes_a_pointer_and_rewrapped_text(self):
        filled = SLICE.replace(fp.PLACEHOLDER, "- Accessibility: see `accessibility-review-001.md`.")
        self.assertTrue(self.p.search(filled))
        self.assertTrue(self.p.search(filled.replace("when they pay,\n  the", "when they pay, the")))

    def test_passes_criteria_in_its_place(self):
        self.assertTrue(self.p.search(SLICE.replace(fp.PLACEHOLDER, "- Given a keyboard user, focus moves.\n- Given an error, it is announced.")))

    def test_fails_unchanged_reworded_or_kept(self):
        self.assertFalse(self.p.search(SLICE))
        pointer = "- Accessibility: see the review."
        self.assertFalse(self.p.search(SLICE.replace(fp.PLACEHOLDER, pointer).replace("shows as paid", "is marked paid")))
        self.assertFalse(self.p.search(SLICE.replace(fp.PLACEHOLDER, pointer + "\n" + fp.PLACEHOLDER)))

    def test_refuses_a_fixture_without_the_line(self):
        with self.assertRaises(SystemExit):
            fp.slice_placeholder("# Slice\n")


class MapPattern(unittest.TestCase):
    def setUp(self):
        self.p = js(fp.map_rows(MAP))

    def test_passes_rows_kept_with_backticks_and_new_rows(self):
        new = ("| `catalog/book.ts` | tier 1 | — | — | `Book` |\n"
               "| `lending/cancel-hold.ts` | tier 1 | — | — | `CancelHold` |\n"
               "| `utils/date-utils.ts` | untiered | — | `date-fns-lite` | `daysBetween` |\n")
        self.assertTrue(self.p.search(new))
        self.assertTrue(self.p.search(MAP))

    def test_fails_a_dropped_row_or_a_changed_tier(self):
        self.assertFalse(self.p.search("| catalog/book.ts | tier 1 | none | none | Book |\n"))
        self.assertFalse(self.p.search(MAP.replace("| untiered | none | date-fns-lite", "| tier 3 | none | date-fns-lite")))

    def test_leaves_test_rows_out(self):
        self.assertNotIn("book\\.test", fp.map_rows(MAP))


class InCase(unittest.TestCase):
    def test_finds_the_pattern_of_the_named_grader(self):
        text = ("graders:\n  - type: regex\n    name: other\n    pattern: 'a'\n"
                "  - type: regex\n    name: wanted\n    # a comment\n    target:\n      source: file\n      path: x.md\n    pattern: 'b''c'\n")
        start, end = fp.in_case(text, "wanted")
        self.assertEqual(text[start:end], "'b''c'")
        self.assertIsNone(fp.in_case(text, "absent"))

    def test_quoting_doubles_a_single_quote(self):
        self.assertEqual(fp.quoted("provider's"), "'provider''s'")


if __name__ == "__main__":
    unittest.main()
