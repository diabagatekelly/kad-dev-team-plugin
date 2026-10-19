"""Evidence that the eval gate passed locally against exactly these inputs.

The gate costs model time, so it runs on a developer machine (WSL2 on a
Claude subscription) and not in CI. What CI checks instead is this file,
`evals/evidence.json`, committed with the change: for each case, a
fingerprint of every file the case loads (its own directory, the skills
and agents it exercises, the fixtures its scaffold copies: the same set
`affected_cases.py` matches a diff against) and the gate result that was
seen against that fingerprint. `eval_gate.py` writes an entry for every
case that passed; the check fails a pull request when a case the diff
reaches has no entry, or an entry whose fingerprint no longer matches
(something it loads changed since the run), or has no bar in
`thresholds.json` to clear, or whose score no longer clears it. Like a
coverage gate: the cost is paid once, locally, and the PR carries the
proof.

The gate fingerprints each case before its runs start and records an
entry only if the fingerprint is the same when they finish: a skill
edited during a run was not what the score tested.

The fingerprint hashes file contents with CRLF folded to LF, so a run
recorded in a Linux clone matches a Windows checkout of the same tree.

Usage: python3 -I evals/tools/eval_evidence.py [--base origin/main] [--cases a b ... | --all]
           [--tolerance 0.1]
  Exit 1 when any affected case lacks current evidence; prints what to run.
"""
import argparse
import datetime
import hashlib
import json
import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
EVALS = os.path.dirname(TOOLS)
ROOT = os.path.dirname(EVALS)
sys.path.insert(0, TOOLS)
import affected_cases  # noqa: E402

PATH = os.path.join(EVALS, "evidence.json")


def fingerprint(case, files=None, reach=None):
    """sha256 over the path and CRLF-normalised content of every file the
    case loads, in path order."""
    h = hashlib.sha256()
    for f in affected_cases.inputs_of(case, files, reach):
        data = open(os.path.join(ROOT, f), "rb").read().replace(b"\r\n", b"\n")
        h.update(f.encode() + b"\0" + str(len(data)).encode() + b"\0")
        h.update(data)
    return h.hexdigest()


def load():
    return json.load(open(PATH, encoding="utf-8")) if os.path.isfile(PATH) else {}


def save(table):
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump({k: table[k] for k in sorted(table)}, f, indent=2)
        f.write("\n")


def record(passed, failed, version=None, before=None):
    """`passed`: case -> row from the gate (score, runs, bar, source).
    `failed`: cases whose old evidence no longer holds. `before`: case ->
    fingerprint taken before the runs; a case whose inputs moved since gets
    no entry. Returns the cases dropped for that."""
    table = load()
    files = affected_cases.repo_files()
    reach = affected_cases.Reach()
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    moved = []
    for case, row in passed.items():
        inputs = fingerprint(case, files, reach)
        if before and before.get(case) not in (None, inputs):
            moved.append(case)
            table.pop(case, None)
            continue
        table[case] = {
            "inputs": inputs,
            "score": None if row["score"] is None else round(row["score"], 3),
            "bar": row["bar"],
            "runs": row["runs"],
            "source": row.get("source"),
            "claude_version": version,
            "recorded": now,
        }
    for case in failed:
        table.pop(case, None)
    save(table)
    return moved


def tolerance_for(bar_entry, runs, tolerance):
    """The tolerance one case's score is judged with: the flat `--tolerance`,
    or the width of one grader flip in one run when that is wider. A score
    is the mean over runs of the share of graders passed, so with G scored
    graders over R runs one judge flip moves it by 1/(G*R): 0.111 for three
    graders at three runs, over a flat 0.1, which failed a case recorded
    from one three-run sample as often as not. The floor absorbs exactly
    one flip; two still fail. R is the larger of the runs behind the score
    and the runs the bar was recorded at, so a one-run first pass with a
    flipped grader is still suspect and re-run at the case's own count.
    Bars recorded before per-grader rates existed keep the flat tolerance."""
    graders = len(bar_entry.get("graders") or {})
    runs = max(runs or 0, bar_entry.get("runs") or 0)
    if graders and runs:
        return max(tolerance, 1.0 / (graders * runs))
    return tolerance


def check(cases, tolerance):
    """For each case: (verdict, detail). Verdict is 'ok' or a reason."""
    table = load()
    bars = json.load(open(os.path.join(EVALS, "thresholds.json")))
    files = affected_cases.repo_files()
    reach = affected_cases.Reach()
    out = {}
    for case in cases:
        e = table.get(case)
        bar = bars.get(case, {}).get("score")
        if not e:
            out[case] = ("no evidence", "never passed the gate, or its last run failed")
        elif e["inputs"] != fingerprint(case, files, reach):
            out[case] = ("stale", "a file it loads changed since " + str(e.get("recorded", "?"))[:10])
        elif bar is None:
            out[case] = ("no bar", "no entry in thresholds.json; record one with record_thresholds.py")
        elif e["score"] is None or e["score"] < bar - tolerance_for(bars.get(case, {}), e.get("runs"), tolerance):
            out[case] = ("below bar", f"evidence {e['score']} against a bar of {bar}")
        else:
            out[case] = ("ok", f"{e['score']} on {str(e.get('recorded', '?'))[:10]}")
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="origin/main")
    p.add_argument("--cases", nargs="*")
    p.add_argument("--all", action="store_true")
    p.add_argument("--tolerance", type=float, default=0.1)
    a = p.parse_args()
    if a.all:
        cases = list(affected_cases.case_dirs())
    else:
        cases = a.cases or affected_cases.affected(affected_cases.changed_files(a.base), a.base)
    if not cases:
        print("No eval case is affected by this change; no evidence needed.")
        return 0
    results = check(cases, a.tolerance)
    missing = sorted(c for c, (v, _) in results.items() if v != "ok")
    lines = ["| Case | Evidence | Detail |", "|---|---|---|"]
    for case in sorted(results):
        v, d = results[case]
        lines.append(f"| `{case}` | {'ok' if v == 'ok' else '**' + v + '**'} | {d} |")
    head = (f"**Eval evidence: {'FAIL' if missing else 'PASS'}** — {len(cases) - len(missing)}/{len(cases)} "
            f"affected cases have a passing gate run recorded against their current inputs.")
    report = head + "\n\n" + "\n".join(lines) + "\n"
    if missing:
        report += ("\nRun the gate for them and commit `evals/evidence.json` with the change:\n\n"
                   "    wsl -d Ubuntu-22.04 -- bash evals/tools/wsl-gate.sh --cases " + " ".join(missing) + "\n\n"
                   "(from the Windows checkout; inside Linux, `python3 -I evals/tools/eval_gate.py --cases ...`)\n")
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        open(summary, "a").write(report)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
