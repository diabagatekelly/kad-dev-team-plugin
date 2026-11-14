#!/usr/bin/env python3
"""Regex graders whose pattern is a fixture file's own text.

`claude plugin eval` has no grader that runs code (checked against its
documentation for 2.1.325: regex, tool_used, tool_order, file_exists, llm,
baseline). A check that compares a run's file with what the fixture held
before the run is therefore one regex with the fixture's text written into
it, and nobody should write that by hand. This writes them (TODO.md, E5):

  slice-placeholder-filled      accessibility-review-payfine, -payfine-subtle
      the fixture's slice with its accessibility placeholder line replaced
      by a line that names accessibility or a document, and every other
      line as it was (whitespace folded)
  keeps-existing-rows-and-tiers map-update-cancel-hold
      every source row of the fixture's earlier map still in the table with
      the tier it had (rows under test/ left out: the extractor drops them)

Usage: python3 -I evals/tools/fixture_patterns.py --check   # the cases hold what the fixtures give
       python3 -I evals/tools/fixture_patterns.py --write   # put the patterns into the cases
       python3 -I evals/tools/fixture_patterns.py --json    # the patterns, to test them

A fixture edit that changes one of these files fails `--check` until
`--write` is run and the case has its gate run again.
"""
import argparse
import json
import os
import re
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
EVALS = os.path.dirname(TOOLS)
FIXTURE = os.path.join(EVALS, "fixtures", "library-app")
PLACEHOLDER = "- [ACCESSIBILITY — placeholder, to be authored by accessibility-engineer]"


def escape(text):
    """Escape for a JavaScript regex without flags."""
    return re.sub(r"[.*+?^${}()|\[\]\\/]", lambda m: "\\" + m.group(0), text)


def folded(text):
    return re.sub(r"\s+", lambda m: r"\s+", escape(text.strip()))


def slice_placeholder(slice_text):
    text = slice_text.strip()
    if text.count(PLACEHOLDER) != 1:
        raise SystemExit("the fixture's slice does not hold the accessibility placeholder line exactly once")
    before, after = text.split(PLACEHOLDER)
    filled = r"(?![\s\S]*ACCESSIBILITY — placeholder)[-*] (?=[\s\S]{0,400}?(?:[Aa]ccessib|\.md\b))\S[\s\S]{1,6000}?"
    tail = r"\s+" + folded(after) if after.strip() else ""
    return r"^\s*" + folded(before) + r"\s+" + filled + tail + r"\s*$"


def map_rows(map_text):
    rows = []
    for line in map_text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not re.match(r"[\w./-]+\.\w+$", cells[0]) or cells[0].startswith("test/"):
            continue
        rows.append((cells[0], cells[1]))
    if not rows:
        raise SystemExit("the fixture's earlier map has no module rows")
    return "^" + "".join(
        r"(?=[\s\S]*\|\s*\x60?%s\x60?\s*\|\s*%s\s*\|)" % (escape(path), escape(tier)) for path, tier in rows)


def read(*parts):
    with open(os.path.join(FIXTURE, *parts), encoding="utf-8") as f:
        return f.read()


def patterns():
    """{(case, grader): pattern}"""
    slice_pattern = slice_placeholder(read("ui-plants", "pay-fine", "slice-001.md"))
    return {
        ("accessibility-review-payfine", "slice-placeholder-filled"): slice_pattern,
        ("accessibility-review-payfine-subtle", "slice-placeholder-filled"): slice_pattern,
        ("map-update-cancel-hold", "keeps-existing-rows-and-tiers"):
            map_rows(read("code-plants", "map", "update", "docs", "architecture-map.md")),
    }


def quoted(pattern):
    return "'" + pattern.replace("'", "''") + "'"


def in_case(text, grader):
    """(start, end) of the grader's pattern value in a case file, or None."""
    block = re.search(r"(?m)^    name: %s\n(?:    (?!name: ).*\n|      .*\n)*?    pattern: (.*)$" % re.escape(grader), text)
    return block.span(1) if block else None


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--write", action="store_true")
    g.add_argument("--json", action="store_true")
    a = p.parse_args()
    want = patterns()
    if a.json:
        json.dump({f"{case}::{grader}": pattern for (case, grader), pattern in want.items()}, sys.stdout)
        return 0
    stale = 0
    for (case, grader), pattern in sorted(want.items()):
        path = os.path.join(EVALS, case, "case.yaml")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        span = in_case(text, grader)
        if span is None:
            print(f"FAIL  {case} / {grader}: no such regex grader in the case")
            stale += 1
        elif text[span[0]:span[1]] == quoted(pattern):
            print(f"PASS  {case} / {grader}")
        elif a.write:
            # written beside the case and moved into place, so a write that
            # stops half way leaves the case as it was
            with open(path + ".tmp", "w", encoding="utf-8") as f:
                f.write(text[:span[0]] + quoted(pattern) + text[span[1]:])
            os.replace(path + ".tmp", path)
            print(f"WROTE {case} / {grader}")
        else:
            print(f"FAIL  {case} / {grader}: the pattern is not what the fixture gives; run --write, then the case's gate run")
            stale += 1
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
