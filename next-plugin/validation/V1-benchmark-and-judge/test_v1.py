import unittest

import agreement as ag
import wording_check


class CheckRun(unittest.TestCase):
    def test_a_complete_run_is_read_as_bug_to_class(self):
        entries = [{"id": "1", "class": "N"}, {"id": "2", "class": "X"}]
        self.assertEqual(ag.check_run(entries, ["1", "2"], "f"), {"1": "N", "2": "X"})

    def test_a_missing_bug_is_refused(self):
        with self.assertRaisesRegex(ag.BadRun, r"missing \['2'\]"):
            ag.check_run([{"id": "1", "class": "N"}], ["1", "2"], "f")

    def test_a_bug_outside_the_benchmark_is_refused(self):
        with self.assertRaisesRegex(ag.BadRun, r"not in the benchmark \['9'\]"):
            ag.check_run([{"id": "1", "class": "N"}, {"id": "9", "class": "N"}], ["1"], "f")

    def test_an_unknown_class_is_refused(self):
        with self.assertRaisesRegex(ag.BadRun, "class 'Q'"):
            ag.check_run([{"id": "1", "class": "Q"}], ["1"], "f")

    def test_a_bug_scored_twice_is_refused(self):
        with self.assertRaisesRegex(ag.BadRun, "scored twice"):
            ag.check_run([{"id": "1", "class": "N"}, {"id": "1", "class": "P"}], ["1"], "f")


class Majority(unittest.TestCase):
    def test_two_of_three_wins(self):
        self.assertEqual(ag.majority(["N", "P", "N"]), "N")

    def test_a_three_way_tie_goes_to_the_least_favourable(self):
        self.assertEqual(ag.majority(["N", "P", "W"]), "W")
        self.assertEqual(ag.majority(["D", "P", "X"]), "X")


class Agreement(unittest.TestCase):
    CALLS = {
        ("a", "1"): ["N", "N", "N"],   # same class
        ("a", "2"): ["N", "D", "N"],   # same side of the line, classes differ
        ("a", "3"): ["N", "P", "N"],   # crosses the line
        ("b", "1"): ["X", "P", "W"],   # none named, classes differ
    }

    def test_named_or_not_counts_bugs_on_one_side_in_every_run(self):
        self.assertEqual(ag.agreement(self.CALLS)["same_named_or_not"], 3)

    def test_same_class_counts_only_identical_calls(self):
        self.assertEqual(ag.agreement(self.CALLS)["same_class"], 1)

    def test_named_per_plan_is_counted_run_by_run(self):
        result = ag.agreement(self.CALLS)["named_per_plan_per_run"]
        self.assertEqual(result["a"], {"bugs": 3, "named": [3, 2, 3]})
        self.assertEqual(result["b"], {"bugs": 1, "named": [0, 0, 0]})

    def test_split_lists_every_bug_the_runs_disagreed_on(self):
        self.assertEqual(ag.agreement(self.CALLS)["split"],
                         ["a:2 N/D/N", "a:3 N/P/N", "b:1 X/P/W"])


class Sample(unittest.TestCase):
    def calls(self):
        calls = {}
        for plan in ("a", "b", "c"):
            for i in range(8):
                calls[(plan, f"n{i}")] = ["N"] * 3
            calls[(plan, "p")] = ["P"] * 3
        calls[("a", "x")] = ["X"] * 3
        return calls

    def test_the_size_asked_for_is_drawn_without_repeats(self):
        picked = ag.draw_sample(self.calls(), 15, seed=1)
        self.assertEqual(len(picked), 15)
        self.assertEqual(len(set(picked)), 15)

    def test_every_class_present_is_in_the_sample(self):
        calls = self.calls()
        picked = ag.draw_sample(calls, 15, seed=1)
        self.assertEqual({ag.majority(calls[k]) for k in picked}, {"N", "P", "X"})

    def test_a_rare_class_is_not_drawn_past_what_exists(self):
        calls = self.calls()
        picked = ag.draw_sample(calls, 15, seed=1)
        self.assertEqual(sum(1 for k in picked if ag.majority(calls[k]) == "X"), 1)

    def test_every_plan_is_in_the_sample(self):
        self.assertEqual({k[0] for k in ag.draw_sample(self.calls(), 15, seed=1)}, {"a", "b", "c"})

    def test_the_same_seed_draws_the_same_sample(self):
        self.assertEqual(ag.draw_sample(self.calls(), 15, seed=7),
                         ag.draw_sample(self.calls(), 15, seed=7))

    def test_a_benchmark_smaller_than_the_size_is_drawn_whole(self):
        calls = {("a", "1"): ["N"] * 3, ("a", "2"): ["X"] * 3}
        self.assertEqual(sorted(ag.draw_sample(calls, 15, seed=1)), sorted(calls))


class Owner(unittest.TestCase):
    CALLS = {("a", "1"): ["N", "N", "P"], ("a", "2"): ["X", "X", "X"]}

    def test_the_owner_is_compared_with_the_majority(self):
        agreed, total, differ = ag.compare_owner(self.CALLS, {"a:1": "N", "a:2": "P"})
        self.assertEqual((agreed, total), (1, 2))
        self.assertEqual(differ, ["a:2: owner P, matcher X"])

    def test_an_answer_left_empty_is_refused(self):
        with self.assertRaisesRegex(ag.BadRun, "a:1"):
            ag.compare_owner(self.CALLS, {"a:1": ""})


class Wording(unittest.TestCase):
    def test_a_domain_term_is_found_with_its_line(self):
        self.assertEqual(wording_check.find_terms("fine\nthe Bank's API\n"),
                         [(2, "bank"), (2, "api")])

    def test_a_term_inside_another_word_is_not_a_hit(self):
        self.assertEqual(wording_check.find_terms("a rapid embankment"), [])

    def test_a_clean_text_has_no_hits(self):
        self.assertEqual(wording_check.find_terms("every cell has an id"), [])


if __name__ == "__main__":
    unittest.main()
