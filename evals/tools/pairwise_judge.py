#!/usr/bin/env python3
"""Blind side-by-side judge for a `claude plugin eval --ablation with-without` run.

`claude plugin eval` scores each arm against fixed graders but never compares
the with-plugin and without-plugin outputs to each other, and its judges answer
with one word, so no reasoning is kept. This script pairs run i of each arm,
asks a judge which review is better in both presentation orders (to cancel
position bias), and writes every verdict with its reasoning to
<results-dir>/pairwise.json.

Usage: python3 -I evals/tools/pairwise_judge.py evals/results/<timestamp> [--model sonnet]
"""
import argparse
import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

JUDGE_PROMPT = """You are judging two code reviews of the same code. You do not know who wrote either one.

The request and the code under review:
<request>
{request}
</request>

<review_1>
{first}
</review_1>

<review_2>
{second}
</review_2>

Decide which review would serve the developer better. Weigh, in order:
1. Correctness: does it identify the real problems in this code, and does it avoid claims that are false about the code shown?
2. Judgment: are the most important problems clearly separated from minor or optional ones, with sensible priorities?
3. Actionability: would its fixes actually solve the problems?

Ignore length, formatting, tone, and whether it uses any particular named rule or vocabulary. A longer review is not better unless the extra content is correct and useful.

Respond with only a JSON object, no code fence:
{{"reasoning": "<3-6 sentences>", "winner": "1" | "2" | "tie"}}"""


def last_message(run):
    """The CLI stores the agent's final message as `evidence` on each llm grader."""
    for grader in run["graders"]:
        if grader.get("evidence"):
            return grader["evidence"]
    return None


def ask_judge(prompt, model):
    with tempfile.TemporaryDirectory() as cwd:
        proc = subprocess.run(
            ["claude", "-p", "--model", model, "--tools", "",
             "--disable-slash-commands", "--strict-mcp-config",
             "--no-session-persistence", "--output-format", "json"],
            input=prompt, capture_output=True, text=True, cwd=cwd, timeout=300,
        )
    envelope = json.loads(proc.stdout)
    text = envelope["result"]
    # The judge sometimes wraps or prefixes the JSON; take the outermost object.
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError(f"judge returned no JSON object: {text[:200]!r}")
    verdict = json.loads(text[start:end + 1])
    if verdict.get("winner") not in ("1", "2", "tie"):
        raise ValueError(f"judge returned an unexpected winner: {verdict!r}")
    return verdict, envelope.get("total_cost_usd", 0.0)


def judge_pair(job):
    case, index, with_review, without_review, request, model = job
    orders = {"with_first": (with_review, without_review),
              "without_first": (without_review, with_review)}
    result = {"case": case, "run": index, "orders": {}, "cost_usd": 0.0}
    for order, (first, second) in orders.items():
        verdict, cost = ask_judge(
            JUDGE_PROMPT.format(request=request, first=first, second=second), model)
        winner_arm = {"1": order.split("_")[0], "2": "without" if order == "with_first" else "with",
                      "tie": "tie"}[verdict["winner"]]
        result["orders"][order] = {"winner": winner_arm, "reasoning": verdict["reasoning"]}
        result["cost_usd"] += cost
    winners = {o["winner"] for o in result["orders"].values()}
    result["verdict"] = winners.pop() if len(winners) == 1 else "split"
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results_dir", type=Path)
    parser.add_argument("--model", default="sonnet")
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
                             case["promptMarkdown"], args.model))
    if not jobs:
        sys.exit("no paired with/without outputs found (cases need an llm grader for the CLI to keep output)")

    with ThreadPoolExecutor(args.concurrency) as pool:
        pairs = list(pool.map(judge_pair, jobs))

    summary = {}
    for pair in pairs:
        tally = summary.setdefault(pair["case"], {"with": 0, "without": 0, "tie": 0, "split": 0})
        tally[pair["verdict"]] += 1
    out = {"model": args.model, "summary": summary, "pairs": pairs,
           "cost_usd": sum(p["cost_usd"] for p in pairs)}
    (args.results_dir / "pairwise.json").write_text(json.dumps(out, indent=2))
    for case, tally in summary.items():
        print(f"{case}: with={tally['with']} without={tally['without']} tie={tally['tie']} split={tally['split']}")
    print(f"judge cost: ${out['cost_usd']:.2f} -> {args.results_dir / 'pairwise.json'}")


if __name__ == "__main__":
    main()
