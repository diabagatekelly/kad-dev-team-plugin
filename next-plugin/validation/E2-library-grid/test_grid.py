import unittest

import grid

ACTIONS = [
    {"id": "a01", "action": "sync", "what": "Pull new rows", "where": "d.md:1"},
    {"id": "a02", "action": "time", "what": "Give up after a minute", "where": "d.md:2"},
]
LIBRARY = [
    {"id": "sync-01", "action": "sync", "failure": "Arrives twice.", "question": "Then what?"},
    {"id": "sync-02", "action": "sync", "failure": "Arrives late.", "question": "Then what?"},
    {"id": "time-01", "action": "time", "failure": "Clock jumps.", "question": "Then what?"},
    {"id": "text-01", "action": "text", "failure": "Looks equal, is not.", "question": "Then what?"},
]


def filled():
    cells = grid.make(ACTIONS, LIBRARY)
    for cell in cells:
        cell["tag"], cell["says"] = "PLAN SILENT", "Nothing is said."
    return cells


class Make(unittest.TestCase):
    def test_each_item_meets_every_entry_of_its_own_kind_and_no_other(self):
        self.assertEqual([c["cell"] for c in grid.make(ACTIONS, LIBRARY)],
                         ["a01.sync-01", "a01.sync-02", "a02.time-01"])

    def test_a_cell_carries_the_item_and_the_entry_and_starts_empty(self):
        cell = grid.make(ACTIONS, LIBRARY)[0]
        self.assertEqual((cell["what"], cell["failure"], cell["tag"], cell["says"]),
                         ("Pull new rows", "Arrives twice.", "", ""))

    def test_an_item_of_a_kind_the_library_lacks_is_refused(self):
        with self.assertRaisesRegex(ValueError, "a09.*'magic'"):
            grid.make([{"id": "a09", "action": "magic", "what": "x", "where": "y"}], LIBRARY)


class Split(unittest.TestCase):
    def test_every_cell_lands_in_exactly_one_part(self):
        cells = grid.make(ACTIONS, LIBRARY)
        parts = grid.split(cells, 2)
        self.assertEqual(sorted(c["cell"] for p in parts for c in p), sorted(c["cell"] for c in cells))

    def test_an_item_is_never_cut_across_parts(self):
        for part in grid.split(grid.make(ACTIONS, LIBRARY), 2):
            self.assertEqual(len({c["item"] for c in part}), 1)

    def test_more_parts_than_items_gives_no_empty_part(self):
        self.assertEqual(len(grid.split(grid.make(ACTIONS, LIBRARY), 5)), 2)


class Problems(unittest.TestCase):
    def setUp(self):
        self.expected = grid.make(ACTIONS, LIBRARY)

    def test_a_grid_filled_as_handed_out_has_no_problems(self):
        self.assertEqual(grid.problems(self.expected, filled()), [])

    def test_a_dropped_cell_is_named(self):
        self.assertEqual(grid.problems(self.expected, filled()[1:]), ["a01.sync-01: missing"])

    def test_an_added_cell_is_named(self):
        extra = dict(filled()[0], cell="a01.sync-99")
        self.assertIn("a01.sync-99: not a cell of the grid", grid.problems(self.expected, filled() + [extra]))

    def test_a_cell_filled_twice_is_named(self):
        self.assertIn("a01.sync-01: filled twice", grid.problems(self.expected, filled() + [filled()[0]]))

    def test_a_changed_failure_is_named(self):
        cells = filled()
        cells[0]["failure"] = "Something easier."
        self.assertEqual(grid.problems(self.expected, cells), ["a01.sync-01: failure was changed"])

    def test_a_tag_outside_the_four_is_named(self):
        cells = filled()
        cells[0]["tag"] = "MAYBE"
        self.assertEqual(grid.problems(self.expected, cells), ["a01.sync-01: tag is 'MAYBE'"])

    def test_an_empty_says_is_named(self):
        cells = filled()
        cells[0]["says"] = "  "
        self.assertEqual(grid.problems(self.expected, cells), ["a01.sync-01: says is empty"])


class Render(unittest.TestCase):
    def test_each_item_gets_a_heading_and_each_cell_a_row_with_its_tag(self):
        text = grid.render(filled())
        self.assertIn("## a01 (sync): Pull new rows (d.md:1)", text)
        self.assertIn("| a01.sync-02 | Arrives late. | PLAN SILENT | Nothing is said. |", text)

    def test_a_bar_or_a_line_break_in_the_text_cannot_break_the_table(self):
        cells = filled()
        cells[0]["says"] = "one | two\nthree"
        self.assertIn("| PLAN SILENT | one / two three |", grid.render(cells))


if __name__ == "__main__":
    unittest.main()
