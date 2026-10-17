#!/usr/bin/env python3
"""Blind pairwise judge for the orchestrator's Combine step.

Two `tdd-implementation` candidates built the same slice in two worktrees.
Before the orchestrator reads them and makes its combine call, this script
shows a judge the slice's brief and both candidates' changes with nothing
that identifies either (no paths, no branch names, no reviewer findings),
in both presentation orders so position bias cancels, and keeps every
verdict with its reasoning. The judge is a model with no tools, run through
`claude -p`; it cannot run the tests or look anything up, so it judges the
code and tests as written against the brief as written. Its verdict is
information for the orchestrator's own call, not the call itself: the
skill says how the two relate.

What the judge sees per candidate: every file the candidate changed since
the gate's baseline (the same change set `validation_gate.py` computes:
tracked changes against the baseline commit plus untracked files, minus
files the baseline recorded whose content is unchanged), each with its
content, minus `--exclude` entries (the candidate's own report: a
self-description is not the code) and anything binary. Lock files sort
last and `--max-bytes` caps each candidate, so a huge dependency lock is
what gets truncated first; the judge is told when something was cut.

Exit 0 on a verdict (`candidate 1`, `candidate 2`, `tie`, or `split` when
the two orders disagree), 2 when there is no verdict: the judge could not
be run, answered twice with something other than a verdict, or a
candidate's change set could not be computed. Output: the verdict line last,
both orders' reasoning above it, and `--out` (default: next to the
baseline file as `kad-pairwise.json`) with everything, including which
files each candidate's view held and whether it was truncated.

The eval suite's `evals/tools/pairwise_judge.py` imports `compare()` from
here to judge with-plugin against without-plugin review runs; the judge
mechanics live in one place, inside the plugin, because a skill can only
run a script that ships with it.

Usage: python3 -I ${CLAUDE_SKILL_DIR}/scripts/pairwise_judge.py
           --candidate "<worktree 1>" --candidate "<worktree 2>"
           --baseline "<project>/.git/kad-gate-baseline.json" | --base <commit>
           --task "<design doc>" --task "<slice file>" [--task ...]
           [--exclude "<report path>" ...] [--model sonnet] [--max-bytes 200000]
           [--timeout 300] [--out FILE]
       (from this repository: python3 -I skills/orchestrator/scripts/pairwise_judge.py ...)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

# `python -I` leaves the script's own directory off sys.path; the gate's
# change-set helpers live next to this file.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validation_gate  # noqa: E402

IMPLEMENTATION_RUBRIC = """You are judging two implementations of the same slice of work, each with its tests. You do not know who wrote either one, and you cannot run anything: judge the code and tests as written against the brief as written.

Decide which implementation is the better basis for the finished slice. Weigh, in order:
1. Behaviour: does it do what the brief asks (every acceptance criterion and runtime-safety criterion the brief states) and nothing the brief does not ask for? A criterion not met, or met by assuming something the brief leaves open without saying so, counts against it. Code the slice does not need counts against it.
2. Tests: do the tests exercise the behaviour the criteria describe, through the module's public interface, and would they fail if that behaviour broke? Tests that mirror the implementation, mock the thing under test, or cannot fail count against it.
3. Boundaries: does the code live in the modules the brief names, with dependencies pointing the direction the brief states? Logic in the wrong module, or a dependency the brief forbids, counts against it.
4. Clarity: could someone fix a defect in it without reading the other implementation? Simplicity, not brevity.

Ignore length, comment volume, formatting and naming style. More code is not better unless the extra code is needed for the brief. If one view was truncated, judge what is shown and say so in your reasoning."""

JUDGE_PROMPT = """{rubric}

The brief:
<brief>
{request}
</brief>

<{tag}_1>
{first}
</{tag}_1>

<{tag}_2>
{second}
</{tag}_2>

You have no tools and nothing to look up; everything is above. Respond with only a JSON object, no code fence:
{{"reasoning": "<3-6 sentences>", "winner": "1" | "2" | "tie"}}"""


class JudgeError(Exception):
    pass


def ask_judge(prompt, model, timeout=300):
    """One judge call. Returns (verdict dict, cost in USD)."""
    claude = shutil.which("claude")
    if not claude:
        raise JudgeError("`claude` is not on PATH; the judge runs through `claude -p`")
    with tempfile.TemporaryDirectory() as cwd:  # no project CLAUDE.md, no settings
        proc = subprocess.run(
            [claude, "-p", "--model", model, "--tools", "",
             "--disable-slash-commands", "--strict-mcp-config",
             "--no-session-persistence", "--output-format", "json"],
            input=prompt, capture_output=True, text=True, encoding="utf-8",
            errors="replace", cwd=cwd, timeout=timeout,
        )
    if proc.returncode != 0:
        raise JudgeError(f"claude -p exited {proc.returncode}: {proc.stderr.strip()[:500]}")
    try:
        envelope = json.loads(proc.stdout)
        text = envelope["result"]
    except (ValueError, KeyError, TypeError):
        raise JudgeError(f"claude -p returned no result envelope: {proc.stdout[:200]!r}")
    # The judge sometimes wraps or prefixes the JSON; take the outermost object.
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError(f"judge returned no JSON object: {text[:200]!r}")
    verdict = json.loads(text[start:end + 1])
    if verdict.get("winner") not in ("1", "2", "tie"):
        raise ValueError(f"judge returned an unexpected winner: {verdict!r}")
    return verdict, envelope.get("total_cost_usd", 0.0) or 0.0


def compare(request, sides, rubric, model, tag="implementation", timeout=300):
    """Judge `sides` ({name: text}, exactly two) in both orders.

    Returns {"orders": [{"first", "second", "winner", "reasoning"}, ...],
    "verdict": one of the names, "tie" or "split", "cost_usd"}. Each order's
    winner is a side's name, so the caller never sees the judge's 1/2."""
    (name_a, text_a), (name_b, text_b) = sides.items()
    result = {"orders": [], "cost_usd": 0.0}
    for first, second in ((name_a, name_b), (name_b, name_a)):
        prompt = JUDGE_PROMPT.format(rubric=rubric, request=request, tag=tag,
                                     first=sides[first], second=sides[second])
        try:
            verdict, cost = ask_judge(prompt, model, timeout)
        except ValueError:
            # One retry: the judge occasionally emits a tool-call-shaped reply.
            verdict, cost = ask_judge(prompt, model, timeout)
        winner = {"1": first, "2": second, "tie": "tie"}[verdict["winner"]]
        result["orders"].append({"first": first, "second": second,
                                 "winner": winner, "reasoning": verdict["reasoning"]})
        result["cost_usd"] += cost
    winners = {o["winner"] for o in result["orders"]}
    result["verdict"] = winners.pop() if len(winners) == 1 else "split"
    return result


def excluded(path, entries):
    return any(validation_gate.allowed(path, e) for e in entries)


def is_lock_file(path):
    name = os.path.basename(path).lower()
    return "lock" in name


def read_text(full):
    """File content as text, or None when it is binary (not UTF-8)."""
    with open(full, "rb") as f:
        data = f.read()
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def candidate_view(project, base, baseline, exclude, max_bytes):
    """One candidate's changes rendered for the judge, with nothing that
    names the worktree: paths are the project-relative ones git reports."""
    files = [f for f in validation_gate.changed_files(project, base, baseline)
             if not excluded(f, exclude)]
    files.sort(key=lambda f: (is_lock_file(f), f))
    parts, shown, budget, cut = [], [], max_bytes, []
    for path in files:
        full = os.path.join(project, path)
        if not os.path.isfile(full):
            parts.append(f"--- {path} (deleted) ---")
            shown.append(path)
            continue
        text = read_text(full)
        if text is None:
            parts.append(f"--- {path} (binary, not shown) ---")
            shown.append(path)
            continue
        if budget <= 0:
            cut.append(path)
            continue
        if len(text) > budget:
            text = text[:budget] + f"\n[truncated: {len(text) - budget} more characters of this file not shown]"
            cut.append(path)
        budget -= len(text)
        parts.append(f"--- {path} ---\n{text}")
        shown.append(path)
    not_shown = [f for f in cut if f not in shown]
    if not_shown:
        parts.append("[truncated: these changed files are not shown: " + ", ".join(not_shown) + "]")
    if not files:
        parts.append("(no changed files)")
    return {"text": "\n\n".join(parts), "files": files, "truncated": bool(cut)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", action="append", default=[], metavar="DIR",
                   help="a candidate's worktree (exactly two)")
    p.add_argument("--base", default="HEAD", help="commit both candidates branched from")
    p.add_argument("--baseline", help="baseline file written by validation_gate.py --record-baseline (overrides --base)")
    p.add_argument("--task", action="append", default=[], metavar="FILE",
                   help="a file of the brief both candidates were given: design doc, slice, criteria (repeatable)")
    p.add_argument("--exclude", action="append", default=[], metavar="PATH",
                   help="changed path to leave out of the judge's view: dir/ or exact file (repeatable)")
    p.add_argument("--model", default="sonnet")
    p.add_argument("--max-bytes", type=int, default=200_000, help="cap on each candidate's view")
    p.add_argument("--timeout", type=float, default=300, help="seconds each judge call may take")
    p.add_argument("--out", help="where to write the verdicts with their reasoning (default: next to the baseline file)")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if len(a.candidate) != 2:
        p.error("exactly two --candidate entries are needed")
    if not a.task:
        p.error("at least one --task file is needed: the judge has to know what was asked")
    out = a.out or (os.path.join(os.path.dirname(os.path.abspath(a.baseline)), "kad-pairwise.json")
                    if a.baseline else None)
    if not out:
        p.error("--out is needed when there is no --baseline to put the verdicts next to")

    baseline, base = None, a.base
    if a.baseline:
        with open(a.baseline, encoding="utf-8") as f:
            baseline = json.load(f)
        base = baseline["base"]

    request = []
    for path in a.task:
        text = read_text(path)
        if text is None:
            sys.exit(f"--task {path} is not a text file")
        request.append(f"--- {os.path.basename(path)} ---\n{text}")
    request = "\n\n".join(request)

    views = []
    try:
        for project in a.candidate:
            project = os.path.abspath(project)
            validation_gate.git(project, "rev-parse", "--verify", "--quiet", base + "^{commit}")
            views.append(candidate_view(project, base, baseline, a.exclude, a.max_bytes))
    except SystemExit as e:  # the gate's git helper exits with its own footer
        print(str(e).replace("\nvalidation gate: FAIL", ""))
        print("pairwise judge: NO VERDICT")
        return 2

    sides = {"candidate 1": views[0]["text"], "candidate 2": views[1]["text"]}
    try:
        result = compare(request, sides, IMPLEMENTATION_RUBRIC, a.model, timeout=a.timeout)
    except (JudgeError, ValueError, subprocess.TimeoutExpired) as e:
        print(f"judge could not be run: {e}")
        print("pairwise judge: NO VERDICT")
        return 2

    record = {
        "model": a.model, "base": base, "baseline": a.baseline, "task": a.task,
        "candidates": [{"label": f"candidate {i + 1}", "project": os.path.abspath(c),
                        "files": v["files"], "truncated": v["truncated"]}
                       for i, (c, v) in enumerate(zip(a.candidate, views))],
        "orders": result["orders"], "verdict": result["verdict"],
        "cost_usd": result["cost_usd"],
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    for i, v in enumerate(views):
        print(f"candidate {i + 1}: {len(v['files'])} changed file(s)"
              + (" (view truncated)" if v["truncated"] else ""))
    for o in result["orders"]:
        print(f"\n{o['first']} shown first -> {o['winner']}\n  {o['reasoning']}")
    print(f"\nreasons kept in {out} (judge cost ${result['cost_usd']:.2f})")
    print("pairwise judge:", result["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
