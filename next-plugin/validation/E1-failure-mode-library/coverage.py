#!/usr/bin/env python3
"""Count what the coverage judge's runs say about the library (no model).

  coverage.py RUNS_DIR LIBRARY.json

RUNS_DIR/run<n>/out.json is one run: [{plan, id, class, entries, reason}],
class F (full), P (part) or X (none). Prints JSON: how often the runs
agree, the majority class per plan, and which entries were ever used.
"""
import collections
import json
import os
import sys

CLASSES = ("F", "P", "X")
LEAST_FAVOURABLE_FIRST = ("X", "P", "F")


def majority(classes):
    """The class most runs gave; on a tie, the least favourable of the tied."""
    counts = collections.Counter(classes)
    top = max(counts.values())
    return min((c for c in counts if counts[c] == top), key=LEAST_FAVOURABLE_FIRST.index)


def read_run(entries, where):
    """Return {(plan, id): (class, entry ids)} or raise ValueError."""
    calls = {}
    for entry in entries:
        key = (entry.get("plan"), entry.get("id"))
        if entry.get("class") not in CLASSES:
            raise ValueError(f"{where}: {key} has class {entry.get('class')!r}")
        if key in calls:
            raise ValueError(f"{where}: {key} judged twice")
        cited = tuple(entry.get("entries", []))
        if entry["class"] != "X" and not cited:
            raise ValueError(f"{where}: {key} is {entry['class']} but cites no entry")
        calls[key] = (entry["class"], cited)
    return calls


def summarise(runs, library_ids):
    """runs: list of {(plan, id): (class, entries)}, one per run."""
    if not runs:
        raise ValueError("no runs to count")
    keys = sorted(runs[0])
    for number, run in enumerate(runs[1:], start=2):
        if sorted(run) != keys:
            raise ValueError(f"run {number} does not judge the same defects as run 1")
    per_plan = collections.defaultdict(collections.Counter)
    used = collections.Counter()
    unknown = set()
    same = 0
    split = []
    for key in keys:
        classes = [run[key][0] for run in runs]
        same += len(set(classes)) == 1
        if len(set(classes)) > 1:
            split.append(f"{key[0]}:{key[1]} {'/'.join(classes)}")
        winner = majority(classes)
        per_plan[key[0]][winner] += 1
        if winner != "X":
            cited = {e for run in runs if run[key][0] == winner for e in run[key][1]}
            for entry in cited:
                if entry in library_ids:
                    used[entry] += 1
                else:
                    unknown.add(entry)
    if unknown:
        raise ValueError(f"entries cited that the library does not have: {sorted(unknown)}")
    total = collections.Counter()
    for counts in per_plan.values():
        total.update(counts)
    by_action = collections.Counter(entry.rsplit("-", 1)[0] for entry in used)
    return {
        "defects": len(keys),
        "runs": len(runs),
        "same_class_in_every_run": same,
        "split": split,
        "majority": {c: total[c] for c in CLASSES},
        "per_plan": {plan: {c: per_plan[plan][c] for c in CLASSES} for plan in sorted(per_plan)},
        "library_entries": len(library_ids),
        "entries_used": len(used),
        "entries_used_by_action": dict(sorted(by_action.items())),
        "most_used": used.most_common(10),
        "cited_but_not_in_library": sorted(unknown),
    }


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    runs_dir, library_path = argv
    with open(library_path, encoding="utf-8") as handle:
        library_ids = {entry["id"] for entry in json.load(handle)}
    runs = []
    for name in sorted(d for d in os.listdir(runs_dir) if d.startswith("run")):
        path = os.path.join(runs_dir, name, "out.json")
        with open(path, encoding="utf-8") as handle:
            runs.append(read_run(json.load(handle), path))
    json.dump(summarise(runs, library_ids), sys.stdout, indent=1)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
