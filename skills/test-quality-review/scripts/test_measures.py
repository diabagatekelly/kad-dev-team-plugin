"""Two measures of a test suite's shape, for `test-quality-review` at the slice review.

Both came out of the slice 2 review (handoff-slice2 P3.8): the same in run
3 and slice 2, absent in run 2's suite. Mechanical, so the reviewer
reports a number and names the tests, not an impression.

1. **Duplicated helpers.** A function or arrow constant defined at the top
   level of two or more test files (`function openPage(`, `const choose =
   (`, `async function startApp(`), outside the suite's shared support
   folder (`test/support/`, `helpers/`, `utils/`, `fixtures/`, `lib/`).
   Each is a helper copied instead of shared; slice 2 had `startApp` in
   10 files and a `chime` fixture in 17. Printed as `duplicated helpers
   <n>: <name> (<k> files), …`.
2. **Brittle assertions.** The share of assertions, per test, whose
   expected value is a regular expression, or a string literal that holds
   markup (`<tag`, `class="`, `aria-`, `role="`), a CSS fragment (`px`,
   `#id`, `.class` at the start, `rgb(`, a `property: value;` pair) or
   prose of four words or more. Such a test breaks on a wording or a
   markup change that changed no behaviour. Counted over `assert.*(`,
   `expect(…).to…(`, `assertEqual(` and `assertRegex(` calls whose
   argument list holds such a literal; tests are `test(`, `it(` and
   `def test_` definitions. Printed as `brittle assertions <b> over <t>
   tests: <share> per test`. The bar is `--bar` (default 0.30): run 3 and
   slice 2 measured 0.61 and 0.57 per test, run 2's suite 0.11; above the
   bar the line ends with `(Medium)` and the skill writes the finding
   naming the ten worst files.

Approximate by design: regex-level, no parser. A multi-line assertion is
read as one statement up to its closing `);` (or the next blank line).

Usage: python3 -I ${CLAUDE_SKILL_DIR}/scripts/test_measures.py --project <root> [--bar 0.30] [--json out.json]
"""
import argparse
import json
import os
import re
import sys

TEST_DIRS = {"test", "tests", "__tests__", "spec"}
SUPPORT_DIRS = {"support", "helpers", "utils", "fixtures", "lib", "__fixtures__"}
TEST_NAME = re.compile(r"\.(test|spec)\.[cm]?[jt]sx?$|^test_.*\.py$|_test\.py$")
SKIP = {"node_modules", "dist", "build", "coverage", ".git", "__pycache__", ".venv", "venv"}
HELPER_DEF = re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(|"
                        r"^(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*(?::[^=]*)?=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*(?::[^=]*)?=>|"
                        r"^(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(", re.M)
TEST_DEF = re.compile(r"\b(?:test|it)\s*\(|^\s*(?:async\s+)?def\s+test_", re.M)
ASSERT_START = re.compile(r"^\s*(?:await\s+)?(?:assert\.\w+\s*\(|assert\s*\(|expect\s*\(|self\.assert\w*\s*\(|assert\w*\s*\()", re.M)
STRING = re.compile(r"'((?:\\.|[^'\\\n])*)'|\"((?:\\.|[^\"\\\n])*)\"|`((?:\\.|[^`\\])*)`")
REGEX_LITERAL = re.compile(r"(?<![\w)\]])/(?:\\.|\[[^\]]*\]|[^/\n\\\[])+/[gimsuy]*(?=\s*[,)])")
MARKUP = re.compile(r"<[a-zA-Z][\w-]*[\s>/]|class=\"|aria-[\w-]+=|role=\"|</")
CSS = re.compile(r"\b\d+(?:\.\d+)?px\b|^#[\w-]+$|^\.[\w-]+(?:\s|$)|rgb\(|#[0-9a-fA-F]{3,8}\b|\b[\w-]+\s*:\s*[^;]+;")
NOT_TEST_WORDS = re.compile(r"[A-Za-z]")


def test_files(project):
    for dirpath, dirnames, filenames in os.walk(project):
        dirnames[:] = [d for d in dirnames if d not in SKIP and not d.startswith(".")]
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, project).replace(os.sep, "/")
            parts = rel.split("/")
            in_test_dir = any(p in TEST_DIRS for p in parts[:-1])
            if (in_test_dir or TEST_NAME.search(name)) and name.endswith((".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py")):
                yield rel, any(p in SUPPORT_DIRS for p in parts[:-1]), full


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def statements(text):
    """Assertion statements, each joined to its closing `);` or the next blank line."""
    lines = text.splitlines()
    out, i = [], 0
    while i < len(lines):
        if ASSERT_START.match(lines[i]):
            stmt, depth, j = [], 0, i
            while j < len(lines):
                stmt.append(lines[j])
                depth += lines[j].count("(") - lines[j].count(")")
                if (depth <= 0 and j > i) or (depth <= 0 and lines[j].rstrip().endswith((";", ")"))) or not lines[j].strip():
                    break
                j += 1
            out.append("\n".join(stmt))
            i = j + 1
        else:
            i += 1
    return out


def brittle(statement):
    if REGEX_LITERAL.search(statement):
        return "regex"
    for m in STRING.finditer(statement):
        lit = (m.group(1) or m.group(2) or m.group(3) or "").strip()
        if not lit:
            continue
        if MARKUP.search(lit):
            return "markup"
        if CSS.search(lit):
            return "css"
        words = [w for w in re.split(r"\s+", lit) if NOT_TEST_WORDS.search(w)]
        if len(words) >= 4:
            return "prose"
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", default=".")
    p.add_argument("--bar", type=float, default=0.30, help="brittle assertions per test above which the share is a Medium")
    p.add_argument("--json")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    project = os.path.abspath(a.project)

    defs = {}
    per_file, total_tests, total_brittle = {}, 0, 0
    kinds = {}
    for rel, support, full in test_files(project):
        text = read(full)
        if not support:
            for m in HELPER_DEF.finditer(text):
                name = m.group(1) or m.group(2) or m.group(3)
                if name and not name.startswith("test"):
                    defs.setdefault(name, set()).add(rel)
        if support:
            continue
        tests = len(TEST_DEF.findall(text))
        stmts = statements(text)
        b = [(s, brittle(s)) for s in stmts]
        b = [(s, k) for s, k in b if k]
        for _, k in b:
            kinds[k] = kinds.get(k, 0) + 1
        per_file[rel] = {"tests": tests, "assertions": len(stmts), "brittle": len(b)}
        total_tests += tests
        total_brittle += len(b)

    duplicated = {n: sorted(fs) for n, fs in defs.items() if len(fs) >= 2}
    share = round(total_brittle / total_tests, 2) if total_tests else 0.0
    worst = sorted(per_file.items(), key=lambda kv: -kv[1]["brittle"])[:10]

    dup_line = f"duplicated helpers {len(duplicated)}"
    if duplicated:
        dup_line += ": " + ", ".join(f"{n} ({len(fs)} files)" for n, fs in sorted(duplicated.items(), key=lambda kv: -len(kv[1])))
        dup_line += " (Medium: move each into the suite's support folder)"
    print(dup_line)
    for n, fs in sorted(duplicated.items(), key=lambda kv: -len(kv[1])):
        print(f"  {n}: {', '.join(fs)}")
    kind_text = ", ".join(f"{k} {v}" for k, v in sorted(kinds.items()))
    brittle_line = f"brittle assertions {total_brittle} over {total_tests} tests: {share:.2f} per test ({kind_text or 'none'}; bar {a.bar:g})"
    if share > a.bar:
        brittle_line += " (Medium)"
    print(brittle_line)
    for rel, m in worst:
        if m["brittle"]:
            print(f"  {rel}: {m['brittle']} of {m['assertions']} assertions in {m['tests']} tests")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"duplicated_helpers": duplicated, "tests": total_tests, "brittle": total_brittle, "share": share,
                       "bar": a.bar, "kinds": kinds, "files": per_file}, f, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
