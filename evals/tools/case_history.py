#!/usr/bin/env python3
"""Which eval cases have ever failed, from the results history (TODO.md, E1).

Reads every result the gate left behind and prints, per case: the runs
held, the runs since the case's bar was first recorded, how many of those
failed, which graders failed, and what was lost to errors. No model time.

Where the history is. `eval_gate.py` writes one flat
`gate-<stamp>-<case>.json` per case into `evals/results/`, and `claude
plugin eval` leaves a directory per run with the same result as
`aggregate-result.json`; the directories older than a review are moved to
an archive (`evals/README.md`, "Eval gate"). Both are read, from every
`--results` directory, and a run present in both is counted once (by case
and start time). Only the plugin arm is counted.

What counts as what:

- **errored**: a run with an `error` and no grader results (the usage
  limit, a revoked sign-in, an interruption). It says nothing about the
  case.
- **thrown**: a grader that threw for a reason outside the run: the judge
  call hit the usage limit or was aborted, or the grader's own pattern
  does not compile. Counted apart, never as a failure. A run whose only
  non-passes are thrown graders did not fail.
- **failed**: a completed run in which a scored grader did not pass. A
  grader that threw because the file it reads does not exist is a
  failure of that grader (`file not written`): the run did not produce
  what the case asks for.

"Since its bar was recorded" starts at the run the case's first bar was
taken from: the `source` of the case's first entry in the history of
`evals/thresholds.json` (read with `git log`), or that commit's date when
the entry names no source. Runs before it are the case being written. A
case whose first bar is older than the oldest result held has every held
run counted. Without git, or for a case with no bar, every run counts and
the column says `none`.

Usage:
  python3 -I evals/tools/case_history.py [--results DIR ...] [--thresholds FILE]
      [--few N] [--readme FILE]

  --results DIR   a directory of results (repeatable). Default:
                  evals/results and, when it exists, ~/kad-eval-results-archive.
  --few N         a case with fewer than N completed runs since its bar is
                  listed as too few to say (default 6: two gate passes at
                  three runs).
  --readme FILE   replace the text between the two `case-history` marker
                  comments in FILE with the report, instead of printing it.
Exit codes: 0 written or printed; 1 no result found, or the markers are
not in the README.
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EVALS = os.path.dirname(HERE)
ROOT = os.path.dirname(EVALS)
ARCHIVE = os.path.join(os.path.expanduser("~"), "kad-eval-results-archive")
START, END = "<!-- case-history:start -->", "<!-- case-history:end -->"
STAMP = re.compile(r"gate-(\d{8}T\d{6})-")


def parse_time(text):
    """A result's `startedAt` (ISO, Z) as an aware datetime, or None."""
    try:
        return dt.datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None


def stamp_time(source):
    """The UTC time in a `gate-<YYYYMMDDTHHMMSS>-<case>.json` name, or None."""
    m = STAMP.search(source or "")
    if not m:
        return None
    return dt.datetime.strptime(m.group(1), "%Y%m%dT%H%M%S").replace(tzinfo=dt.timezone.utc)


def result_files(dirs):
    for d in dirs:
        yield from sorted(glob.glob(os.path.join(d, "gate-*.json")))
        yield from sorted(glob.glob(os.path.join(d, "*", "aggregate-result.json")))


def error_kind(text):
    """The reason a run or a judge call was lost, in a word or two."""
    t = str(text)
    if "limit" in t and "resets" in t:
        return "usage limit"
    if "authenticate" in t or "log in again" in t:
        return "sign-in"
    if "interrupted" in t or "aborted" in t:
        return "interrupted"
    if "Invalid regular expression" in t:
        return "grader pattern does not compile"
    if "more than" in t and "entries" in t:
        return "results folder over the entry limit"
    return "other"


def grader_outcome(grader):
    """'pass', 'fail', or 'thrown:<kind>' for one grader result of one run."""
    if grader.get("passed"):
        return "pass"
    why = str(grader.get("explanation") or "")
    if why.startswith("grader threw"):
        if "does not exist" in why:
            return "fail"
        return "thrown:" + error_kind(why)
    return "fail"


def read_runs(dirs):
    """Every plugin-arm run once: {case: [run]}, a run being
    {at, errored: kind|None, failed: [(grader, judge?)], thrown: [kind]}.
    Returns (runs by case, files read, files unreadable)."""
    runs = collections.defaultdict(dict)
    read = unreadable = 0
    for path in result_files(dirs):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            unreadable += 1
            continue
        read += 1
        for case in data.get("cases") or []:
            name = case.get("name")
            for i, run in enumerate((case.get("arms") or {}).get("with") or []):
                key = run.get("startedAt") or f"{path}#{i}"
                if key in runs[name]:
                    continue
                graders = [g for g in run.get("graders") or [] if g.get("scored", True)]
                rec = {"at": parse_time(run.get("startedAt")), "errored": None, "failed": [], "thrown": []}
                if not graders:
                    rec["errored"] = error_kind(run.get("error") or "no grader result")
                for g in graders:
                    outcome = grader_outcome(g)
                    if outcome == "fail":
                        judge = str(g.get("explanation") or "").startswith("judge votes")
                        rec["failed"].append((g.get("name"), judge))
                    elif outcome != "pass":
                        rec["thrown"].append(outcome.split(":", 1)[1])
                runs[name][key] = rec
    return {k: list(v.values()) for k, v in runs.items()}, read, unreadable


def first_bars(thresholds):
    """{case: (time the first bar's run started, or its commit's date)} from
    the git history of the thresholds file; {} when git cannot be asked."""
    rel = os.path.relpath(thresholds, ROOT)
    try:
        log = subprocess.run(
            ["git", "-C", ROOT, "log", "--reverse", "--format=%H %aI", "--", rel],
            capture_output=True, text=True, check=True,
        ).stdout.split("\n")
    except (OSError, subprocess.CalledProcessError):
        return {}
    firsts = {}
    for line in filter(None, log):
        sha, when = line.split(" ", 1)
        shown = subprocess.run(["git", "-C", ROOT, "show", f"{sha}:{rel}"], capture_output=True, text=True)
        try:
            bars = json.loads(shown.stdout)
        except ValueError:
            continue
        for name, bar in bars.items():
            if name in firsts:
                continue
            source = bar.get("source") if isinstance(bar, dict) else None
            firsts[name] = stamp_time(source) or parse_time(when)
    return firsts


def case_dirs():
    """Case directories in either format the CLI reads, as `affected_cases.py`
    finds them: `case.yaml`, or `prompt.md` (the negative trigger cases)."""
    return sorted(
        d for d in os.listdir(EVALS)
        if d != "example" and any(os.path.isfile(os.path.join(EVALS, d, f)) for f in ("case.yaml", "prompt.md"))
    )


def summarise(runs, since):
    """One case's row: the counts over all held runs and over those since the bar."""
    done = [r for r in runs if not r["errored"]]
    counted = [r for r in done if since is None or r["at"] is None or r["at"] >= since]
    failed = [r for r in counted if r["failed"]]
    graders = collections.Counter()
    judges = set()
    for r in failed:
        for name, judge in set(r["failed"]):
            graders[name] += 1
            if judge:
                judges.add(name)
    last = max((r["at"] for r in failed if r["at"]), default=None)
    return {
        "held": len(done),
        "errored": sum(1 for r in runs if r["errored"]),
        "thrown": sum(len(r["thrown"]) for r in runs),
        "counted": len(counted),
        "failed": len(failed),
        "graders": graders,
        "judges": judges,
        "last": last,
    }


def graders_cell(row, most=6):
    items = row["graders"].most_common()
    shown = [f"`{n}`{' (judge)' if n in row['judges'] else ''} ×{c}" for n, c in items[:most]]
    if len(items) > most:
        shown.append(f"and {len(items) - most} more")
    return ", ".join(shown)


def report(runs, firsts, few, read, unreadable, dirs):
    present = case_dirs()
    rows = {name: summarise(runs.get(name, []), firsts.get(name)) for name in present}
    every = [r for rs in runs.values() for r in rs]
    times = sorted(r["at"] for r in every if r["at"])
    lost = collections.Counter(r["errored"] for r in every if r["errored"])
    thrown = collections.Counter(k for r in every for k in r["thrown"])
    span = f"{times[0]:%Y-%m-%d} to {times[-1]:%Y-%m-%d}" if times else "no dated run"
    kinds = lambda c: ", ".join(f"{k} {n}" for k, n in c.most_common()) or "none"
    out = [
        f"Written by `tools/case_history.py` on {dt.date.today():%Y-%m-%d} from {read} result files"
        + (f" ({unreadable} unreadable)" if unreadable else "")
        + f" under {', '.join('`' + os.path.basename(os.path.normpath(d)) + '/`' for d in dirs)}:"
        f" {len(every)} plugin-arm runs, {span}. {sum(lost.values())} of them errored before any grader ran"
        f" ({kinds(lost)}); {sum(thrown.values())} grader results threw for a reason outside the run ({kinds(thrown)}).",
        "",
        "| Case | Bar since | Runs held | Since the bar | Failed | Graders that failed (runs) | Last failure | Errored, thrown |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name in present:
        row = rows[name]
        since = firsts.get(name)
        bar = since.strftime("%Y-%m-%d") if since else "none"
        last = row["last"].strftime("%Y-%m-%d") if row["last"] else ""
        out.append(
            f"| `{name}` | {bar} | {row['held']} | {row['counted']} | {row['failed']}"
            f" | {graders_cell(row)} | {last} | {row['errored']}, {row['thrown']} |"
        )
    never = [n for n in present if rows[n]["failed"] == 0 and rows[n]["counted"] >= few]
    thin = [n for n in present if rows[n]["failed"] == 0 and rows[n]["counted"] < few]
    gone = sorted(n for n in runs if n not in present)
    failed_cases = len(present) - len(never) - len(thin)
    names = lambda ns: ", ".join(f"`{n}`" for n in ns) if ns else "none"
    out += [
        "",
        f"Of {len(present)} cases, {failed_cases} have failed at least once since their bar, {len(never)} never have"
        f" over {few} or more completed runs, and {len(thin)} have fewer than {few} runs to go by.",
        "",
        f"**Never failed since the bar ({len(never)}):** {names(never)}.",
        "",
        f"**Too few runs to say ({len(thin)}, no failure in under {few} runs):** {names(thin)}.",
        "",
        f"**In the history with no case directory now ({len(gone)}, retired or renamed, not in the table):** {names(gone)}.",
    ]
    return "\n".join(out) + "\n"


def write_readme(path, text):
    with open(path, encoding="utf-8") as f:
        body = f.read()
    if body.count(START) != 1 or body.count(END) != 1 or body.index(START) > body.index(END):
        return False
    head, rest = body.split(START, 1)
    tail = rest.split(END, 1)[1]
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{head}{START}\n{text}{END}{tail}")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--results", action="append", metavar="DIR")
    ap.add_argument("--thresholds", default=os.path.join(EVALS, "thresholds.json"))
    ap.add_argument("--few", type=int, default=6)
    ap.add_argument("--readme", metavar="FILE")
    args = ap.parse_args()
    dirs = args.results or [d for d in (os.path.join(EVALS, "results"), ARCHIVE) if os.path.isdir(d)]
    runs, read, unreadable = read_runs(dirs)
    if not runs:
        print(f"no result found under: {', '.join(dirs) or 'no directory'}", file=sys.stderr)
        return 1
    text = report(runs, first_bars(args.thresholds), args.few, read, unreadable, dirs)
    if not args.readme:
        sys.stdout.write(text)
        return 0
    if not write_readme(args.readme, text):
        print(f"{args.readme}: the markers {START} and {END} must each appear once, in that order", file=sys.stderr)
        return 1
    print(f"{args.readme}: case history written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
