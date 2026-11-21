import unittest

import coverage as cv


def run(**calls):
    return {("a", bug): value for bug, value in calls.items()}


class Majority(unittest.TestCase):
    def test_two_of_three_wins(self):
        self.assertEqual(cv.majority(["F", "P", "F"]), "F")

    def test_a_three_way_tie_goes_to_the_least_favourable(self):
        self.assertEqual(cv.majority(["F", "P", "X"]), "X")


class ReadRun(unittest.TestCase):
    def test_an_unknown_class_is_refused(self):
        with self.assertRaisesRegex(ValueError, "class 'N'"):
            cv.read_run([{"plan": "a", "id": "1", "class": "N"}], "f")

    def test_a_defect_judged_twice_is_refused(self):
        entry = {"plan": "a", "id": "1", "class": "X", "entries": []}
        with self.assertRaisesRegex(ValueError, "judged twice"):
            cv.read_run([entry, dict(entry)], "f")

    def test_the_same_id_in_two_plans_is_two_defects(self):
        calls = cv.read_run([{"plan": "a", "id": "1", "class": "X", "entries": []},
                             {"plan": "b", "id": "1", "class": "F", "entries": ["sync-01"]}], "f")
        self.assertEqual(calls[("b", "1")], ("F", ("sync-01",)))


class Summarise(unittest.TestCase):
    RUNS = [
        run(b1=("F", ("sync-01",)), b2=("P", ("time-02",)), b3=("X", ())),
        run(b1=("F", ("sync-01",)), b2=("X", ()), b3=("X", ())),
        run(b1=("F", ("sync-03",)), b2=("P", ("time-02",)), b3=("X", ())),
    ]
    LIBRARY = {"sync-01", "sync-03", "time-02", "text-01"}

    def test_the_majority_class_is_counted_per_plan(self):
        self.assertEqual(cv.summarise(self.RUNS, self.LIBRARY)["per_plan"], {"a": {"F": 1, "P": 1, "X": 1}})

    def test_agreement_counts_defects_with_one_class_in_every_run(self):
        result = cv.summarise(self.RUNS, self.LIBRARY)
        self.assertEqual(result["same_class_in_every_run"], 2)
        self.assertEqual(result["split"], ["a:b2 P/X/P"])

    def test_entries_used_are_those_cited_by_runs_that_gave_the_majority_class(self):
        result = cv.summarise(self.RUNS, self.LIBRARY)
        self.assertEqual(result["entries_used"], 3)
        self.assertEqual(result["entries_used_by_action"], {"sync": 2, "time": 1})

    def test_a_cited_entry_the_library_lacks_is_reported(self):
        runs = [run(b1=("F", ("made-up-09",)))]
        self.assertEqual(cv.summarise(runs, self.LIBRARY)["cited_but_not_in_library"], ["made-up-09"])

    def test_runs_judging_different_defects_are_refused(self):
        with self.assertRaisesRegex(ValueError, "run 2"):
            cv.summarise([run(b1=("X", ())), run(b2=("X", ()))], self.LIBRARY)


if __name__ == "__main__":
    unittest.main()
