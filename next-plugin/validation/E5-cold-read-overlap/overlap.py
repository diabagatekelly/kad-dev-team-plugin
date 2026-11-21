#!/usr/bin/env python3
"""Count how independent readers' findings overlap (no model).

  overlap.py MATCHING.json

MATCHING.json is a list of distinct defects, each {"id", "title",
"found_by": [reader names]}: the result of deciding which of several
readers' findings are the same defect. Prints JSON: what each reader
found, what a further reader adds on average, and an estimate of how
many defects no reader found.
"""
import itertools
import json
import sys


def readers_of(defects):
    return sorted({reader for defect in defects for reader in defect["found_by"]})


def added_by_position(defects, readers):
    """Average, over every order of the readers, of the new defects the k-th reader adds."""
    totals = [0] * len(readers)
    orders = list(itertools.permutations(readers))
    for order in orders:
        seen = set()
        for position, reader in enumerate(order):
            found = {d["id"] for d in defects if reader in d["found_by"]}
            totals[position] += len(found - seen)
            seen |= found
    return [round(total / len(orders), 2) for total in totals]


def unseen_estimate(defects):
    """Chao's lower bound on defects no reader found, from those found once and twice."""
    once = sum(1 for d in defects if len(d["found_by"]) == 1)
    twice = sum(1 for d in defects if len(d["found_by"]) == 2)
    if twice:
        return round(once * once / (2 * twice), 1)
    return round(once * (once - 1) / 2, 1)


def summarise(defects, threshold=3):
    readers = readers_of(defects)
    added = added_by_position(defects, readers)
    worth = 0
    for position, gain in enumerate(added, start=1):
        if gain < threshold:
            break
        worth = position
    by_count = {}
    for defect in defects:
        by_count[len(defect["found_by"])] = by_count.get(len(defect["found_by"]), 0) + 1
    return {
        "readers": len(readers),
        "distinct_defects": len(defects),
        "found_by_each": {r: sum(1 for d in defects if r in d["found_by"]) for r in readers},
        "found_by_how_many_readers": {str(k): by_count[k] for k in sorted(by_count)},
        "added_by_the_kth_reader_on_average": added,
        "share_of_all_found_after_k_readers": [
            round(sum(added[: k + 1]) / len(defects), 2) for k in range(len(added))] if defects else [],
        "readers_worth_running_by_the_rule": worth,
        "estimated_defects_no_reader_found": unseen_estimate(defects),
    }


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 2
    with open(argv[0], encoding="utf-8") as handle:
        json.dump(summarise(json.load(handle)), sys.stdout, indent=1)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
