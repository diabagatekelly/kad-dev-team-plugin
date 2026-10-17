"""Re-ask the eval's own judge about one llm grader in a `--json` result.

`claude plugin eval` keeps each judge's one-word vote but not its reason, and
`claude -p --model sonnet` can reach a different model from the eval's
`--judge-model sonnet`, so a quick re-ask in a terminal is no check at all.
This rebuilds the eval's judge call from the result file (the grader's
criteria from the case, the graded text from the grader's `evidence`) and
sends it to the model the eval used, with the same system prompt and the
same one-word instruction. A vote counts as PASS only if the reply says PASS
and never says FAIL, as in the eval.

This is a hint, not a replay: the eval's judge has failed outputs 3/3 that
this passes 5/5, most often on long `last_message` graders, and on a
borderline output neither is stable. Only a run of the eval itself is
authoritative.

--explain asks the same model for a verdict and the reason, which is how to
find out what a failing vote objects to. An explained verdict can differ
from the one-word one.

Usage: python3 -I evals/tools/rejudge.py <result.json> <grader> [--run N]
           [--votes N] [--criteria-from evals/<case>/case.yaml] [--explain]
  --criteria-from  grade with that file's current criteria for the grader
                   instead of the ones recorded in the result (to check a
                   reworded grader against an old output)
"""
import argparse
import json
import re
import subprocess

JUDGE_MODEL = "claude-sonnet-5-5"
SYSTEM = "You are a strict, terse evaluation judge for coding-agent traces."


def criteria_from_case(path, grader):
    try:
        import yaml  # the WSL clone has PyYAML; ruby is the fallback where it doesn't
        case = yaml.safe_load(open(path, encoding="utf-8"))
    except ImportError:
        out = subprocess.check_output(
            ["ruby", "-ryaml", "-rjson", "-e", "puts YAML.load_file(ARGV[0]).to_json", path])
        case = json.loads(out)
    for g in case["graders"]:
        if g["name"] == grader:
            return g["criteria"], g.get("focus")
    raise SystemExit(f"{path} has no grader named {grader}")


def ask(prompt, system=SYSTEM):
    args = ["claude", "-p", "--model", JUDGE_MODEL, "--tools", ""]
    if system:
        args += ["--system-prompt", system]
    # The prompt goes on stdin: `--tools` takes several values and would
    # swallow a prompt passed after it as one more tool name.
    # An argument list, no shell: the model id is a module constant, the system
    # prompt is this file's, and the judged text travels on stdin, so nothing a
    # result file or a case contains can become a command.
    reply = subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
        args, input=prompt, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    return "\n".join(l for l in reply.splitlines() if "connectors are disabled" not in l).strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("result")
    p.add_argument("grader")
    p.add_argument("--run", type=int, default=None)
    p.add_argument("--votes", type=int, default=3)
    p.add_argument("--criteria-from")
    p.add_argument("--explain", action="store_true")
    a = p.parse_args()

    case = json.load(open(a.result))["cases"][0]
    spec = next(g for g in case["graders"] if g["name"] == a.grader)
    criteria, focus = spec["config"]["criteria"], spec["config"].get("focus")
    if a.criteria_from:
        criteria, focus = criteria_from_case(a.criteria_from, a.grader)
    label = f"file {focus['path']}" if isinstance(focus, dict) else focus

    runs = case["arms"]["with"]
    picked = [a.run] if a.run is not None else range(len(runs))
    for i in picked:
        g = next(g for g in runs[i]["graders"] if g["name"] == a.grader)
        output = g.get("evidence") or ""
        if a.explain:
            print(f"run {i}:\n" + ask(
                f"Grade the output of a coding agent against a criterion. Give PASS or "
                f"FAIL, then quote the part of the criterion and of the output that "
                f"decides it.\nCriterion:\n{criteria}\nAgent output ({label}):\n{output}",
                system=None))
            continue
        prompt = (f"You are grading the output of a coding agent against a criterion.\n"
                  f"Criterion:\n{criteria}\nAgent output ({label}):\n{output}\n"
                  f"Respond with exactly one word: PASS or FAIL.")
        votes = []
        for _ in range(a.votes):
            reply = ask(prompt)
            votes.append("PASS" if re.search(r"\bPASS\b", reply, re.I)
                         and not re.search(r"\bFAIL\b", reply, re.I) else "FAIL")
        print(f"run {i}: was {'PASS' if g.get('passed') else 'FAIL'}, now {' '.join(votes)}")


if __name__ == "__main__":
    main()
