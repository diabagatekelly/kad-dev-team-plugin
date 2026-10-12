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

Changes elsewhere (the README, `evals/tools/`, PERSONAS.md) affect no case.

Usage: python3 -I evals/tools/affected_cases.py [--base origin/main] [file ...]
  With no files, lists what differs from --base, uncommitted and untracked
  files included.
  Prints one case name per line.
"""
import argparse
import json
import os
import re
import subprocess

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


def changed_files(base):
    """Files that differ from `base`'s merge point, uncommitted and new
    files included, so a run before committing sees the work in progress."""
    merge_base = subprocess.check_output(["git", "merge-base", base, "HEAD"], cwd=ROOT, text=True).strip()
    tracked = subprocess.check_output(["git", "diff", "--name-only", merge_base], cwd=ROOT, text=True)
    new = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True)
    return sorted({l for l in (tracked + new).splitlines() if l})


def affected(files):
    thresholds_path = os.path.join(EVALS, "thresholds.json")
    recorded = json.load(open(thresholds_path)) if os.path.isfile(thresholds_path) else {}
    owned = agent_skills()
    hits = set()
    for case in case_dirs():
        tags = tags_of(case)
        invoked = set(recorded.get(case, {}).get("skills_invoked", []))
        delegates = agents_named(case) & set(owned)
        fixtures = fixture_paths(case)
        for f in files:
            parts = f.split("/")
            if f.startswith(f"evals/{case}/"):
                hits.add(case)
            elif parts[0] == "skills" and len(parts) > 2 and (parts[1] in tags or parts[1] in invoked):
                hits.add(case)
            elif parts[0] == "agents" and len(parts) > 2 and (
                    parts[1] in delegates or owned.get(parts[1], set()) & tags):
                hits.add(case)
            elif f.startswith("evals/fixtures/"):
                rel = f[len("evals/"):]
                if any(rel == p or (p.endswith("/") and rel.startswith(p)) or rel.startswith(p + "/")
                       for p in fixtures):
                    hits.add(case)
    return sorted(hits)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="origin/main")
    p.add_argument("files", nargs="*")
    a = p.parse_args()
    for case in affected(a.files or changed_files(a.base)):
        print(case)


if __name__ == "__main__":
    main()
