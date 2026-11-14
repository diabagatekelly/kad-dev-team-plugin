#!/usr/bin/env python3
"""The eval cases sorted: what grades each, what it costs, what it has caught (TODO.md, E4).

Per case, with no model time:

- its graders by kind, read from the case's own files: judges (`type:
  llm`) and tool checks (`regex`, `tool_used`, `tool_order`,
  `file_exists`);
- what one run costs and how long it takes, the agent's own run and the
  judges apart, from the results history;
- whether it has failed since its bar was recorded (E1, the counts of
  `case_history.py`);
- whether a rule deletion failed it (E2: the deletions of
  `tools/mutants/*.json` that were run on it, and the ones kept beside it
  as `known-bad/*.json`);
- and two columns that take reading and are not computed: for each judge,
  whether a tool could decide it, and whether the prompt states the rule
  the case grades. Those are in `tools/case_reading.json`, written by
  whoever read the case, and merged in here; correct a row there and run
  this again.

Cost and time. A run's `costUsd` in a result already includes its
`judgeCostUsd` (the agent's own total in the run's trace plus the judge
cost equals it), so the agent's share is the difference. A result holds
one judge cost per run, not one per judge: a judge's share is that cost
split evenly over the case's judges, an estimate. `durationSeconds` is
the whole run; the agent's own time is in the run's trace (`duration_ms`
on its `result` line) and the judges' time is the rest, so the split is
given only over the runs whose trace is still on disk, and not for a run
that launched agents (its result's time leaves theirs out). Figures are the mean
over the completed runs since `--since`; a case with no run since then
has the mean of every completed run held and is marked `*`. List prices,
as the CLI records them; not a bill.

The reading file, `tools/case_reading.json`: one entry per case,

    "<case>": {
      "prompt": {"states_rule": "yes" | "partly" | "no",
                 "quote": "<the prompt's words, when yes or partly>",
                 "note": "<what the words give away, or why not>"},
      "judges": {"<grader name>": {"by": "tool" | "reading", "why": "<one short reason>"}},
      "findings": ["<a grader that looks wrong, described; never fixed here>"]
    }

`--check` fails when a case has no entry, an entry names a case that is
gone, or an entry's judges are not exactly the case's `llm` graders: a
judge added to a case has to be read before the table is current.

Usage:
  python3 -I evals/tools/case_sort.py [--results DIR ...] [--since YYYY-MM-DD]
      [--reading FILE] [--costly USD] [--readme FILE] [--check]

  --results DIR   a directory of results (repeatable). Default: evals/results
                  and, when it exists, ~/kad-eval-results-archive.
  --since DATE    cost and time are taken over the runs from this day on
                  (default 2026-11-10, the day the baseline counts from).
  --costly USD    a never-failed case is listed as costly at or above this
                  cost per run (default 0.40).
  --readme FILE   replace the text between the two `case-sort` marker
                  comments in FILE with the report, instead of printing it.
  --check         only compare the reading file with the cases; no results read.
A result file that cannot be read (malformed, or being rewritten by a gate
run) is counted, and the report's first line says it is incomplete.
Exit codes: 0 written, printed or in step; 1 the reading file is out of
step with the cases, or the markers are not in the README.
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case_history  # noqa: E402

EVALS = os.path.dirname(HERE)
ROOT = os.path.dirname(EVALS)
READING = os.path.join(HERE, "case_reading.json")
START, END = "<!-- case-sort:start -->", "<!-- case-sort:end -->"
TOOL_KINDS = ("regex", "tool_used", "tool_order", "file_exists")
SHORT = {"regex": "regex", "tool_used": "tool call", "tool_order": "tool order", "file_exists": "file"}


def graders_of(case_dir):
    """[(name, type)] for a case in either format: the `graders:` list of
    `case.yaml`, read as text (the tools carry no YAML parser), or one
    markdown file per grader under `graders/` with the type in its front
    matter and the file's name as the grader's."""
    found = []
    path = os.path.join(case_dir, "case.yaml")
    if os.path.isfile(path):
        lines = read_text(path).split("\n")
        try:
            at = next(i for i, l in enumerate(lines) if re.match(r"graders:\s*$", l))
        except StopIteration:
            return found
        item, indent = None, None
        for line in lines[at + 1:]:
            if re.match(r"\S", line) and not line.startswith("#") and not line.startswith("-"):
                break  # the next top-level key
            m = re.match(r"(\s*)-\s+(\w+):\s*(.*)$", line)
            if m and (indent is None or len(m.group(1)) == indent):
                indent = len(m.group(1))
                item = {m.group(2): m.group(3)}
                found.append(item)
                continue
            m = re.match(r"(\s+)(\w+):\s*(.*)$", line)
            if m and item is not None and len(m.group(1)) == indent + 2:
                item.setdefault(m.group(2), m.group(3))
        return [(unquote(g.get("name", "?")), unquote(g.get("type", "?"))) for g in found]
    gdir = os.path.join(case_dir, "graders")
    if os.path.isdir(gdir):
        for f in sorted(os.listdir(gdir)):
            if not f.endswith(".md"):
                continue
            front = read_text(os.path.join(gdir, f)).split("\n---", 1)[0]
            m = re.search(r"^type:\s*(\S+)", front, re.M)
            n = re.search(r"^name:\s*(\S+)", front, re.M)
            found.append((unquote(n.group(1)) if n else f[:-3], unquote(m.group(1)) if m else "?"))
    return found


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def unquote(text):
    return text.strip().strip("'\"")


def skill_of(case, skills):
    """The skill a case is filed under: the longest skill name its own name
    starts with, else the first of its tags that is a skill, else none."""
    named = [s for s in skills if case == s or case.startswith(s + "-")]
    if named:
        return max(named, key=len)
    path = os.path.join(EVALS, case, "case.yaml")
    if os.path.isfile(path):
        m = re.search(r"^tags:\s*\[([^\]]*)\]", read_text(path), re.M)
        for tag in (t.strip() for t in m.group(1).split(",")) if m else ():
            if tag in skills:
                return tag
    return "(none)"


def skill_names(root=ROOT):
    d = os.path.join(root, "skills")
    return {n for n in os.listdir(d) if os.path.isfile(os.path.join(d, n, "SKILL.md"))} if os.path.isdir(d) else set()


def trace_seconds(path):
    """The agent's own seconds from a run's trace: `duration_ms` of its one
    `result` line. None when the trace is gone, or when the run launched
    agents (a `task_*` line, or more than one result): a result's time
    then leaves out the launched agents' and is not the run's."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = [l for l in f if '"duration_ms"' in l or '"task_' in l]
    except OSError:
        return None
    results = []
    for line in lines:
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if str(obj.get("subtype") or "").startswith("task_"):
            return None
        if obj.get("type") == "result" and isinstance(obj.get("duration_ms"), (int, float)):
            results.append(obj["duration_ms"])
    return results[0] / 1000.0 if len(results) == 1 else None


def read_costs(dirs):
    """({case: [run]}, files unreadable) for every plugin-arm run that holds
    grader results, once: a run being {at, agent, judge, seconds, trace}. A
    run the gate marked errored because a grader threw was still paid for
    and still counts, as it does in `case_history`; a run with no grader
    result (the usage limit, an interruption) does not."""
    runs = collections.defaultdict(dict)
    unreadable = 0
    for path in case_history.result_files(dirs):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            unreadable += 1
            continue
        for case in data.get("cases") or []:
            for i, run in enumerate((case.get("arms") or {}).get("with") or []):
                key = (run.get("startedAt") or os.path.basename(str(run.get("tracePath") or path)), i)
                if key in runs[case.get("name")] or not run.get("graders"):
                    continue
                total, judge = run.get("costUsd") or 0.0, run.get("judgeCostUsd") or 0.0
                runs[case.get("name")][key] = {
                    "at": case_history.parse_time(run.get("startedAt")),
                    "agent": max(total - judge, 0.0),
                    "judge": judge,
                    "seconds": run.get("durationSeconds"),
                    "trace": run.get("tracePath"),
                }
    return {k: list(v.values()) for k, v in runs.items()}, unreadable


def cost_row(runs, since):
    """The means for one case: over the runs since `since`, else over all
    held (`old` True), else None."""
    recent = [r for r in runs if r["at"] and r["at"] >= since]
    used = recent or runs
    if not used:
        return None
    mean = lambda xs: sum(xs) / len(xs) if xs else None
    split = []
    for r in used:
        agent = trace_seconds(r["trace"]) if r["trace"] else None
        if agent is not None and r["seconds"] is not None:
            split.append((agent, max(r["seconds"] - agent, 0.0)))
    return {
        "runs": len(used),
        "old": not recent,
        "agent": mean([r["agent"] for r in used]),
        "judge": mean([r["judge"] for r in used]),
        "seconds": mean([r["seconds"] for r in used if r["seconds"] is not None]),
        "agent_seconds": mean([a for a, _ in split]),
        "judge_seconds": mean([j for _, j in split]),
    }


def deletions(evals=EVALS):
    """{case: (run, [(rule file, [graders that failed])])} from the deletion
    lists of `tools/mutants/` and the known-bad files beside the cases;
    and the set of skills that have had a pass."""
    run = collections.Counter()
    passed = set()
    for path in sorted(glob.glob(os.path.join(evals, "tools", "mutants", "*.json"))):
        try:
            mutants = json.loads(read_text(path))
        except (OSError, ValueError):
            continue
        for m in mutants:
            passed.add(m.get("skill"))
            for case in m.get("cases") or []:
                run[case] += 1
    caught = collections.defaultdict(list)
    for path in sorted(glob.glob(os.path.join(evals, "*", "known-bad", "*.json"))):
        try:
            ref = json.loads(read_text(path))
        except (OSError, ValueError):
            continue
        case = os.path.basename(os.path.dirname(os.path.dirname(path)))
        caught[case].append((os.path.basename(path)[:-5], ref.get("fails") or []))
    return run, caught, passed


def load_reading(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        return {}


def out_of_step(reading, cases):
    """What the reading file and the cases disagree on, as lines; [] when in step.
    `cases` is {case: [(grader, type)]}."""
    said = []
    for case in sorted(set(reading) - set(cases)):
        said.append(f"{case}: in the reading file, no such case")
    for case, graders in sorted(cases.items()):
        entry = reading.get(case)
        if entry is None:
            said.append(f"{case}: not read (no entry)")
            continue
        states = (entry.get("prompt") or {}).get("states_rule")
        if states not in ("yes", "partly", "no"):
            said.append(f"{case}: prompt.states_rule must be yes, partly or no")
        elif states != "no" and not (entry.get("prompt") or {}).get("quote"):
            said.append(f"{case}: prompt.states_rule is {states} with no quote")
        judges = {n for n, t in graders if t == "llm"}
        read = entry.get("judges") or {}
        for name in sorted(judges - set(read)):
            said.append(f"{case}: judge {name} not read")
        for name in sorted(set(read) - judges):
            said.append(f"{case}: {name} is not a judge of the case")
        for name, verdict in sorted(read.items()):
            if verdict.get("by") not in ("tool", "reading") or not verdict.get("why"):
                said.append(f"{case}: judge {name} needs by (tool or reading) and why")
    return said


def money(x):
    return "" if x is None else f"{x:.2f}"


def cell(text):
    """Text safe inside a table cell."""
    return str(text).replace("|", "\\|").replace("\n", " ")


def report(cases, reading, costs, history, firsts, dels, since, costly, few, dirs, unreadable=0):
    skills = skill_names()
    run_on, caught, passed = dels
    rows = []
    for case, graders in cases.items():
        kinds = collections.Counter(t for _, t in graders)
        judges = [n for n, t in graders if t == "llm"]
        entry = reading.get(case) or {}
        verdicts = entry.get("judges") or {}
        by_tool = [n for n in judges if (verdicts.get(n) or {}).get("by") == "tool"]
        hist = case_history.summarise(history.get(case, []), firsts.get(case))
        since_bar = firsts.get(case)
        counted = [r for r in history.get(case, []) if not r["errored"]
                   and (since_bar is None or r["at"] is None or r["at"] >= since_bar)]
        failed = [r for r in counted if r["failed"]]
        rows.append({
            "runs": len(counted), "failed_runs": len(failed),
            "judge_only": sum(1 for r in failed if all(judge for _, judge in r["failed"])),
            "tool_judge_only": sum(1 for r in failed if {n for n, _ in r["failed"]} <= set(by_tool)),
            "case": case, "skill": skill_of(case, skills), "kinds": kinds, "judges": judges, "by_tool": by_tool,
            "entry": entry, "cost": cost_row(costs.get(case, []), since), "hist": hist,
            "never": hist["failed"] == 0 and hist["counted"] >= few,
        })
    out = [
        f"Written by `tools/case_sort.py` on {dt.date.today():%Y-%m-%d} from the cases, `tools/case_reading.json`"
        f" and the results under {', '.join('`' + os.path.basename(os.path.normpath(d)) + '/`' for d in dirs)};"
        f" cost and time are means over the completed runs since {since:%Y-%m-%d} (`*`: no run since, every held run)."
        + (f" **Incomplete: {unreadable} result files could not be read**, so runs may be missing from the costs"
           " and the failure counts." if unreadable else ""),
        "",
        "| Case | Skill | Tool checks | Judges | A tool could decide | Prompt states the rule | Agent $ | Judges $ | Seconds (agent + judges) | Failed since the bar | Deletions that failed it |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        tools = ", ".join(f"{r['kinds'][k]} {SHORT[k]}" for k in TOOL_KINDS if r["kinds"][k]) or "0"
        other = [k for k in r["kinds"] if k not in TOOL_KINDS and k != "llm"]
        if other:
            tools += ", " + ", ".join(f"{r['kinds'][k]} {k}" for k in other)
        prompt = r["entry"].get("prompt") or {}
        states = prompt.get("states_rule", "not read")
        if states in ("yes", "partly") and prompt.get("quote"):
            states += f": \"{cell(prompt['quote'])}\""
        c = r["cost"]
        if c is None:
            agent = judge = secs = ""
        else:
            mark = "*" if c["old"] else ""
            agent, judge = money(c["agent"]) + mark, money(c["judge"])
            secs = "" if c["seconds"] is None else f"{c['seconds']:.0f}"
            if c["agent_seconds"] is not None:
                secs += f" ({c['agent_seconds']:.0f} + {c['judge_seconds']:.0f})"
        h = r["hist"]
        failed = f"{h['failed']} of {h['counted']}" + (" (few runs)" if h["counted"] < few else "")
        if r["case"] in run_on or r["case"] in caught:
            n = len(caught.get(r["case"], []))
            deleted = f"{n} of {run_on[r['case']]}" if run_on[r["case"]] else f"{n} kept"
            if n:
                deleted += ": " + ", ".join(f"`{rule}`" for rule, _ in caught[r["case"]])
        else:
            deleted = "none run" if r["skill"] in passed else "no pass on the skill"
        decided = f"{len(r['by_tool'])} of {len(r['judges'])}" if r["judges"] else ""
        if r["judges"] and not r["entry"]:
            decided = "not read"
        out.append(
            f"| `{r['case']}` | {r['skill']} | {tools} | {len(r['judges'])} | {decided} | {states}"
            f" | {agent} | {judge} | {secs} | {failed} | {deleted} |"
        )

    # Counts
    priced = [r for r in rows if r["cost"]]
    agent_total = sum(r["cost"]["agent"] for r in priced)
    judge_total = sum(r["cost"]["judge"] for r in priced)
    recent = [r for r in priced if not r["cost"]["old"]]
    judges_all = sum(len(r["judges"]) for r in rows)
    tool_all = sum(len(r["by_tool"]) for r in rows)
    share = lambda r: (r["cost"]["judge"] / len(r["judges"])) if r["cost"] and r["judges"] else 0.0
    saving = sum(share(r) * len(r["by_tool"]) for r in rows)
    states = collections.Counter((r["entry"].get("prompt") or {}).get("states_rule", "not read") for r in rows)
    no_judge = [r for r in rows if not r["judges"]]
    all_tool = [r for r in rows if r["judges"] and len(r["by_tool"]) == len(r["judges"])]
    never_costly = [r for r in rows if r["never"] and r["cost"] and r["cost"]["agent"] + r["cost"]["judge"] >= costly]
    never = [r for r in rows if r["never"]]
    names = lambda rs: ", ".join(f"`{r['case']}`" for r in rs) if rs else "none"
    total = lambda rs: sum(r["cost"]["agent"] + r["cost"]["judge"] for r in rs if r["cost"])
    out += [
        "",
        f"**One run of every case:** ${agent_total + judge_total:.2f} over the {len(priced)} cases with a completed run held"
        f" (agent ${agent_total:.2f}, judges ${judge_total:.2f}, "
        f"{100 * judge_total / (agent_total + judge_total) if priced else 0:.0f}% judges);"
        f" ${total(recent):.2f} over the {len(recent)} with a run since {since:%Y-%m-%d}."
        f" {len(rows) - len(priced)} cases have no completed run held and are not priced.",
        "",
        f"**Graders:** {judges_all} judges and {sum(sum(r['kinds'][k] for k in r['kinds'] if k != 'llm') for r in rows)}"
        f" tool checks over {len(rows)} cases; {len(no_judge)} cases have no judge.",
        "",
        f"**Judges a tool could decide:** {tool_all} of {judges_all}, in {sum(1 for r in rows if r['by_tool'])} cases;"
        f" {len(all_tool)} cases would be left with no judge. Their share of the judge cost, split evenly"
        f" within each case (an estimate): ${saving:.2f} per run of every case.",
        "",
        f"**Runs that failed only on a judge:** of {sum(r['runs'] for r in rows)} completed runs since the bars,"
        f" {sum(r['failed_runs'] for r in rows)} failed; {sum(r['judge_only'] for r in rows)} of those failed on judges"
        f" alone, and {sum(r['tool_judge_only'] for r in rows)} on judges a tool could decide alone"
        f" (${sum(r['tool_judge_only'] * (r['cost']['agent'] + r['cost']['judge']) for r in rows if r['cost']):.2f}"
        f" of runs at today's cost per run): "
        + (", ".join(f"`{r['case']}` {r['tool_judge_only']}" for r in sorted(rows, key=lambda r: -r["tool_judge_only"])
                     if r["tool_judge_only"]) or "none") + ".",
        "",
        f"**Prompt states the rule it grades:** yes {states['yes']}, partly {states['partly']}, no {states['no']}"
        + (f", not read {states['not read']}" if states["not read"] else "") + ".",
        "",
        f"**Never failed since the bar ({few} or more runs):** {len(never)} cases, ${total(never):.2f} of one run of every case."
        f" **Never failed and ${costly:.2f} or more a run ({len(never_costly)}, ${total(never_costly):.2f}):** "
        + (", ".join(f"`{r['case']}` ${r['cost']['agent'] + r['cost']['judge']:.2f}" for r in sorted(
            never_costly, key=lambda r: -(r["cost"]["agent"] + r["cost"]["judge"]))) or "none") + ".",
        "",
        "By skill (one run of each of its cases; the judges a tool could decide and their estimated share):",
        "",
        "| Skill | Cases (priced) | Agent $ | Judges $ | Judges | A tool could decide | Their share $ | Prompts stating the rule (yes, partly) | Never failed |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    by_skill = collections.defaultdict(list)
    for r in rows:
        by_skill[r["skill"]].append(r)
    for skill, rs in sorted(by_skill.items(), key=lambda kv: -total(kv[1])):
        st = collections.Counter((r["entry"].get("prompt") or {}).get("states_rule") for r in rs)
        priced_here = [r for r in rs if r["cost"]]
        agent_here = f"{sum(r['cost']['agent'] for r in priced_here):.2f}" if priced_here else ""
        judge_here = f"{sum(r['cost']['judge'] for r in priced_here):.2f}" if priced_here else ""
        out.append(
            f"| {skill} | {len(rs)} ({len(priced_here)}) | {agent_here}"
            f" | {judge_here} | {sum(len(r['judges']) for r in rs)}"
            f" | {sum(len(r['by_tool']) for r in rs)} | {sum(share(r) * len(r['by_tool']) for r in rs):.2f}"
            f" | {st['yes']}, {st['partly']} | {sum(1 for r in rs if r['never'])} |"
        )

    out += ["", "**Judges a tool could decide, with the reason** (the judges that take reading have theirs in"
            " `tools/case_reading.json`):", "", "| Case | Judge | What a tool would read | Share of a run $ |", "|---|---|---|---|"]
    for r in rows:
        for name in r["by_tool"]:
            out.append(f"| `{r['case']}` | `{name}` | {cell(r['entry']['judges'][name]['why'])} | {share(r):.3f} |")

    out += ["", "**Prompts that state the rule they grade:**", "", "| Case | The prompt's words | What they give away |", "|---|---|---|"]
    for r in rows:
        p = r["entry"].get("prompt") or {}
        if p.get("states_rule") in ("yes", "partly"):
            out.append(f"| `{r['case']}` | {p['states_rule']}: \"{cell(p.get('quote', ''))}\" | {cell(p.get('note', ''))} |")

    out += ["", "**Grader findings** (described, none fixed):", ""]
    any_finding = False
    for r in rows:
        for finding in r["entry"].get("findings") or []:
            any_finding = True
            out.append(f"- `{r['case']}`: {finding}")
    if not any_finding:
        out.append("- none")
    return "\n".join(out) + "\n"


def write_readme(path, text):
    with open(path, encoding="utf-8") as f:
        body = f.read()
    if body.count(START) != 1 or body.count(END) != 1 or body.index(START) > body.index(END):
        return False
    head, rest = body.split(START, 1)
    tail = rest.split(END, 1)[1]
    scratch = f"{path}.case-sort.tmp"
    with open(scratch, "w", encoding="utf-8") as f:
        f.write(f"{head}{START}\n{text}{END}{tail}")
    os.replace(scratch, path)  # never a half-written README
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--results", action="append", metavar="DIR")
    ap.add_argument("--since", default="2026-11-10")
    ap.add_argument("--reading", default=READING)
    ap.add_argument("--thresholds", default=os.path.join(EVALS, "thresholds.json"))
    ap.add_argument("--costly", type=float, default=0.40)
    ap.add_argument("--few", type=int, default=6)
    ap.add_argument("--readme", metavar="FILE")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    cases = {c: graders_of(os.path.join(EVALS, c)) for c in case_history.case_dirs()}
    reading = load_reading(args.reading)
    said = out_of_step(reading, cases)
    if args.check:
        for line in said:
            print(line, file=sys.stderr)
        print(f"{len(cases)} cases, {len(reading)} read: " + ("in step" if not said else f"{len(said)} out of step"))
        return 1 if said else 0
    since = dt.datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc)
    dirs = args.results or [d for d in (os.path.join(EVALS, "results"), case_history.ARCHIVE) if os.path.isdir(d)]
    history, _, unread_history = case_history.read_runs(dirs)
    costs, unread_costs = read_costs(dirs)
    unreadable = max(unread_history, unread_costs)
    text = report(cases, reading, costs, history, case_history.first_bars(args.thresholds, dirs),
                  deletions(), since, args.costly, args.few, dirs, unreadable)
    if unreadable:
        print(f"{unreadable} result files could not be read: the report is incomplete", file=sys.stderr)
    if said:
        text += f"\n{len(said)} rows of the reading file are out of step with the cases (`--check` lists them).\n"
    if not args.readme:
        sys.stdout.write(text)
        return 1 if said else 0
    if not write_readme(args.readme, text):
        print(f"{args.readme}: the markers {START} and {END} must each appear once, in that order", file=sys.stderr)
        return 1
    print(f"{args.readme}: case sort written" + (f"; {len(said)} out of step" if said else ""))
    return 1 if said else 0


if __name__ == "__main__":
    sys.exit(main())
