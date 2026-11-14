"""The case-sort tool, without a model: on scratch cases, results and a
reading file,

1. a case's graders are read by kind from `case.yaml` (nested keys, comments
   and a key after the list do not confuse it) and from a markdown case's
   `graders/` directory;
2. the reading file is out of step when a case has no entry, an entry names
   no case, a judge is not read, a grader that is not a judge is listed, a
   verdict is neither tool nor reading or has no reason, or a prompt said
   to state the rule has no quote; and in step otherwise;
3. a run's agent cost is its cost less its judge cost; a run held in two
   result files counts once; a run with no grader result counts for
   nothing, and one marked errored because a grader threw still counts; a
   result file that cannot be read is counted and the report says it is
   incomplete; a case with no run since the date falls back to every held
   run and is marked;
4. the agent's seconds come from the trace's one result line, and a run
   that launched agents has none;
5. deletions are counted per case from the lists and the known-bad files;
6. the report merges the reading into the row, counts the judges a tool
   could decide with their even share of the judge cost, counts the runs
   that failed on judges alone and on such judges alone (an errored run
   counts for nothing), sums a skill over its priced cases, lists the
   prompts and the findings, and is written between the README's markers
   and nowhere else.

Usage: python3 -I evals/tools/case_sort_test.py
"""
import datetime as dt
import json
import os
import sys
import tempfile
import unittest

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import case_sort as cs  # noqa: E402

CASE = """schema_version: "1.0"
name: demo-skill-one
tags: [demo-skill]
execution:
  prompt: |
    Do the thing.
  model: sonnet
runs: 3
graders:
  # a comment between the key and the list
  - type: tool_used
    name: skill-invoked
    tool: Skill
    min: 1
  - type: regex
    name: gate-file-says-pass
    target:
      source: file
      path: out.txt
    pattern: 'type: llm'
  - type: llm
    name: finds-the-problem
    focus:
      source: file
      path: out.md
    criteria: |
      PASS if found.
        - type: llm
  - type: llm
    name: "reply-is-one-line"
    focus: last_message
    criteria: |
      PASS if one line.
after: true
"""
GRADER_MD = """---
type: tool_used
tool: Skill
min: 0
max: 0
---

Must not fire.
"""
SINCE = dt.datetime(2026, 11, 10, tzinfo=dt.timezone.utc)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def result(case, runs):
    return {"cases": [{"name": case, "arms": {"with": runs}}]}


def run(at, cost, judge, seconds=30, trace=None, error=None):
    return {"startedAt": at, "costUsd": cost, "judgeCostUsd": judge, "durationSeconds": seconds,
            "tracePath": trace, "error": error,
            "graders": [] if error else [{"name": "g", "passed": True}]}


class Graders(unittest.TestCase):
    def test_yaml_case_by_kind(self):
        with tempfile.TemporaryDirectory() as d:
            write(os.path.join(d, "case.yaml"), CASE)
            self.assertEqual(cs.graders_of(d), [
                ("skill-invoked", "tool_used"), ("gate-file-says-pass", "regex"),
                ("finds-the-problem", "llm"), ("reply-is-one-line", "llm")])

    def test_markdown_case(self):
        with tempfile.TemporaryDirectory() as d:
            write(os.path.join(d, "prompt.md"), "---\nruns: 3\n---\nA question.\n")
            write(os.path.join(d, "graders", "skill-not-invoked.md"), GRADER_MD)
            self.assertEqual(cs.graders_of(d), [("skill-not-invoked", "tool_used")])

    def test_case_without_graders(self):
        with tempfile.TemporaryDirectory() as d:
            write(os.path.join(d, "case.yaml"), "name: x\nruns: 3\n")
            self.assertEqual(cs.graders_of(d), [])


class Reading(unittest.TestCase):
    cases = {"a": [("j1", "llm"), ("t1", "regex")], "b": [("t2", "tool_used")]}

    def good(self):
        return {
            "a": {"prompt": {"states_rule": "yes", "quote": "next is the gate"},
                  "judges": {"j1": {"by": "tool", "why": "a count"}}},
            "b": {"prompt": {"states_rule": "no"}, "judges": {}},
        }

    def test_in_step(self):
        self.assertEqual(cs.out_of_step(self.good(), self.cases), [])

    def test_each_way_out_of_step(self):
        for change, said in [
            (lambda r: r.pop("b"), "b: not read"),
            (lambda r: r.update(gone={"prompt": {"states_rule": "no"}}), "gone: in the reading file, no such case"),
            (lambda r: r["a"]["judges"].clear(), "a: judge j1 not read"),
            (lambda r: r["a"]["judges"].update(t1={"by": "tool", "why": "x"}), "a: t1 is not a judge"),
            (lambda r: r["a"]["judges"]["j1"].update(by="maybe"), "a: judge j1 needs by"),
            (lambda r: r["a"]["judges"]["j1"].update(why=""), "a: judge j1 needs by"),
            (lambda r: r["a"]["prompt"].pop("quote"), "a: prompt.states_rule is yes with no quote"),
            (lambda r: r["b"]["prompt"].update(states_rule="perhaps"), "b: prompt.states_rule must be"),
        ]:
            reading = self.good()
            change(reading)
            lines = cs.out_of_step(reading, self.cases)
            self.assertTrue(any(l.startswith(said) for l in lines), (said, lines))


class Costs(unittest.TestCase):
    def test_agent_is_cost_less_judge_and_a_run_counts_once(self):
        with tempfile.TemporaryDirectory() as d:
            threw = run("2026-11-11T01:00:00.000Z", 0.30, 0.00)
            threw["error"] = "1 grader(s) threw: grader threw"  # paid for, graders held: still a run
            runs = [run("2026-11-11T01:00:00.000Z", 0.50, 0.10), threw,
                    run("2026-11-11T01:00:00.000Z", 9.0, 9.0, error="You've hit your limit · resets 3am")]
            write(os.path.join(d, "gate-20261111T010000-demo.json"), json.dumps(result("demo", runs)))
            write(os.path.join(d, "2026-11-11T01-00-00-000Z", "aggregate-result.json"), json.dumps(result("demo", runs)))
            write(os.path.join(d, "gate-20261111T020000-demo.json"), '{"cases": [')  # half written
            costs, unreadable = cs.read_costs([d])
            self.assertEqual(unreadable, 1)
            self.assertEqual(len(costs["demo"]), 2)
            row = cs.cost_row(costs["demo"], SINCE)
            self.assertAlmostEqual(row["agent"], 0.35)
            self.assertAlmostEqual(row["judge"], 0.05)
            self.assertEqual((row["runs"], row["old"]), (2, False))

    def test_no_run_since_falls_back_and_is_marked(self):
        with tempfile.TemporaryDirectory() as d:
            write(os.path.join(d, "gate-20261101T010000-demo.json"),
                  json.dumps(result("demo", [run("2026-11-01T01:00:00.000Z", 0.20, 0.05)])))
            row = cs.cost_row(cs.read_costs([d])[0]["demo"], SINCE)
            self.assertTrue(row["old"])
            self.assertAlmostEqual(row["agent"], 0.15)
        self.assertIsNone(cs.cost_row([], SINCE))

    def test_seconds_split_from_the_trace(self):
        with tempfile.TemporaryDirectory() as d:
            plain, launched = os.path.join(d, "plain.jsonl"), os.path.join(d, "launched.jsonl")
            write(plain, '{"type":"assistant"}\n{"type":"result","subtype":"success","duration_ms":21000}\n')
            write(launched, '{"type":"system","subtype":"task_progress","usage":{"duration_ms":5}}\n'
                            '{"type":"result","subtype":"success","duration_ms":9000}\n')
            self.assertEqual(cs.trace_seconds(plain), 21.0)
            self.assertIsNone(cs.trace_seconds(launched))
            self.assertIsNone(cs.trace_seconds(os.path.join(d, "gone.jsonl")))
            runs = [{"at": SINCE, "agent": 0.1, "judge": 0.0, "seconds": 30, "trace": plain},
                    {"at": SINCE, "agent": 0.1, "judge": 0.0, "seconds": 300, "trace": launched}]
            row = cs.cost_row(runs, SINCE)
            self.assertEqual((row["agent_seconds"], row["judge_seconds"]), (21.0, 9.0))
            self.assertEqual(row["seconds"], 165)


class Deletions(unittest.TestCase):
    def test_counted_from_the_lists_and_the_references(self):
        with tempfile.TemporaryDirectory() as d:
            write(os.path.join(d, "tools", "mutants", "demo-skill.json"), json.dumps([
                {"id": "r1", "skill": "demo-skill", "cases": ["demo-skill-one", "demo-skill-two"]},
                {"id": "r2", "skill": "demo-skill", "cases": ["demo-skill-one"]}]))
            write(os.path.join(d, "demo-skill-one", "known-bad", "r1.json"), json.dumps({"fails": ["g1", "g2"]}))
            run_on, caught, passed = cs.deletions(d)
            self.assertEqual((run_on["demo-skill-one"], run_on["demo-skill-two"]), (2, 1))
            self.assertEqual(caught["demo-skill-one"], [("r1", ["g1", "g2"])])
            self.assertEqual(passed, {"demo-skill"})


class Report(unittest.TestCase):
    def text(self):
        cases = {"chunk-runner-one": [("j1", "llm"), ("j2", "llm"), ("t1", "regex")],
                 "chunk-runner-two": [("t2", "tool_used")]}
        reading = {
            "chunk-runner-one": {
                "prompt": {"states_rule": "yes", "quote": "next is the gate", "note": "the action graded"},
                "judges": {"j1": {"by": "tool", "why": "the shape of a line"}, "j2": {"by": "reading", "why": "x"}},
                "findings": ["`t1` cannot fail."]},
            "chunk-runner-two": {"prompt": {"states_rule": "no"}, "judges": {}},
        }
        costs = {"chunk-runner-one": [{"at": SINCE, "agent": 0.50, "judge": 0.10, "seconds": 40, "trace": None}]}
        dels = ({"chunk-runner-one": 3}, {"chunk-runner-one": [("r1", ["t1"])]}, {"chunk-runner"})
        held = lambda failed: {"at": SINCE, "errored": None, "failed": failed, "thrown": []}
        history = {"chunk-runner-one": [held([]), held([("j1", True)]), held([("j2", True)]),
                                        held([("j1", True), ("t1", False)]),
                                        {"at": SINCE, "errored": "usage limit", "failed": [], "thrown": []}]}
        return cs.report(cases, reading, costs, history, {}, dels, SINCE, 0.40, 6, ["results"])

    def test_row_counts_and_lists(self):
        text = self.text()
        self.assertIn('| `chunk-runner-one` | chunk-runner | 1 regex | 2 | 1 of 2 | yes: "next is the gate"'
                      " | 0.50 | 0.10 | 40 | 3 of 4 (few runs) | 1 of 3: `r1` |", text)
        self.assertIn("of 4 completed runs since the bars, 3 failed; 2 of those failed on judges alone, and 1 on judges"
                      " a tool could decide alone ($0.60 of runs at today's cost per run): `chunk-runner-one` 1.", text)
        self.assertIn("| chunk-runner | 2 (1) | 0.50 | 0.10 | 2 | 1 | 0.05 | 1, 0 | 0 |", text)
        self.assertIn("| `chunk-runner-two` | chunk-runner | 1 tool call | 0 |  | no |  |  |  | 0 of 0 (few runs) | none run |", text)
        self.assertIn("**Judges a tool could decide:** 1 of 2, in 1 cases; 0 cases would be left with no judge.", text)
        self.assertIn("$0.05 per run of every case", text)  # half of the case's judge cost
        self.assertIn("**Prompt states the rule it grades:** yes 1, partly 0, no 1.", text)
        self.assertIn("| `chunk-runner-one` | `j1` | the shape of a line | 0.050 |", text)
        self.assertIn("- `chunk-runner-one`: `t1` cannot fail.", text)
        self.assertIn("$0.60 over the 1 cases with a completed run held", text)

    def test_unreadable_results_are_said(self):
        self.assertNotIn("Incomplete", self.text())
        text = cs.report({}, {}, {}, {}, {}, ({}, {}, set()), SINCE, 0.40, 6, ["results"], unreadable=2)
        self.assertIn("**Incomplete: 2 result files could not be read**", text.split("\n")[0])

    def test_written_between_the_markers_only(self):
        with tempfile.TemporaryDirectory() as d:
            readme = os.path.join(d, "README.md")
            write(readme, f"before\n{cs.START}\nold\n{cs.END}\nafter\n")
            self.assertTrue(cs.write_readme(readme, "new\n"))
            self.assertEqual(cs.read_text(readme), f"before\n{cs.START}\nnew\n{cs.END}\nafter\n")
            write(readme, "no markers\n")
            self.assertFalse(cs.write_readme(readme, "new\n"))
            self.assertEqual(cs.read_text(readme), "no markers\n")


if __name__ == "__main__":
    unittest.main()
