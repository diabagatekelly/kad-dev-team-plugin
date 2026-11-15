#!/usr/bin/env python3
"""Blind side-by-side judge for a `claude plugin eval --ablation with-without` run.

`claude plugin eval` scores each arm against fixed graders but never compares
the with-plugin and without-plugin outputs to each other, and its judges answer
with one word, so no reasoning is kept. This script pairs run i of each arm,
asks a judge which review is better in both presentation orders (to cancel
position bias), and writes every verdict with its reasoning to
<results-dir>/pairwise.json.

The judge itself (the `claude -p` call, both orders, the verdict) is
`implementation_judge.py` next to this file (it was the orchestrator's
Combine-step judge until the chunk loop replaced that flow on 2026-10-24;
the evals keep it); this file only supplies the review rubric and the
results-dir plumbing.

`--rubric work` is for cases whose output is not a code review: the first
turn of a requirements or design skill (questions to the owner, a proposal,
a document). The default, `review`, is the rubric the review skills' passes
were judged with.

Usage: python3 -I evals/tools/pairwise_judge.py <results-dir> [--model sonnet] [--rubric review|work]
"""
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from implementation_judge import compare  # noqa: E402

REVIEW_RUBRIC = """You are judging two code reviews of the same code. You do not know who wrote either one.

Decide which review would serve the developer better. Weigh, in order:
1. Correctness: does it identify the real problems in this code, and does it avoid claims that are false about the code shown?
2. Judgment: are the most important problems clearly separated from minor or optional ones, with sensible priorities?
3. Actionability: would its fixes actually solve the problems?

Ignore length, formatting, tone, and whether it uses any particular named rule or vocabulary. A longer review is not better unless the extra content is correct and useful."""


WORK_RUBRIC = """You are judging two responses to the same request. The request is one step of planning a piece of software: requirements, acceptance criteria, a design, a technology choice, or the questions to settle before one of those can be written. You do not know who wrote either response.

Decide which response would serve the person who asked better. Weigh, in order:
1. Fit to the request and to the material it points at: does it do the step that was asked, no more and no less, and does it avoid claims that are false about that material?
2. Judgment: does it separate what must be decided by the person from what it can settle itself, and are the things it raises the ones that matter for this step?
3. Usability: could the person act on it as it stands (answer its questions, approve it, build from it)?

A response that asks the person the questions the step depends on, instead of answering them itself, is not worse for that; a response that invents answers the material does not give is worse. Ignore length, formatting, tone, and whether it uses any particular named rule or vocabulary. A longer response is not better unless the extra content is correct and useful."""

RUBRICS = {"review": (REVIEW_RUBRIC, "review"), "work": (WORK_RUBRIC, "response")}


def last_message(run):
    """The CLI stores the agent's final message as `evidence` on each llm grader."""
    for grader in run["graders"]:
        if grader.get("evidence"):
            return grader["evidence"]
    return None


def judge_pair(job):
    case, index, with_review, without_review, request, model, rubric = job
    text, tag = RUBRICS[rubric]
    result = compare(request, {"with": with_review, "without": without_review},
                     text, model, tag=tag)
    # The shape earlier runs' pairwise.json files have: orders keyed by who
    # was shown first, winners named by arm.
    return {"case": case, "run": index,
            "orders": {f"{o['first']}_first": {k: o[k] for k in ("winner", "reasoning", "error") if k in o}
                       for o in result["orders"]},
            "verdict": result["verdict"], "cost_usd": result["cost_usd"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results_dir", type=Path)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--rubric", choices=sorted(RUBRICS), default="review")
    parser.add_argument("-j", "--concurrency", type=int, default=4)
    args = parser.parse_args()

    aggregate = json.loads((args.results_dir / "aggregate-result.json").read_text())
    jobs = []
    for case in aggregate["cases"]:
        with_runs, without_runs = case["arms"].get("with", []), case["arms"].get("without") or []
        for index, (w, wo) in enumerate(zip(with_runs, without_runs)):
            with_review, without_review = last_message(w), last_message(wo)
            if with_review and without_review:
                jobs.append((case["name"], index, with_review, without_review,
                             case["promptMarkdown"], args.model, args.rubric))
    if not jobs:
        sys.exit("no paired with/without outputs found (cases need an llm grader for the CLI to keep output)")

    with ThreadPoolExecutor(args.concurrency) as pool:
        pairs = list(pool.map(judge_pair, jobs))

    summary = {}
    for pair in pairs:
        tally = summary.setdefault(pair["case"], {"with": 0, "without": 0, "tie": 0, "split": 0})
        tally[pair["verdict"]] = tally.get(pair["verdict"], 0) + 1  # "no verdict" when a judge call failed
    out = {"model": args.model, "rubric": args.rubric, "summary": summary, "pairs": pairs,
           "cost_usd": sum(p["cost_usd"] for p in pairs)}
    (args.results_dir / "pairwise.json").write_text(json.dumps(out, indent=2))
    for case, tally in summary.items():
        print(f"{case}: with={tally['with']} without={tally['without']} tie={tally['tie']} split={tally['split']}")
    print(f"judge cost: ${out['cost_usd']:.2f} -> {args.results_dir / 'pairwise.json'}")


if __name__ == "__main__":
    main()
