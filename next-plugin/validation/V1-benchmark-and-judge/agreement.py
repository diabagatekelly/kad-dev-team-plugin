#!/usr/bin/env python3
"""Measure the matcher against itself and against the owner (step V1).

Layout it reads (outside this public repository, since it quotes projects):
  RUNS/<plan>/run<n>/out.json   one matcher run: [{id, class, cells, reason}]
  BENCH/<plan>.json             the benchmark: [{id, title, trigger, ...}]

Commands:
  summary RUNS BENCH              agreement counts, as JSON on stdout
  sample  RUNS BENCH OUT [--seed] draw 15 calls for the owner to judge blind
  owner   RUNS ANSWERS            compare the owner's classes with the majority
No model is used here.
"""
import argparse
import collections
import json
import os
import random
import sys

CLASSES = ("N", "D", "W", "P", "X")
NAMED = frozenset(("N", "D"))
# Least favourable to the tables first; breaks a three-way tie.
LEAST_FAVOURABLE_FIRST = ("X", "W", "P", "D", "N")


class BadRun(ValueError):
    """A matcher output that cannot be scored as it stands."""


def check_run(entries, bug_ids, where):
    """Return {bug id: class} or raise BadRun naming what is wrong."""
    seen = {}
    for entry in entries:
        bug, cls = entry.get("id"), entry.get("class")
        if cls not in CLASSES:
            raise BadRun(f"{where}: bug {bug!r} has class {cls!r}")
        if bug in seen:
            raise BadRun(f"{where}: bug {bug!r} scored twice")
        seen[bug] = cls
    missing = [b for b in bug_ids if b not in seen]
    extra = [b for b in seen if b not in bug_ids]
    if missing or extra:
        raise BadRun(f"{where}: missing {missing}, not in the benchmark {extra}")
    return seen


def majority(classes):
    """The class most runs gave; on a tie, the least favourable of the tied."""
    counts = collections.Counter(classes)
    top = max(counts.values())
    tied = [c for c in counts if counts[c] == top]
    return min(tied, key=LEAST_FAVOURABLE_FIRST.index)


def agreement(calls):
    """calls: {(plan, bug): [class per run]} -> counts for the bar."""
    total = len(calls)
    same_class = sum(1 for c in calls.values() if len(set(c)) == 1)
    same_named = sum(1 for c in calls.values() if len({x in NAMED for x in c}) == 1)
    per_plan = collections.defaultdict(lambda: collections.defaultdict(int))
    bugs_per_plan = collections.Counter()
    for (plan, _bug), classes in calls.items():
        bugs_per_plan[plan] += 1
        for run, cls in enumerate(classes, start=1):
            per_plan[plan][run] += cls in NAMED
    return {
        "bugs": total,
        "runs": len(next(iter(calls.values()))) if calls else 0,
        "same_named_or_not": same_named,
        "same_class": same_class,
        "majority_classes": dict(collections.Counter(majority(c) for c in calls.values())),
        "named_per_plan_per_run": {
            plan: {"bugs": bugs_per_plan[plan],
                   "named": [per_plan[plan][r] for r in sorted(per_plan[plan])]}
            for plan in sorted(per_plan)
        },
        "split": sorted(f"{plan}:{bug} {'/'.join(c)}"
                        for (plan, bug), c in calls.items() if len(set(c)) > 1),
    }


def draw_sample(calls, size, seed):
    """Pick `size` (plan, bug) keys spread over majority classes, then plans.

    Every class present gets at least one place, the rest go in proportion;
    inside a class the plan with the fewest picks so far goes next.
    """
    rng = random.Random(seed)
    by_class = collections.defaultdict(list)
    for key in sorted(calls):
        by_class[majority(calls[key])].append(key)
    size = min(size, len(calls))
    quota = {cls: 1 for cls in by_class}
    while sum(quota.values()) > size:
        quota.pop(min(quota, key=lambda c: len(by_class[c])))
    while sum(quota.values()) < size:
        open_classes = [c for c in quota if quota[c] < len(by_class[c])]
        quota[max(open_classes, key=lambda c: len(by_class[c]) / quota[c])] += 1
    picked, per_plan = [], collections.Counter()
    for cls in sorted(quota):
        pool = by_class[cls][:]
        rng.shuffle(pool)
        for _ in range(quota[cls]):
            choice = min(pool, key=lambda key: per_plan[key[0]])
            pool.remove(choice)
            per_plan[choice[0]] += 1
            picked.append(choice)
    rng.shuffle(picked)
    return picked


def compare_owner(calls, answers):
    """answers: {"plan:bug": class} -> (agreed, total, the disagreements)."""
    agreed, differ = 0, []
    for label, owner_class in sorted(answers.items()):
        plan, bug = label.split(":", 1)
        if owner_class not in CLASSES:
            raise BadRun(f"owner answer {label}: class {owner_class!r}")
        judge = majority(calls[(plan, bug)])
        if judge == owner_class:
            agreed += 1
        else:
            differ.append(f"{label}: owner {owner_class}, matcher {judge}")
    return agreed, len(answers), differ


def load(runs_dir, bench_dir):
    """Read every run of every plan; return (calls, cells cited, benchmark)."""
    calls, cited, bench = {}, collections.defaultdict(dict), {}
    for name in sorted(os.listdir(bench_dir)):
        if not name.endswith(".json"):
            continue
        plan = name[:-5]
        with open(os.path.join(bench_dir, name), encoding="utf-8") as handle:
            bench[plan] = {b["id"]: b for b in json.load(handle)}
        plan_dir = os.path.join(runs_dir, plan)
        runs = sorted(d for d in os.listdir(plan_dir) if d.startswith("run"))
        for run in runs:
            path = os.path.join(plan_dir, run, "out.json")
            with open(path, encoding="utf-8") as handle:
                entries = json.load(handle)
            for bug, cls in check_run(entries, list(bench[plan]), path).items():
                calls.setdefault((plan, bug), []).append(cls)
            for entry in entries:
                for cell in entry.get("cells", []):
                    cited[(plan, entry["id"])].setdefault(cell["id"], cell.get("quote", ""))
    return calls, cited, bench


def write_sheet(picked, cited, bench, out_dir):
    """The owner's sheet (no classes shown) and an empty answers file."""
    os.makedirs(out_dir, exist_ok=True)
    lines = ["# Fifteen calls to judge", "",
             "For each defect, read the cells the matcher's runs pointed at and give one class:",
             "N (a silent or contradicting cell states the trigger and what goes wrong), "
             "D (decided soundly, the build did otherwise), W (the decision itself is the defect), "
             "P (touched but short of those), X (no cell names the trigger).",
             "Write your class in `answers.json` beside this file.", ""]
    answers = {}
    for number, (plan, bug) in enumerate(picked, start=1):
        item = bench[plan][bug]
        answers[f"{plan}:{bug}"] = ""
        lines += [f"## {number}. {plan}:{bug}  {item['title']}", "",
                  f"- **When:** {item['trigger']}",
                  f"- **What the build does:** {item['build_behaviour']}",
                  f"- **What the person meets:** {item['harm']}", "",
                  "Cells cited by any run:"]
        cells = cited.get((plan, bug), {})
        lines += [f"- `{cell}`: {quote}" for cell, quote in sorted(cells.items())] or ["- (none cited)"]
        lines.append("")
    with open(os.path.join(out_dir, "sheet.md"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    with open(os.path.join(out_dir, "answers.json"), "w", encoding="utf-8") as handle:
        json.dump(answers, handle, indent=1)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("summary", "sample", "owner"):
        cmd = sub.add_parser(name)
        cmd.add_argument("runs")
        if name == "owner":
            cmd.add_argument("answers")
        cmd.add_argument("bench")
        if name == "sample":
            cmd.add_argument("out")
            cmd.add_argument("--seed", type=int, default=20261120)
            cmd.add_argument("--size", type=int, default=15)
    args = parser.parse_args(argv)
    calls, cited, bench = load(args.runs, args.bench)
    if args.command == "summary":
        json.dump(agreement(calls), sys.stdout, indent=1)
        print()
    elif args.command == "sample":
        picked = draw_sample(calls, args.size, args.seed)
        write_sheet(picked, cited, bench, args.out)
        print(f"{len(picked)} calls written to {args.out}")
    else:
        with open(args.answers, encoding="utf-8") as handle:
            agreed, total, differ = compare_owner(calls, json.load(handle))
        print(f"{agreed} of {total} agree")
        print("\n".join(differ))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
