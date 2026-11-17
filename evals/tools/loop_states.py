#!/usr/bin/env python3
"""What each loop state builds, as one hash per state.

The loop fixture (`fixtures/library-app/code-plants/loop/`) is one builder
for thirty states, and a case stands on one of them. Until 0.16.0 a case
was stale whenever any file of the fixture changed, so a new state sent
every other state's cases back through the gate. A case now depends on
what its own state builds: this tool builds each state a case's
`scaffold.sh` names (`state.sh <state>`, or `base.sh <planning set>`),
hashes the tree it leaves, and writes `evals/loop_states.json`.
`affected_cases.py` reads a case's entry from that file in place of the
fixture's files.

What is hashed: every file of the built working directory outside `.git/`
and `node_modules/`, by path and content, plus the commit subjects and
`git status`. What is taken out first,
since it differs between two builds of the same state: commit hashes
(seven or more hex characters), dates and times, the build directory's
own path, durations in test and gate output, and the names of the first
failing tests in a mutation report (the runner's order varies). A state's hash therefore
changes when what it holds changes, and for nothing else.

The file is only right while nothing a state is built from has changed
since it was written. It records one hash of all of that (`inputs`: the
loop fixture, the app, the planning sets and source plants the states
copy, every script under `skills/*/scripts/`, `skills/ci-pipeline/screens/`),
and `--check` fails when it no longer matches: run `--write` again (no
model; about five minutes: every state is built until two builds agree) and commit the file. The pull-request check
(`eval_evidence.py`) runs `--check`.

    --write        build every state and write evals/loop_states.json
    --check        the recorded `inputs` still matches the tree (exit 1 if not)
    --state KEY    print one state's normalised listing (to see what
                   differs between two builds)

Usage: python3 -I evals/tools/loop_states.py --write
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
EVALS = os.path.dirname(TOOLS)
ROOT = os.path.dirname(EVALS)
LOOP = "evals/fixtures/library-app/code-plants/loop/"
MANIFEST = os.path.join(EVALS, "loop_states.json")
# Everything a state can be built from. A change to any of it makes the
# recorded hashes unproven until they are built again.
INPUT_PREFIXES = (LOOP, "evals/fixtures/library-app/app/", "evals/fixtures/library-app/code-plants/tdd/",
                  "evals/fixtures/library-app/route-plants/", "evals/fixtures/library-app/planning/",
                  "evals/fixtures/library-app/source-plants/", "evals/fixtures/library-app/scaffold.sh",
                  "skills/ci-pipeline/screens/")
INPUT_PATTERN = re.compile(r"^skills/[a-z0-9-]+/scripts/")

sys.path.insert(0, TOOLS)


def git_bin():
    for exe in ("/opt/homebrew/bin/git", "/usr/local/bin/git", "git"):
        if shutil.which(exe):
            return exe
    return "git"


def repo_files():
    out = subprocess.check_output([git_bin(), "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, text=True)
    return sorted(f for f in set(out.splitlines()) if f and os.path.isfile(os.path.join(ROOT, f)))


def inputs_hash():
    h = hashlib.sha256()
    for f in repo_files():
        if f.startswith(INPUT_PREFIXES) or INPUT_PATTERN.match(f):
            h.update(f.encode() + b"\0")
            with open(os.path.join(ROOT, f), "rb") as fh:
                h.update(fh.read().replace(b"\r\n", b"\n") + b"\0")
    return h.hexdigest()


def key_of(case):
    """`state:<name>` or `base:<planning set>` for a case whose scaffold
    builds a loop state; None for any other case."""
    path = os.path.join(EVALS, case, "scaffold.sh")
    if not os.path.isfile(path):
        return None
    lines = [l for l in open(path, encoding="utf-8").read().splitlines() if not l.lstrip().startswith("#")]
    text = "\n".join(lines)
    for var, value in re.findall(r'^\s*(\w+)="(\$here/\.\./[^"]*)"', text, re.M):  # fx="$here/../fixtures/library-app"
        text = re.sub(r"\$\{?" + var + r"\}?(?!\w)", value, text)
    m = re.search(r"code-plants/loop/state\.sh\"?\s+([a-z0-9-]+)", text)
    if m:
        return "state:" + m.group(1)
    m = re.search(r"code-plants/loop/base\.sh\"?\s+\"?\$here/\.\./fixtures/library-app/([A-Za-z0-9_./-]+)", text)
    if m:
        return "base:" + m.group(1)
    return None


def keys_in_use():
    keys = {}
    for case in sorted(os.listdir(EVALS)):
        key = key_of(case)
        if key:
            keys.setdefault(key, []).append(case)
    return keys


NOISE = [
    # the mutation report names the first three failing tests, in the order
    # the runner happened to finish them
    (re.compile(r"(CAUGHT \(\d+ failed\)) by [^|\n]*"), r"\1 "),
    (re.compile(r"\b\d{4}-\d\d-\d\d(?:T\d\d:\d\d:\d\d(?:\.\d+)?Z?)?\b"), "<date>"),
    (re.compile(r"\b\d\d:\d\d(?::\d\d)?(?: UTC)?\b"), "<clock>"),
    # the sidecar stamps each row with the id of the session that recorded
    # it, which is the session that built the state: without this line a
    # manifest written in one session matched no build made in another
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"), "<session>"),
    (re.compile(r"\b[0-9a-f]{7,40}\b"), "<sha>"),
    (re.compile(r"\b\d+(?:\.\d+)?\s?(?:ms|s)\b"), "<time>"),
    (re.compile(r"duration_ms\s+[\d.]+"), "duration_ms <time>"),
    (re.compile(r"kad-[a-z]+-[A-Za-z0-9_.-]+"), "kad-<tmp>"),
    (re.compile(r"-\d{3,}\b"), "-<n>"),
]


def normalise(data, where):
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    for path in sorted({where, os.path.realpath(where)}, key=len, reverse=True):
        text = text.replace(path, "<cwd>")
    for tmp in sorted({tempfile.gettempdir(), os.path.realpath(tempfile.gettempdir()), os.environ.get("TMPDIR", "/tmp").rstrip("/")}, key=len, reverse=True):
        if tmp:
            text = text.replace(tmp, "<tmp>")
    for pattern, put in NOISE:
        text = pattern.sub(put, text)
    return text.replace("\r\n", "\n").encode("utf-8")


def listing(where):
    """[(path, normalised bytes)] of a built state."""
    out = []
    for base, dirs, files in os.walk(where):
        dirs[:] = sorted(d for d in dirs if d not in (".git", "node_modules"))
        for name in sorted(files):
            full = os.path.join(base, name)
            rel = os.path.relpath(full, where).replace(os.sep, "/")
            if os.path.islink(full):
                out.append((rel, b"link"))
                continue
            with open(full, "rb") as f:
                out.append((rel, normalise(f.read(), where)))
    g = git_bin()

    def git(*args):
        r = subprocess.run([g, "-C", where, *args], capture_output=True, text=True)
        return normalise(r.stdout.encode(), where)
    # sorted: commits made within one second have no stable order
    out.append(("<git log>", b"\n".join(sorted(git("log", "--all", "--format=%s").split(b"\n")))))
    out.append(("<git status>", git("status", "--porcelain")))
    return out


def build(key, root=ROOT, absent_ok=False):
    kind, name = key.split(":", 1)
    loop = os.path.join(root, LOOP)
    script = [os.path.join(loop, "state.sh"), name] if kind == "state" else \
        [os.path.join(loop, "base.sh"), os.path.join(root, "evals", "fixtures", "library-app", name)]
    where = tempfile.mkdtemp(prefix="kad-state-")
    try:
        r = subprocess.run(["bash", *script], cwd=where, capture_output=True, text=True)
        if r.returncode != 0 and absent_ok:
            return None
        if r.returncode != 0:
            raise SystemExit(f"loop_states: {key} did not build:\n{r.stdout[-800:]}\n{r.stderr[-800:]}")
        return listing(where)
    finally:
        shutil.rmtree(where, ignore_errors=True)


def settled(key, root=ROOT, absent_ok=False):
    """A state's hash once two builds in a row agree (four tries). A
    build under load has given a different tree once (a state that runs
    the mutation pass, 2026-11-16); a hash seen twice running is the
    state's own."""
    last = None
    for _ in range(4):
        now = digest(build(key, root, absent_ok))
        if now == last:
            return now
        last = now
    raise SystemExit(f"loop_states: {key} built four times and no two builds in a row agree")


def digest(items):
    if items is None:
        return "absent"
    h = hashlib.sha256()
    for path, data in items:
        h.update(path.encode() + b"\0" + data + b"\0")
    return h.hexdigest()


def load():
    if not os.path.isfile(MANIFEST):
        return None
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def check():
    """An error line, or None when the recorded hashes are current."""
    manifest = load()
    if manifest is None:
        return "evals/loop_states.json is missing: python3 -I evals/tools/loop_states.py --write"
    missing = sorted(set(keys_in_use()) - set(manifest.get("states", {})))
    if missing:
        return f"evals/loop_states.json has no entry for {', '.join(missing)}: python3 -I evals/tools/loop_states.py --write"
    if manifest.get("inputs") != inputs_hash():
        return ("evals/loop_states.json was written before the last change to something a loop state is built from "
                "(the loop fixture, the app, a planning set, a script under skills/*/scripts/): "
                "python3 -I evals/tools/loop_states.py --write, and commit it")
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    p.add_argument("--state")
    p.add_argument("--jobs", type=int, default=4)
    a = p.parse_args()
    if a.state:
        for path, data in build(a.state):
            print(f"== {path} {hashlib.sha256(data).hexdigest()[:12]}")
            if len(data) < 200000 and b"\0" not in data:
                sys.stdout.write(data.decode("utf-8", "replace"))
        return 0
    if a.write:
        keys = keys_in_use()
        before = inputs_hash()
        with concurrent.futures.ThreadPoolExecutor(a.jobs) as pool:
            hashes = dict(zip(keys, pool.map(settled, keys)))
        if inputs_hash() != before:
            raise SystemExit("loop_states: a state's inputs changed while the states were being built; run it again")
        old = (load() or {}).get("states", {})
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump({"inputs": before, "states": dict(sorted(hashes.items()))}, f, indent=1)
            f.write("\n")
        moved = sorted(k for k in hashes if old.get(k) != hashes[k])
        print(f"wrote {len(hashes)} states to evals/loop_states.json; {len(moved)} changed: {', '.join(moved) or 'none'}")
        return 0
    error = check()
    print(error or "loop states: current")
    return 1 if error else 0


if __name__ == "__main__":
    sys.exit(main())
