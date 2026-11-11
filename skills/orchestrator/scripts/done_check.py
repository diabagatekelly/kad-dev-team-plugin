"""The Definition of Done: is this slice production-grade enough to review?

Run by the orchestrator at step D of the chunk loop, before the slice
reviewers, from the app root. Every check is mechanical; each failure names
the fix and who makes it, so the orchestrator can hand the whole batch to one
fixer (or, for the README, to `docs-writer:readme`) and run the gate, then
launch the reviewers against a tree that already has the boring things no
chunk owns: a README a stranger can follow, a linter and formatter, a
typecheck, no application code hiding in strings, no comment that cites a
planning document, few comments at all, the columns the next slice needs,
no production default in the local configuration, and tests that test the
code rather than the repository's text.

The source set: `src/` under the project when it exists, otherwise every
top-level directory holding source files except tests, `node_modules`,
`dist`, `build`, `coverage`, `.git`, `.wrangler`, `docs`, `planning`,
`audit-docs`, `scripts`. Source files are `.ts .tsx .js .jsx .mjs .cjs .py`;
test files (`test/`, `tests/`, `__tests__/`, `spec/`, or `*.test.*` /
`*.spec.*` / `test_*.py`) are never in it. The runner for scripts comes
from `--test-cmd` (`corepack pnpm test` -> `corepack pnpm run <script>`,
`npm test` -> `npm run <script>`, `yarn`, `bun`; default `npm`).

The nine checks, how each decides, and the fix a failure names:

1. readme -> docs-writer:readme. `README.md` at the project root exists,
   opens with a top heading followed by a paragraph, and has a heading
   (any level, case ignored) for prerequisites (`prerequisites`,
   `requirements`, `you need`, `before you start`), running (`getting
   started`, `running`, `run it`, `clone to running`, `setup`, `install`),
   tests and checks (`tests`, `testing`, `checks`), where data and logs
   live (`data`, `logs`, `where things live`, `storage`) and what this
   slice does and does not (`what this does`, `scope`, `this slice`, `does
   not`, `limitations`, `not yet`). Lists the missing sections.
   Its "does not" list is read against the slice's acceptance criteria
   (`slice-<nnn>*.md` under `--planning`): an item there that shares three
   meaning-carrying words with a criterion (or every word of a short item)
   is the README saying the slice does not do what the criteria say it
   does, and the check fails naming the item and the criterion.
2. lint-and-format -> a tdd-coach fixer. A linter configuration exists
   (`eslint.config.*`, `.eslintrc*`, `biome.json*`, `[tool.ruff]` in
   `pyproject.toml`, `ruff.toml`, `.golangci.yml`), a formatter does too
   (`.prettierrc*`, a `prettier` key in package.json, a `formatter` key in
   `biome.json*`, `[tool.ruff.format]` or `[tool.black]`), the manifest
   has a `lint` script (or ruff is configured), and that script exits 0;
   a `format:check`/`format-check`/`prettier --check` script, when there is
   one, exits 0 too. The detail names the missing part or the failing
   command's last lines.
3. typecheck -> a tdd-coach fixer. `package.json` has a `typecheck`
   script (or a script that runs `tsc`) and it exits 0; a Python project
   with `mypy` or `pyright` in `pyproject.toml` runs that. No stack with a
   typechecker: `SKIP`, never a pass.
4. no-code-in-strings -> a tdd-coach fixer (structure by
   software-architect when the code needs a module the design lacks). In
   the source set: `<script` inside a quoted or template string, `new
   Function(`, `eval(`, and a template literal spanning five or more lines
   whose body has three or more lines ending in `;` and one statement
   shape (`function`, `const`/`let`/`var` followed by a name, `if (`,
   `addEventListener`, `document.`; CSS in a template literal has
   semicolons and `var(--x)` but none of these). Reports `path:line`.
5. no-planning-references -> a tdd-coach fixer (delete the comment or
   rewrite it as the WHY it stands for). In the source set, case ignored:
   `decision <n>`, `ADR-<n>`, the word `criterion`, `planning/`,
   `slice-<nnn>`, `design-slice`, `reliability-slice`, `security-slice`,
   `accessibility-slice`, `requirements-<nnn>`. Reports `path:line`.
6. comment-density -> a `code-review` pass on comments only (invoking
   `why-comments` on every file over the line), then the fixer. Comment
   lines (`//`, `#`, every line of a `/* */` block, every line of a Python
   docstring block) over non-blank lines across the source set, at most
   `--comment-threshold` percent (default 5). The detail prints the share
   and the files above the threshold, worst first. A line of JSX or a
   string that happens to start with `//` or `#` counts as a comment: the
   number is a prompt, not a verdict.
7. kept-for-later-slices-persisted -> software-architect:architecture-design
   when the design has no `Kept for later slices` line; a tdd-coach fixer
   when a named identifier is missing from the schema. The identifiers are
   the backticked names and the snake_case or camelCase words in that line
   or section of the design (`design-slice-<nnn>*.md` under `--planning`,
   or `--design`); each must appear, case ignored and camelCase folded to
   snake_case, in the schema sources: `migrations/**`, `**/*.sql`,
   `schema.*`, `prisma/schema.prisma`, `drizzle/**`, `models.py`,
   `alembic/**`.
8. env-defaults-not-production -> a tdd-coach fixer. In `wrangler.toml`,
   `wrangler.json*`, `.env`, `.env.example`, `.dev.vars.example`,
   `config/*.{json,toml,yaml,yml}`, `app.yaml`, `fly.toml`: a line outside
   a section whose header names production (`[env.production]`,
   `production:`) that sets a value containing `production` or `prod`
   (`PLAID_ENV = "production"`, `NODE_ENV=production`, a URL with
   `production`). Reports `path:line`; the fixer and the security reviewer
   judge whether a hit is really a production default. No such files: pass
   with a note.
9. tests-not-padding -> a tdd-coach fixer (delete or replace the tests
   named). Prints the test-to-source non-blank line ratio (information
   only, never a failure) and fails when more than `--padding-threshold`
   percent (default 10) of test files assert on the repository's text
   instead of its behaviour: a file that reads a source file or manifest
   (`readFileSync(`, `readFile(`, `open(` with `.ts`, `.tsx`, `.js`,
   `.mjs`, `.py`, `package.json` or `wrangler.toml` in the argument, an
   import of `package.json`, an `import.meta.glob(`, or an index into a
   files map by a source path) and asserts on the content (`toContain(`,
   `toMatch(`, `toBe(`, `toEqual(`, `assert.match(`, `includes(`, `in
   content`). Lists the files.

Output: one `PASS`/`FAIL`/`SKIP` line per check, each FAIL followed by a
`  fix: <who> — <what>` line, then `definition of done: PASS` or `FAIL` as
the last line. Exit 0 on PASS (SKIPs allowed), 1 on FAIL. `--json FILE`
writes the table.

Usage: python3 -I ${CLAUDE_SKILL_DIR}/scripts/done_check.py --project DIR --planning DIR --slice 001
           [--design PATH] [--test-cmd 'corepack pnpm test'] [--comment-threshold 5]
           [--padding-threshold 10] [--timeout 600] [--json out.json]
"""
import argparse
import glob
import json
import os
import re
import shlex
import shutil
import subprocess
import sys

SOURCE_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py")
TEST_DIRS = {"test", "tests", "__tests__", "spec"}
SKIP_DIRS = {"node_modules", "dist", "build", "coverage", ".git", ".wrangler", "docs", "planning", "audit-docs",
             "scripts", ".claude", ".github", "evals"} | TEST_DIRS
TEST_NAME = re.compile(r"(\.(test|spec)\.[cm]?[jt]sx?$)|(^test_.*\.py$)|(_test\.py$)")
FIXER = "a tdd-coach fixer"


def is_test_file(rel):
    parts = rel.split("/")
    return any(p in TEST_DIRS for p in parts[:-1]) or bool(TEST_NAME.search(parts[-1]))


def walk(root, skip=SKIP_DIRS):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in skip and not d.startswith("."))
        for f in sorted(filenames):
            yield os.path.join(dirpath, f)


def rel(project, path):
    return os.path.relpath(path, project).replace(os.sep, "/")


def source_files(project):
    roots = [os.path.join(project, "src")] if os.path.isdir(os.path.join(project, "src")) else [
        os.path.join(project, d) for d in sorted(os.listdir(project))
        if os.path.isdir(os.path.join(project, d)) and d not in SKIP_DIRS and not d.startswith(".")]
    out = []
    for r in roots:
        for f in walk(r):
            if f.endswith(SOURCE_EXT) and not is_test_file(rel(project, f)) and not f.endswith(".d.ts"):
                out.append(f)
    return out


def test_files(project):
    out = []
    for f in walk(project, skip=SKIP_DIRS - TEST_DIRS):
        if f.endswith(SOURCE_EXT) and is_test_file(rel(project, f)):
            out.append(f)
    return out


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def comment_counts(path):
    """(comment lines, non-blank lines) by line-start heuristics."""
    comments, nonblank, in_block, block_end = 0, 0, False, None
    python = path.endswith(".py")
    for line in read(path).splitlines():
        s = line.strip()
        if not s:
            continue
        nonblank += 1
        if in_block:
            comments += 1
            if block_end in s:
                in_block = False
            continue
        if python:
            if s.startswith("#"):
                comments += 1
            elif s.startswith(('"""', "'''")):
                comments += 1
                q = s[:3]
                if s.count(q) < 2:
                    in_block, block_end = True, q
        else:
            if s.startswith("//") or s.startswith("{/*") or s.startswith("*") and not s.startswith("*/"):
                comments += 1
            elif s.startswith("/*"):
                comments += 1
                if "*/" not in s:
                    in_block, block_end = True, "*/"
    return comments, nonblank


def runner_from(test_cmd):
    words = shlex.split(test_cmd or "npm test")
    if words[:2] == ["corepack", "pnpm"]:
        return ["corepack", "pnpm", "run"]
    if words and words[0] in ("npm", "pnpm", "yarn", "bun"):
        return [words[0], "run"]
    if words and words[0] == "corepack" and len(words) > 1:
        return ["corepack", words[1], "run"]
    return ["npm", "run"]


def run(project, argv, timeout):
    program = shutil.which(argv[0])
    if not program:
        return 127, f"{argv[0]} is not on PATH"
    try:
        # The project's own documented script, run without a shell.
        proc = subprocess.run([program, *argv[1:]], cwd=project, capture_output=True, text=True,  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
                              encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, f"timed out after {timeout:g}s"
    out = (proc.stdout + proc.stderr).strip().splitlines()
    return proc.returncode, "\n".join(out[-8:])


def manifest(project):
    try:
        return json.load(open(os.path.join(project, "package.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return None


def pyproject(project):
    return read(os.path.join(project, "pyproject.toml"))


# ---- checks ------------------------------------------------------------------

README_SECTIONS = [
    ("prerequisites", r"prerequisite|requirements|you need|before you start"),
    ("running", r"getting started|running|run it|clone to running|setup|set up|install"),
    ("tests and checks", r"\btests?\b|testing|checks"),
    ("data and logs", r"\bdata\b|\blogs?\b|where things live|storage"),
    ("what this slice does and does not", r"what this does|scope|this slice|does not|doesn't|limitations|not yet"),
]


# A bullet that opens with the not-done marker ("Not yet: a, b", "Does not:
# …", "Deferred: …"); "does not" inside a bullet is the slice's behaviour
# ("turns down a cancel for a hold the member does not have"), not the list.
NOT_DONE = re.compile(r"^(?:not yet|not in this slice|not done|not built|does not(?: yet)?|doesn't(?: yet)?|deferred|later|left for (?:a )?later slices?)\b", re.I)
SMALL_WORDS = set("""a an and are as at be been by for from has have in into is it its of on or that the then this to
   was when with will yet not does doesn its their there which who whom""".split())


def stems(text):
    """The words of a line that carry meaning, lightly stemmed, so `cancelling`
    and `cancelled` are the same word and `a`, `the`, `when` are none."""
    out = set()
    for w in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", text.lower()):
        w = w.replace("'s", "").strip("'-")
        if w in SMALL_WORDS or len(w) < 4:
            continue
        for suf in ("ling", "ing", "ies", "ied", "ed", "es", "s"):
            if w.endswith(suf) and len(w) - len(suf) >= 4:
                w = w[: -len(suf)] + ("y" if suf in ("ies", "ied") else "")
                break
        out.add(w)
    return out


def section(lines, pattern):
    """The lines under the first heading matching `pattern`, up to the next heading."""
    start = next((i for i, l in enumerate(lines) if re.match(r"^#{1,6}\s", l) and re.search(pattern, l.lower())), None)
    if start is None:
        return []
    body = []
    for l in lines[start + 1:]:
        if re.match(r"^#{1,6}\s", l):
            break
        body.append(l)
    return body


def bullets(lines):
    """Bullets with their continuation lines joined."""
    out = []
    for l in lines:
        if re.match(r"^\s*[-*+]\s+|^\s*\d+\.\s+", l):
            out.append(re.sub(r"^\s*(?:[-*+]|\d+\.)\s+", "", l).strip())
        elif out and l.strip() and not l.startswith("#"):
            out[-1] += " " + l.strip()
    return out


def stale_not_done(readme_lines, slice_text):
    """[(item, criterion)]: items the README says the slice does not do that
    one of the slice's acceptance criteria covers (three meaning-carrying
    words in common, or every word of a short item). The README's not-done
    list is written from the slice's non-goals; a criterion that moved into
    the slice after the README was written leaves the list saying the
    opposite of what the code does, and a stranger reads the README first."""
    criteria = bullets(section(slice_text.splitlines(), r"acceptance criteria"))
    if not criteria:
        return []
    found = []
    for b in bullets(section(readme_lines, README_SECTIONS[-1][1])):
        if not NOT_DONE.match(b):
            continue
        tail = b.split(":", 1)[1] if ":" in b else NOT_DONE.sub("", b, count=1)
        for item in re.split(r"[;,]\s+|\s+and\s+(?=[a-z])", tail):
            item = item.strip(" .")
            words = stems(item)
            if len(words) < 2:
                continue
            for c in criteria:
                shared = words & stems(c)
                if len(shared) >= 3 or (len(shared) >= 2 and shared == words):
                    found.append((item, c))
                    break
    return found


def check_readme(project, slice_doc=None):
    path = os.path.join(project, "README.md")
    if not os.path.isfile(path):
        return False, "no README.md at the project root", "docs-writer:readme — write the README from the manifest, the design and the slice"
    text = read(path)
    lines = text.splitlines()
    headings = [l.lstrip("#").strip().lower() for l in lines if re.match(r"^#{1,6}\s", l)]
    missing = []
    first = next((i for i, l in enumerate(lines) if l.startswith("# ")), None)
    if first is None or not any(l.strip() and not l.startswith("#") for l in lines[first + 1:first + 6]):
        missing.append("what it is (a top heading followed by a paragraph)")
    for name, pattern in README_SECTIONS:
        if not any(re.search(pattern, h) for h in headings):
            missing.append(name)
    if missing:
        return False, "README.md lacks sections: " + "; ".join(missing), "docs-writer:readme — add the missing sections"
    stale = stale_not_done(lines, read(slice_doc)) if slice_doc else []
    if stale:
        shown = "; ".join(f"\"{item}\" (criterion: {c[:70].rstrip()}…)" for item, c in stale[:3])
        return (False, f"README.md says the slice does not do what its criteria cover: {shown}",
                "docs-writer:readme — rewrite \"What this slice does and does not\" from the slice's criteria as they stand")
    return True, f"README.md has every section ({len(headings)} headings)" + ("; its not-done list names no criterion" if slice_doc else ""), None


def find_slice(planning, nnn):
    hits = [h for h in sorted(glob.glob(os.path.join(planning, f"slice-{nnn}*.md"))) if not re.search(r"-v\d+\.md$", h)]
    return hits[0] if hits else None


def check_lint(project, runner, timeout):
    pj, py = manifest(project), pyproject(project)
    linters = [f for pat in ("eslint.config.*", ".eslintrc*", "biome.json*", "ruff.toml", ".golangci.yml", ".golangci.yaml")
               for f in glob.glob(os.path.join(project, pat))]
    ruff = "[tool.ruff" in py
    if ruff:
        linters.append("pyproject.toml [tool.ruff]")
    formatters = [f for pat in (".prettierrc*", "prettier.config.*", "biome.json*") for f in glob.glob(os.path.join(project, pat))]
    if pj and "prettier" in pj:
        formatters.append("package.json prettier")
    formatters = [f for f in formatters if not os.path.basename(f).startswith("biome") or '"formatter"' in read(f)]
    if "[tool.ruff.format]" in py or "[tool.black]" in py:
        formatters.append("pyproject.toml formatter")
    problems = []
    if not linters:
        problems.append("no linter configuration")
    if not formatters:
        problems.append("no formatter configuration")
    scripts = (pj or {}).get("scripts", {}) if isinstance((pj or {}).get("scripts", {}), dict) else {}
    if "lint" in scripts:
        code, tail = run(project, runner + ["lint"], timeout)
        if code != 0:
            problems.append(f"`{' '.join(runner)} lint` exited {code}: {tail[-300:]}")
    elif ruff:
        code, tail = run(project, ["ruff", "check", "."], timeout)
        if code != 0:
            problems.append(f"`ruff check .` exited {code}: {tail[-300:]}")
    elif pj is not None:
        problems.append("no `lint` script in package.json")
    fmt_script = next((s for s in scripts if re.match(r"format[:-]?check|fmt[:-]?check|prettier[:-]?check", s)), None)
    if fmt_script:
        code, tail = run(project, runner + [fmt_script], timeout)
        if code != 0:
            problems.append(f"`{' '.join(runner)} {fmt_script}` exited {code}: {tail[-300:]}")
    if problems:
        return False, "; ".join(problems), f"{FIXER} — configure the linter and formatter for the stack, add the `lint` script, make the tree clean"
    return True, "linter and formatter configured and clean (" + ", ".join(os.path.basename(x) for x in linters + formatters) + ")", None


def check_typecheck(project, runner, timeout):
    pj, py = manifest(project), pyproject(project)
    scripts = (pj or {}).get("scripts", {}) if pj else {}
    script = "typecheck" if "typecheck" in scripts else next((s for s, c in scripts.items() if isinstance(c, str) and re.search(r"\btsc\b", c)), None)
    if script:
        code, tail = run(project, runner + [script], timeout)
        if code == 0:
            return True, f"`{' '.join(runner)} {script}` exited 0", None
        return False, f"`{' '.join(runner)} {script}` exited {code}: {tail[-400:]}", f"{FIXER} — make the typecheck pass"
    for tool in ("mypy", "pyright"):
        if tool in py:
            code, tail = run(project, [tool, "."], timeout)
            if code == 0:
                return True, f"`{tool} .` exited 0", None
            return False, f"`{tool} .` exited {code}: {tail[-400:]}", f"{FIXER} — make the typecheck pass"
    if pj is not None and any(f.endswith((".ts", ".tsx")) for f in source_files(project)):
        return False, "TypeScript sources and no `typecheck` script in package.json", f"{FIXER} — add a `typecheck` script (`tsc --noEmit`) and make it pass"
    return None, "no typechecker for this stack", None


STATEMENT = re.compile(r"\bfunction\b|\b(const|let|var)\s+[A-Za-z_$]|\bif\s*\(|addEventListener|document\.")


def check_code_in_strings(project, files):
    hits = []
    for f in files:
        r = rel(project, f)
        lines = read(f).splitlines()
        for i, line in enumerate(lines, 1):
            if re.search(r"""["'`][^"'`]*<script\b""", line) or re.search(r"\bnew Function\s*\(|\beval\s*\(", line):
                hits.append(f"{r}:{i}")
        if f.endswith(".py"):
            continue
        text = read(f)
        for m in re.finditer(r"`([^`]*)`", text, re.S):
            body = m.group(1)
            body_lines = body.splitlines()
            if len(body_lines) < 5:
                continue
            semis = sum(1 for l in body_lines if l.rstrip().endswith(";"))
            if semis >= 3 and STATEMENT.search(body):
                hits.append(f"{r}:{text.count(chr(10), 0, m.start()) + 1} (template literal, {len(body_lines)} lines)")
    hits = sorted(set(hits))
    if hits:
        return False, f"{len(hits)} place(s) hold code inside a string: " + ", ".join(hits[:20]) + (" …" if len(hits) > 20 else ""), \
            f"{FIXER} — move the code into a module the build serves (software-architect:architecture-design places it when the design names none)"
    return True, "no `<script`, `new Function`, `eval` or statement-bearing template literal in the source set", None


PLANNING_REF = re.compile(r"decision \d|ADR-\d|\bcriterion\b|planning/|slice-\d{3}|design-slice|reliability-slice|security-slice|"
                          r"accessibility-slice|requirements-\d{3}", re.I)


def check_planning_refs(project, files):
    hits = []
    for f in files:
        for i, line in enumerate(read(f).splitlines(), 1):
            if PLANNING_REF.search(line):
                hits.append(f"{rel(project, f)}:{i}")
    if hits:
        return False, f"{len(hits)} line(s) cite a planning document or decision: " + ", ".join(hits[:25]) + (" …" if len(hits) > 25 else ""), \
            f"{FIXER} — delete each comment or rewrite it as the WHY it stands for; never a decision number or a file name"
    return True, "no planning reference in the source set", None


def check_comments(project, files, threshold):
    total_c, total_n, per_file = 0, 0, []
    for f in files:
        c, n = comment_counts(f)
        total_c += c
        total_n += n
        if n:
            per_file.append((100.0 * c / n, c, n, rel(project, f)))
    share = 100.0 * total_c / total_n if total_n else 0.0
    over = sorted((x for x in per_file if x[0] > threshold), reverse=True)
    detail = f"{share:.1f}% ({total_c} comment lines / {total_n} non-blank) across {len(files)} files; threshold {threshold:g}%"
    if over:
        detail += "; over the line: " + ", ".join(f"{p} {s:.0f}% ({c}/{n})" for s, c, n, p in over[:15]) + (" …" if len(over) > 15 else "")
    if share > threshold:
        return False, detail, f"a code-review pass on comments only (why-comments on every file over the line), then {FIXER} deletes or rewrites"
    return True, detail, None


def find_design(planning, nnn, explicit):
    if explicit:
        return explicit
    for pat in (f"design-slice-{nnn}*.md", f"design-{nnn}*.md"):
        hits = [h for h in sorted(glob.glob(os.path.join(planning, pat))) if not re.search(r"-v\d+\.md$", h)]
        if hits:
            return hits[0]
    return None


def snake(name):
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name).lower()


def check_kept(project, design_path):
    if not design_path or not os.path.isfile(design_path):
        return False, "no design document found", "software-architect:architecture-design — the design is missing or unnamed"
    text = read(design_path)
    m = re.search(r"kept for (?:later|the next|future) slices?|persisted for (?:later|the next) slices?", text, re.I)
    if not m:
        return False, "the design has no 'Kept for later slices' line", "software-architect:architecture-design — name what the next slice needs persisted (identifiers, cursors, provenance)"
    lines = text[m.start():].splitlines()
    block = [lines[0]]
    for l in lines[1:]:
        if re.match(r"^#{1,6}\s", l) or (not l.strip() and len(block) > 1 and not block[-1].strip()):
            break
        block.append(l)
    section = "\n".join(block)
    names = set(re.findall(r"`([A-Za-z_][A-Za-z0-9_.]*)`", section))
    names |= {w for w in re.findall(r"\b[a-z]+_[a-z0-9_]+\b|\b[a-z]+[A-Z][A-Za-z0-9]+\b", section)}
    names = {n.split(".")[-1] for n in names if len(n) > 2}
    if not names:
        return True, "the design's 'Kept for later slices' line names no identifier to check mechanically", None
    schema = ""
    for pat in ("**/migrations/**/*", "**/*.sql", "schema.*", "prisma/schema.prisma", "drizzle/**/*", "**/models.py", "alembic/**/*"):
        for f in glob.glob(os.path.join(project, pat), recursive=True):
            if os.path.isfile(f) and "node_modules" not in f:
                schema += read(f).lower() + "\n"
    if not schema:
        return False, f"no schema source found to check {sorted(names)} against", f"{FIXER} — persist the named columns in the schema"
    missing = sorted(n for n in names if n.lower() not in schema and snake(n) not in schema)
    if missing:
        return False, f"named in 'Kept for later slices' but absent from the schema: {', '.join(missing)}", f"{FIXER} — add the missing columns and the code that fills them"
    return True, f"every identifier the design keeps for later slices is in the schema ({', '.join(sorted(names))})", None


ENV_FILES = ["wrangler.toml", "wrangler.json", "wrangler.jsonc", ".env", ".env.example", ".dev.vars.example", "app.yaml", "fly.toml"]


def check_env(project):
    files = [os.path.join(project, f) for f in ENV_FILES if os.path.isfile(os.path.join(project, f))]
    files += [f for pat in ("config/*.json", "config/*.toml", "config/*.yaml", "config/*.yml") for f in glob.glob(os.path.join(project, pat))]
    if not files:
        return True, "no environment or deployment configuration file at the root", None
    hits = []
    for f in files:
        in_prod = False
        for i, line in enumerate(read(f).splitlines(), 1):
            s = line.strip()
            if re.match(r"^\[.*\]\s*$", s) or re.match(r"^[A-Za-z_][\w-]*:\s*$", s):
                in_prod = bool(re.search(r"prod", s, re.I))
                continue
            if in_prod or s.startswith("#") or "=" not in s and ":" not in s:
                continue
            value = re.split(r"[=:]", s, 1)[1]
            if re.search(r"\bproduction\b|\bprod\b|production\.", value, re.I):
                hits.append(f"{rel(project, f)}:{i}")
    if hits:
        return False, "a default outside a production section points at production: " + ", ".join(hits), \
            f"{FIXER} — point the default at the local or sandbox environment and keep production under its own section"
    return True, f"no production default in {', '.join(os.path.basename(f) for f in files)}", None


READS_SOURCE = re.compile(r"(readFileSync|readFile|open)\s*\([^)]*(\.tsx?|\.m?js|\.py|package\.json|wrangler\.toml)|"
                          r"from\s+['\"][^'\"]*package\.json['\"]|import\.meta\.glob\(|\[['\"][^'\"]*\.(tsx?|m?js|py)['\"]\]")
ASSERTS_TEXT = re.compile(r"toContain\(|toMatch\(|assert\.match\(|\bin content\b|toMatchInlineSnapshot\(|includes\(|toBe\(|toEqual\(")


def check_padding(project, src, tests, threshold):
    src_lines = sum(1 for f in src for l in read(f).splitlines() if l.strip())
    test_lines = sum(1 for f in tests for l in read(f).splitlines() if l.strip())
    ratio = f"test/src {test_lines}/{src_lines} = {test_lines / src_lines:.2f}" if src_lines else "no source lines"
    padding = []
    for f in tests:
        t = read(f)
        if READS_SOURCE.search(t) and ASSERTS_TEXT.search(t):
            padding.append(rel(project, f))
    share = 100.0 * len(padding) / len(tests) if tests else 0.0
    detail = f"{ratio}; {len(padding)} of {len(tests)} test files assert on source text or manifests ({share:.0f}%, threshold {threshold:g}%)"
    if padding:
        detail += ": " + ", ".join(padding)
    if share > threshold:
        return False, detail, f"{FIXER} — replace tests that assert on the repository's text with tests of behaviour, or delete them"
    return True, detail, None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True)
    p.add_argument("--planning", required=True)
    p.add_argument("--slice", required=True)
    p.add_argument("--design")
    p.add_argument("--test-cmd", default="npm test")
    p.add_argument("--comment-threshold", type=float, default=5)
    p.add_argument("--padding-threshold", type=float, default=10)
    p.add_argument("--timeout", type=float, default=600)
    p.add_argument("--json")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    project = os.path.abspath(a.project)
    if not os.path.isdir(project):
        print(f"FAIL  project: {a.project} is not a directory\ndefinition of done: FAIL")
        return 1
    runner = runner_from(a.test_cmd)
    src, tests = source_files(project), test_files(project)
    design = find_design(os.path.abspath(a.planning), a.slice, a.design)
    slice_doc = find_slice(os.path.abspath(a.planning), a.slice)

    results = [
        ("readme", *check_readme(project, slice_doc)),
        ("lint-and-format", *check_lint(project, runner, a.timeout)),
        ("typecheck", *check_typecheck(project, runner, a.timeout)),
        ("no-code-in-strings", *check_code_in_strings(project, src)),
        ("no-planning-references", *check_planning_refs(project, src)),
        ("comment-density", *check_comments(project, src, a.comment_threshold)),
        ("kept-for-later-slices-persisted", *check_kept(project, design)),
        ("env-defaults-not-production", *check_env(project)),
        ("tests-not-padding", *check_padding(project, src, tests, a.padding_threshold)),
    ]
    table = {}
    for name, ok, detail, fix in results:
        print(f"{'SKIP' if ok is None else 'PASS' if ok else 'FAIL'}  {name}: {detail}")
        if ok is False:
            print(f"  fix: {fix}")
        table[name] = {"passed": ok, "detail": detail, "fix": fix}
    passed = all(ok is not False for _, ok, _, _ in results)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"checks": table, "passed": passed, "source_files": len(src), "test_files": len(tests)}, f, indent=2)
    print("definition of done:", "PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
