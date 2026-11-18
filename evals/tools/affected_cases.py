"""List the eval cases a set of changed files can affect.

A case is affected when any changed file is something it loads:
- its own directory (`evals/<case>/...`);
- `skills/<s>/...` where `<s>` is one of the case's `tags`, or a skill the
  case's runs were seen invoking (recorded per case in
  `evals/thresholds.json` as `skills_invoked`, which catches consults such
  as `map-query` inside `architecture-design`);
- `agents/<p>/...` where the case names `kad-dev-team:<p>` (it delegates to
  that agent), or one of the case's tags is a skill `<p>` owns;
- a fixture path its `scaffold.sh` copies (with `$here`-relative variables
  expanded; the shared `library-app/scaffold.sh` and
  `bootstrap-empty/scaffold.sh` stand for the directories they copy).

Three refinements since 0.16.0 (the owner, 2026-11-16: a change that
touched one corner of a shared file sent sixty unrelated cases back
through the gate). Each narrows what a case depends on inside something
it loads, and `view()` is the one place they live, read by the affected
list and by the evidence fingerprint alike:
- **A loop state, not the loop fixture.** A case whose scaffold builds a
  state of `fixtures/library-app/code-plants/loop/` depends on what that
  state builds (its entry in `evals/loop_states.json`, written by
  `loop_states.py`), not on the fixture's files.
- **The scripts it ran.** A case listed in `evals/case_scripts.json`
  (`--record-scripts`, from every kept trace) depends on those scripts
  under `skills/*/scripts/` and the sibling files they name, whichever
  skill owns them, and on no other script.
- **The orchestrator's steps.** A case depends on `skills/orchestrator/SKILL.md`
  outside its five step sections (A to E) and on the sections of the steps
  `tools/orchestrator_steps.json` lists for it. The text is still all in
  the model's context: a miss caused by a paragraph in another step goes
  unseen until that case next runs. Accepted, knowingly.

A case whose entry in `evals/thresholds.json` differs from the base is
affected too: its evidence has to clear the bar as it now stands. Changes
elsewhere (the README, `evals/tools/`, PERSONAS.md) affect no case.

Usage: python3 -I evals/tools/affected_cases.py [--base origin/main] [file ...]
  With no files, lists what differs from --base, uncommitted and untracked
  files included.
  Prints one case name per line.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loop_states  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVALS = os.path.join(ROOT, "evals")

# The shared scaffolds copy a directory; a change inside it reaches every
# case that runs them.
SHARED_SCAFFOLDS = {
    "fixtures/library-app/scaffold.sh": "fixtures/library-app/app/",
    "fixtures/bootstrap-empty/scaffold.sh": "fixtures/bootstrap-empty/docs/",
}


def case_dirs():
    """Case directories in either format the CLI reads: `case.yaml`, or
    `prompt.md` with a `graders/` directory (the negative trigger cases)."""
    for name in sorted(os.listdir(EVALS)):
        d = os.path.join(EVALS, name)
        if name != "example" and (os.path.isfile(os.path.join(d, "case.yaml"))
                                  or os.path.isfile(os.path.join(d, "prompt.md"))):
            yield name


def case_text(case):
    d = os.path.join(EVALS, case)
    parts = []
    for f in ("case.yaml", "prompt.md"):
        if os.path.isfile(os.path.join(d, f)):
            parts.append(open(os.path.join(d, f)).read())
    g = os.path.join(d, "graders")
    if os.path.isdir(g):
        parts += [open(os.path.join(g, f)).read() for f in sorted(os.listdir(g))]
    return "\n".join(parts)


def skill_names():
    return {n for n in os.listdir(os.path.join(ROOT, "skills"))
            if os.path.isfile(os.path.join(ROOT, "skills", n, "SKILL.md"))}


def tags_of(case):
    """The skills a case tests: its `tags:`, or for a markdown case the
    skills its graders name and the skill its own name starts with."""
    text = case_text(case)
    m = re.search(r"^tags:\s*\[([^\]]*)\]", text, re.M)
    if m:
        return {t.strip() for t in m.group(1).split(",")}
    skills = skill_names()
    named = {s for s in skills if re.search(r"(?<![\w-])" + re.escape(s) + r"(?![\w-])", text)}
    named |= {s for s in skills if case.startswith(s + "-neg-")}
    return named


def agents_named(case):
    return set(re.findall(r"kad-dev-team:([a-z-]+)", case_text(case)))


def agent_skills():
    owned = {}
    agents = os.path.join(ROOT, "agents")
    for persona in os.listdir(agents):
        path = os.path.join(agents, persona, "AGENT.md")
        if not os.path.isfile(path):
            continue
        front = open(path).read().split("\n---\n", 1)[0]
        owned[persona] = set(re.findall(r"^\s*-\s*kad-dev-team:([a-z-]+)", front, re.M))
    return owned


def fixture_paths(case):
    """Fixture paths (relative to evals/) the case's scaffold copies."""
    path = os.path.join(EVALS, case, "scaffold.sh")
    if not os.path.isfile(path):
        return set()
    text = open(path).read()
    for var, value in re.findall(r'^\s*(\w+)="\$here/\.\./([^"]*)"', text, re.M):
        text = re.sub(r'^\s*' + var + r'=.*$', "", text, flags=re.M)
        text = re.sub(r"\$\{?" + var + r"\}?(?!\w)", value, text)
    text = text.replace('"$here/../', '"')
    found = set()
    for p in re.findall(r"(fixtures/[A-Za-z0-9_./-]+)", text):
        p = re.sub(r"/\.$", "/", p)
        found.add(p)
        if p in SHARED_SCAFFOLDS:
            found.add(SHARED_SCAFFOLDS[p])
    return found


STEP_STARTS = [("A", "**A. Start.**"), ("B", "**B. Plan.**"), ("C", "**C. Chunks, one at a time.**"),
               ("D", "**D. Slice review.**"), ("E", "**E. Delivery.**"), ("shared", "**Pausing and resuming.**")]
STEP_LOG_LINES = {"A": "- **A. Start:**", "B": "- **B. Plan:**", "C": "- **C. Chunk", "D": "- **D. Slice review:**",
                  "E": "- **E. Delivery:**"}
ORCHESTRATOR = "skills/orchestrator/SKILL.md"
SCRIPTS_FILE = os.path.join(EVALS, "case_scripts.json")
STEPS_FILE = os.path.join(EVALS, "tools", "orchestrator_steps.json")
LOOP_MANIFEST = "evals/loop_states.json"


def scoped(text, steps):
    """The orchestrator's skill text as a case that reaches only `steps`
    depends on it: everything outside the five step sections, those
    sections for its own steps, and its own steps' lines of the log
    format. The whole text when a section's opening line is not found
    (the skill was restructured: nothing is assumed)."""
    if any(("\n" + mark) not in text for _, mark in STEP_STARTS):
        return text
    out, current = [], "shared"
    for line in text.split("\n"):
        for step, mark in STEP_STARTS:
            if line.startswith(mark):
                current = step
        owner = current
        for step, mark in STEP_LOG_LINES.items():
            if line.startswith(mark):
                owner = step
        if owner == "shared" or owner in steps:
            out.append(line)
    return "\n".join(out)


def script_files():
    """{basename: path} of every file under a skill's `scripts/`."""
    return {os.path.basename(p): os.path.relpath(p, ROOT).replace(os.sep, "/")
            for p in glob.glob(os.path.join(ROOT, "skills", "*", "scripts", "*")) if os.path.isfile(p)}


def with_siblings(names, files):
    """`names` plus every sibling file one of them names (an import, a
    helper it runs), followed until nothing is added."""
    seen, todo = set(), [n for n in names if n in files]
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        seen.add(name)
        try:
            text = open(os.path.join(ROOT, files[name]), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        here = os.path.dirname(files[name])
        for other, path in files.items():
            if other in seen or os.path.dirname(path) != here:
                continue
            stem = re.escape(os.path.splitext(other)[0])
            # an import of the sibling, or its file name as a string (a
            # helper it runs); a mention in a docstring is neither
            if re.search(r"^\s*(?:import\s+" + stem + r"|from\s+" + stem + r"\s+import)\b", text, re.M) or \
                    re.search(r"[\"']" + re.escape(other) + r"[\"']", text):
                todo.append(other)
    return seen


def scripts_in_traces(paths):
    """The scripts under `skills/*/scripts/` named in a Bash command of the
    session or of an agent it launched, in the given trace files. By file
    name: a command reaches a script through a variable as often as by path."""
    names = sorted(script_files(), key=len, reverse=True)
    if not names:
        return set()
    pattern = re.compile(r"(?<![\w-])(" + "|".join(re.escape(n) for n in names) + r")(?![\w-])")
    found = set()
    for path in paths:
        try:
            lines = open(path, encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in lines:
            if '"tool_use"' not in line or '"Bash"' not in line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            for block in (row.get("message") or {}).get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Bash":
                    found |= set(pattern.findall(str((block.get("input") or {}).get("command", ""))))
    return found


def record_scripts(dirs):
    """Add to `evals/case_scripts.json` what every kept trace under `dirs`
    shows each case running. Nothing is ever removed by this: a script a
    case ran once is one it can run again."""
    table = json.load(open(SCRIPTS_FILE, encoding="utf-8")) if os.path.isfile(SCRIPTS_FILE) else {}
    # A script added to a case's list changes what its fingerprint covers
    # and nothing the case loads: evidence that matched before the
    # addition is re-stamped after it.
    import eval_evidence
    evidence, files, reach = eval_evidence.load(), repo_files(), Reach()
    valid = {c for c, e in evidence.items() if os.path.isdir(os.path.join(EVALS, c))
             and e.get("inputs") == eval_evidence.fingerprint(c, files, reach)}
    cases = sorted(case_dirs(), key=len, reverse=True)
    by_case = {}
    for d in dirs:
        for path in glob.glob(os.path.join(d, "*.trace.jsonl")):
            name = os.path.basename(path)
            case = next((c for c in cases if re.search(r"-" + re.escape(c) + r"-run\d+\.trace\.jsonl$", name)), None)
            if case:
                by_case.setdefault(case, []).append(path)
    for case, paths in by_case.items():
        table[case] = sorted(set(table.get(case, [])) | scripts_in_traces(paths))
    with open(SCRIPTS_FILE, "w", encoding="utf-8") as f:
        json.dump({k: table[k] for k in sorted(table)}, f, indent=1)
        f.write("\n")
    reach = Reach()
    for c in valid:
        evidence[c]["inputs"] = eval_evidence.fingerprint(c, files, reach)
    if valid:
        eval_evidence.save(evidence)
    return len(by_case), len(table)


def merge_base(base):
    return subprocess.check_output(["git", "merge-base", base, "HEAD"], cwd=ROOT, text=True).strip()


def changed_files(base):
    """Files that differ from `base`'s merge point, uncommitted and new
    files included, so a run before committing sees the work in progress."""
    tracked = subprocess.check_output(["git", "diff", "--name-only", merge_base(base)], cwd=ROOT, text=True)
    new = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True)
    return sorted({l for l in (tracked + new).splitlines() if l})


def changed_bars(base):
    """Cases whose `thresholds.json` entry differs from `base`'s merge point:
    a bar raised, recorded or removed with no file the case loads touched."""
    path = "evals/thresholds.json"
    try:
        old = json.loads(subprocess.check_output(["git", "show", f"{merge_base(base)}:{path}"],
                                                 cwd=ROOT, text=True, stderr=subprocess.DEVNULL))
    except (subprocess.CalledProcessError, ValueError):
        old = {}
    full = os.path.join(ROOT, path)
    new = json.load(open(full, encoding="utf-8")) if os.path.isfile(full) else {}
    return {c for c in set(old) | set(new) if old.get(c) != new.get(c)}


def repo_files():
    """Every file in the working tree that git would see: tracked files that
    still exist, plus untracked files that aren't ignored."""
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    new = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True)
    return sorted(f for f in set((tracked + new).splitlines())
                  if f and os.path.isfile(os.path.join(ROOT, f)))


class Reach:
    """What each case loads, so a file can be asked which cases it reaches."""

    def __init__(self, whole_files=False):
        # whole_files: the rule before 0.16.0 (every file a case loads, in
        # full), kept so evidence recorded under it can be recognised
        self.whole_files = whole_files
        thresholds_path = os.path.join(EVALS, "thresholds.json")
        self.recorded = json.load(open(thresholds_path)) if os.path.isfile(thresholds_path) else {}
        self.owned = agent_skills()
        self.deps = {}
        self.scripts = json.load(open(SCRIPTS_FILE, encoding="utf-8")) if os.path.isfile(SCRIPTS_FILE) else {}
        self.steps_table = json.load(open(STEPS_FILE, encoding="utf-8")) if os.path.isfile(STEPS_FILE) else None
        self.script_paths = script_files()
        self.keys, self.closures = {}, {}

    def key(self, case):
        if case not in self.keys:
            self.keys[case] = loop_states.key_of(case)
        return self.keys[case]

    def steps(self, case):
        """The orchestrator steps the case reaches, or None for all of the file."""
        t = self.steps_table
        if t is None:
            return None
        if case in t.get("cases", {}):
            return t["cases"][case]
        key = self.key(case)
        if key is None:
            return t.get("default")
        kind, name = key.split(":", 1)
        # a state with a step after it (`<state>+after-state:<variant>`)
        # reaches the steps its state does
        return t.get("base") if kind == "base" else t.get("states", {}).get(name.split("+", 1)[0])

    def ran(self, case):
        """The script paths the case depends on, or None when none are recorded."""
        if case not in self.scripts:
            return None
        if case not in self.closures:
            self.closures[case] = {self.script_paths[n] for n in with_siblings(self.scripts[case], self.script_paths)}
        return self.closures[case]

    def may_reach(self, case, f):
        """By path alone: whether `view` can be anything but None."""
        if self.whole_files:
            return self.reaches(case, f)
        return f == LOOP_MANIFEST or self.reaches(case, f) or \
            (re.match(r"skills/[a-z0-9-]+/scripts/", f) is not None and case in self.scripts)

    def view(self, case, f, data):
        """What of file `f` (its bytes, or None when it does not exist)
        the case depends on: None for nothing, else bytes. Two versions of
        a file reach the case differently only when their views differ."""
        if self.whole_files:
            return data if data is not None and self.reaches(case, f) else None
        if f == LOOP_MANIFEST:
            key = self.key(case)
            if key is None:
                return None
            if data is None:
                return b"no manifest"
            try:
                return str(json.loads(data).get("states", {}).get(key, "no entry")).encode()
            except ValueError:
                return b"unreadable"
        if f.startswith(loop_states.LOOP) and self.key(case) is not None:
            return None  # held by the state's entry in the manifest
        if data is None:
            return None
        if re.match(r"skills/[a-z0-9-]+/scripts/", f) and self.ran(case) is not None:
            return data if f in self.ran(case) else None
        if not self.reaches(case, f):
            return None
        if f == ORCHESTRATOR and self.steps(case) is not None:
            return scoped(data.decode("utf-8", "replace"), self.steps(case)).encode("utf-8")
        return data

    def _deps(self, case):
        if case not in self.deps:
            self.deps[case] = (tags_of(case),
                               set(self.recorded.get(case, {}).get("skills_invoked", [])),
                               agents_named(case) & set(self.owned),
                               fixture_paths(case))
        return self.deps[case]

    def reaches(self, case, f):
        tags, invoked, delegates, fixtures = self._deps(case)
        parts = f.split("/")
        if f.startswith(f"evals/{case}/known-bad/"):
            # a known-bad reference (skill_mutation.py) is read by that
            # tool, never loaded by a run of the case
            return False
        if f.startswith(f"evals/{case}/"):
            return True
        if parts[0] == "skills" and len(parts) > 2 and (parts[1] in tags or parts[1] in invoked):
            return True
        if parts[0] == "agents" and len(parts) > 2 and (
                parts[1] in delegates or self.owned.get(parts[1], set()) & tags):
            return True
        if f.startswith("evals/fixtures/"):
            rel = f[len("evals/"):]
            return any(rel == p or (p.endswith("/") and rel.startswith(p)) or rel.startswith(p + "/")
                       for p in fixtures)
        return False


_BYTES = {}


def working(f):
    """A working-tree file's bytes with CRLF folded, or None when absent."""
    if f not in _BYTES:
        path = os.path.join(ROOT, f)
        _BYTES[f] = open(path, "rb").read().replace(b"\r\n", b"\n") if os.path.isfile(path) else None
    return _BYTES[f]


def at_commit(commit, f):
    r = subprocess.run(["git", "show", f"{commit}:{f}"], cwd=ROOT, capture_output=True)
    return r.stdout.replace(b"\r\n", b"\n") if r.returncode == 0 else None


def inputs_of(case, files=None, reach=None):
    """[(file, bytes)] for what `case` depends on in the working tree (of
    `files`, default all of it): the views a change is matched against in
    `affected`, so a fingerprint of them says whether a recorded run still
    applies."""
    reach = reach or Reach()
    out = []
    for f in (files if files is not None else repo_files()):
        if reach.may_reach(case, f):
            data = reach.view(case, f, working(f))
            if data is not None:
                out.append((f, data))
    return out


def affected(files, base=None):
    reach = Reach()
    commit = merge_base(base) if base else None
    before = {f: at_commit(commit, f) for f in files} if commit else {}
    cases = set()
    for case in case_dirs():
        for f in files:
            if not reach.may_reach(case, f):
                continue
            now = reach.view(case, f, working(f))
            if (commit and now != reach.view(case, f, before[f])) or (not commit and now is not None):
                cases.add(case)
                break
    if base and "evals/thresholds.json" in files:
        cases |= changed_bars(base) & set(case_dirs())
    return sorted(cases)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="origin/main")
    p.add_argument("files", nargs="*")
    p.add_argument("--record-scripts", nargs="*", metavar="DIR",
                   help="read every kept trace under DIR (default evals/results) and add the scripts each case ran to evals/case_scripts.json")
    a = p.parse_args()
    if a.record_scripts is not None:
        read, total = record_scripts(a.record_scripts or [os.path.join(EVALS, "results")])
        print(f"traces of {read} cases read; evals/case_scripts.json lists {total}")
        return
    for case in affected(a.files or changed_files(a.base), a.base if not a.files else None):
        print(case)


if __name__ == "__main__":
    main()
