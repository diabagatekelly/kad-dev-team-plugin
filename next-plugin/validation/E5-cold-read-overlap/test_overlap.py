import unittest

import overlap


def defect(name, *readers):
    return {"id": name, "title": name, "found_by": list(readers)}


class Added(unittest.TestCase):
    def test_readers_who_find_the_same_things_add_nothing_after_the_first(self):
        defects = [defect("a", "r1", "r2"), defect("b", "r1", "r2")]
        self.assertEqual(overlap.added_by_position(defects, ["r1", "r2"]), [2.0, 0.0])

    def test_readers_who_share_nothing_each_add_all_of_theirs(self):
        defects = [defect("a", "r1"), defect("b", "r1"), defect("c", "r2"), defect("d", "r2")]
        self.assertEqual(overlap.added_by_position(defects, ["r1", "r2"]), [2.0, 2.0])

    def test_the_average_is_over_every_order(self):
        defects = [defect("a", "r1"), defect("b", "r1", "r2"), defect("c", "r1")]
        # r1 first: 3 then 0; r2 first: 1 then 2.
        self.assertEqual(overlap.added_by_position(defects, ["r1", "r2"]), [2.0, 1.0])


class Unseen(unittest.TestCase):
    def test_many_found_once_and_few_twice_means_many_unseen(self):
        defects = [defect(str(i), "r1") for i in range(6)] + [defect("x", "r1", "r2")]
        self.assertEqual(overlap.unseen_estimate(defects, 2), 9.0)

    def test_more_readers_scale_the_estimate_towards_the_unscaled_form(self):
        defects = [defect(str(i), "r1") for i in range(6)] + [defect("x", "r1", "r2")]
        self.assertEqual(overlap.unseen_estimate(defects, 4), 13.5)

    def test_everything_found_twice_means_none_unseen(self):
        self.assertEqual(overlap.unseen_estimate([defect("a", "r1", "r2")], 2), 0.0)

    def test_with_nothing_found_twice_the_other_form_is_used(self):
        self.assertEqual(overlap.unseen_estimate([defect("a", "r1"), defect("b", "r2"), defect("c", "r2")], 2), 1.5)


class Summarise(unittest.TestCase):
    DEFECTS = ([defect(f"s{i}", "r1", "r2", "r3") for i in range(4)]
               + [defect(f"a{i}", "r1") for i in range(4)]
               + [defect(f"b{i}", "r2") for i in range(4)]
               + [defect("c0", "r3")])

    def test_each_reader_and_the_distinct_total_are_counted(self):
        result = overlap.summarise(self.DEFECTS)
        self.assertEqual(result["distinct_defects"], 13)
        self.assertEqual(result["found_by_each"], {"r1": 8, "r2": 8, "r3": 5})

    def test_the_rule_stops_at_the_first_reader_who_adds_fewer_than_the_threshold(self):
        result = overlap.summarise(self.DEFECTS, threshold=3)
        self.assertEqual(result["added_by_the_kth_reader_on_average"], [7.0, 3.0, 3.0])
        self.assertEqual(result["readers_worth_running_by_the_rule"], 3)

    def test_a_higher_threshold_supports_fewer_readers(self):
        self.assertEqual(overlap.summarise(self.DEFECTS, threshold=4)["readers_worth_running_by_the_rule"], 1)

    def test_a_reader_who_found_nothing_is_still_counted_when_named(self):
        result = overlap.summarise(self.DEFECTS, readers=["r1", "r2", "r3", "r4"])
        self.assertEqual(result["readers"], 4)
        self.assertEqual(result["found_by_each"]["r4"], 0)
        self.assertEqual(len(result["added_by_the_kth_reader_on_average"]), 4)

    def test_how_many_readers_found_each_defect_is_tallied(self):
        self.assertEqual(overlap.summarise(self.DEFECTS)["found_by_how_many_readers"], {"1": 9, "3": 4})


if __name__ == "__main__":
    unittest.main()
