"""Extract the architecture map from the real source tree, for `map-update`.

Regex-level reading of import, export and require statements; no compiler,
no language server, no build step. The skill ran twice on real projects
with an extractor the orchestrator wrote on the spot, which the chunk
loop's rules forbid, so this one ships with the skill and is the only
extractor it uses. It prints the map in the shape `map-update`'s SKILL.md
states (Modules table, changes since the prior map, duplication and
wrong-direction candidates) and, with `--write`, replaces
`<project>/docs/architecture-map.md`.

Modules: one per source file under the source roots (`src/` when the
project has one, else every top-level directory holding source files),
plus the **test support** modules: every non-test source file under a
test directory's `support/`, `helpers/`, `utils/`, `fixtures/` or
`lib/` folder (`test/support/persistent-app.ts`), listed with the tier
`test-support` so an implementation-level `map-query` can answer "is
there already a helper" (slice 2's builders consulted the map every
chunk and still redefined `openPage` and `startApp` in ten files, since
the map indexed `src/` only). Test files themselves stay out,
skipping `node_modules`, `dist`, `build`, `.git`, `coverage`, `.wrangler`,
`test`, `tests`, `__tests__`, `spec`, `evals`, `docs`, `planning`,
`audit-docs`, `scripts`, and test files by name (`*.test.*`, `*.spec.*`,
`test_*.py`). Paths are project-relative with `/`.

TypeScript and JavaScript (`.ts .tsx .js .jsx .mjs .cjs`, `.d.ts` included):
- Internal edges: `import … from '<spec>'`, `export … from '<spec>'`,
  `import('<spec>')`, `require('<spec>')` whose spec is relative (`./`,
  `../`), or starts with `#` and matches an `imports` entry in
  package.json, or matches a `compilerOptions.paths` alias (with
  `baseUrl`) in tsconfig.json. Resolution tries the spec as written, then
  with `.ts .tsx .js .jsx .mjs .cjs .d.ts` appended (a `.js` spec is also
  tried as `.ts`/`.tsx`, the ESM-in-TypeScript idiom), then `<spec>/index`
  with those extensions. An `import type` edge is kept and marked
  `(type)`. A spec that does not resolve inside the project is external.
- External packages: the bare package name (`@scope/name`, or the first
  segment; subpaths stripped); Node built-ins as `node:<name>` whether or
  not the prefix was written.
- Exports: `export [default] [async] function|class|abstract class|const|
  let|var|enum|type|interface <name>`; `export default <anything else>`
  as `default`; `export { a, b as c }` (the exported name); `export * from`
  as `* from <spec>`; CommonJS `module.exports = ` as `default` and
  `exports.<name> =`.

Python (`.py`): `import a.b` and `from a.b import c, d` resolve internally
when `a/b.py` or `a/b/__init__.py` exists under a source root or the
project root; `from a import c` also resolves `a/c.py` (the member is a
module); relative forms (`from . import x`, `from ..pkg import y`) resolve
against the importing file's package. A spec that resolves nowhere is an
external package (first segment). Exports: the names in `__all__` when it
is assigned, else every top-level `def`, `class` and UPPER_CASE assignment
not starting with `_`.

Any other extension found under the source roots (`.go .rs .java .rb .php
.cs .kt .swift .sql`, anything else) is listed in the Modules table with
`no extractor` in its edges, externals and exports columns, and the
languages are named under `## Coverage`: their edges are unknown, never
guessed.

Tiers are never inferred. The prior map's `## Modules` table gives each
module its tier by path; `--tier <path>=<n>` gives one the slice's design
states; a module in neither is `untiered`. The prior map
also supplies the diff (new/removed modules, edges, externals, exports) and
the carried-forward wrong-direction candidates (its own bullets, kept with
`— carried forward`).

Duplication candidates: an export name (not `default`, not `* from …`,
longer than two characters) exported by two or more modules; and two
modules whose internal import targets overlap on three or more targets
with a Jaccard index of at least 0.6. Wrong-direction candidates: a new
internal edge whose importer has a lower (more important) numeric tier
than the module it imports; an edge with an untiered side goes under
`Untiered, direction unknown:`. Facts, not verdicts, as the skill says.

The last line of stdout is `map written: <path> (<n> modules, <e> internal
edges, <x> externals; no extractor for: <languages or none>)` with
`--write`, or `map: (…)` without it. `--json FILE` writes the extraction.
Exit 0; 1 when the project directory does not exist.

Usage: python3 -I ${CLAUDE_SKILL_DIR}/scripts/extract_map.py --project DIR
           [--prior docs/architecture-map.md] [--write] [--date YYYY-MM-DD] [--json out.json]
"""
import argparse
import datetime
import json
import os
import re
import sys

TS_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
RESOLVE_EXT = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".d.ts"]
SKIP = {"node_modules", "dist", "build", ".git", "coverage", ".wrangler", "test", "tests", "__tests__", "spec",
        "evals", "docs", "planning", "audit-docs", "scripts", ".claude", ".github", "__pycache__", ".venv", "venv"}
TEST_NAME = re.compile(r"(\.(test|spec)\.[cm]?[jt]sx?$)|(^test_.*\.py$)|(_test\.py$)")
NODE_BUILTINS = {"assert", "async_hooks", "buffer", "child_process", "cluster", "console", "constants", "crypto", "dgram",
                 "diagnostics_channel", "dns", "domain", "events", "fs", "http", "http2", "https", "inspector", "module",
                 "net", "os", "path", "perf_hooks", "process", "punycode", "querystring", "readline", "repl", "stream",
                 "string_decoder", "sys", "timers", "tls", "trace_events", "tty", "url", "util", "v8", "vm", "wasi",
                 "worker_threads", "zlib", "test"}
LANG = {".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript",
        ".cjs": "JavaScript", ".py": "Python", ".go": "Go", ".rs": "Rust", ".java": "Java", ".rb": "Ruby", ".php": "PHP",
        ".cs": "C#", ".kt": "Kotlin", ".swift": "Swift", ".sql": "SQL"}

IMPORT_RE = re.compile(
    r"""(?:^|[;\s])import\s+(type\s+)?(?:[\w*{}\s,$]+?\s+from\s+)?['"]([^'"]+)['"]|"""
    r"""(?:^|[;\s])export\s+(type\s+)?(?:[\w*{}\s,$]+?\s+)?from\s+['"]([^'"]+)['"]|"""
    r"""\bimport\s*\(\s*['"]([^'"]+)['"]\s*\)|"""
    r"""\brequire\s*\(\s*['"]([^'"]+)['"]\s*\)""", re.M)
EXPORT_RE = re.compile(
    r"^\s*export\s+(?:declare\s+)?(default\s+)?(?:async\s+)?(?:abstract\s+)?(function\*?|class|const|let|var|enum|type|interface|namespace)\s+([A-Za-z_$][\w$]*)", re.M)
EXPORT_BRACE_RE = re.compile(r"^\s*export\s+(?:type\s+)?\{([^}]*)\}(?!\s*from)", re.M | re.S)
EXPORT_DEFAULT_RE = re.compile(r"^\s*export\s+default\b", re.M)
EXPORT_STAR_RE = re.compile(r"^\s*export\s+\*\s+(?:as\s+\w+\s+)?from\s+['\"]([^'\"]+)['\"]", re.M)
CJS_RE = re.compile(r"^\s*(?:module\.exports\s*=|exports\.([A-Za-z_$][\w$]*)\s*=)", re.M)
PY_IMPORT_RE = re.compile(r"^\s*(?:from\s+([.\w]+)\s+import\s+([^\n(]+|\([^)]*\))|import\s+([\w.]+(?:\s*,\s*[\w.]+)*))", re.M)
PY_DEF_RE = re.compile(r"^(?:def|class)\s+([A-Za-z_]\w*)|^([A-Z][A-Z0-9_]+)\s*(?::[^=]+)?=", re.M)
PY_ALL_RE = re.compile(r"^__all__\s*(?::\s*[^=]+)?=\s*[\[(]([^\])]*)[\])]", re.M | re.S)


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"(^|[^:\\'\"])//[^\n]*", r"\1", text)


def rel(project, path):
    return os.path.relpath(path, project).replace(os.sep, "/")


def source_roots(project):
    if os.path.isdir(os.path.join(project, "src")):
        return [os.path.join(project, "src")]
    roots = []
    for d in sorted(os.listdir(project)):
        full = os.path.join(project, d)
        if os.path.isdir(full) and d not in SKIP and not d.startswith("."):
            if any(f.endswith(tuple(LANG)) for _, _, fs in os.walk(full) for f in fs):
                roots.append(full)
    return roots


TEST_DIRS = ("test", "tests", "__tests__", "spec")
SUPPORT_DIRS = ("support", "helpers", "utils", "fixtures", "lib")


def test_support_roots(project):
    """`test/support/`-style folders: the helpers a test suite shares."""
    roots = []
    for t in TEST_DIRS:
        for sdir in SUPPORT_DIRS:
            full = os.path.join(project, t, sdir)
            if os.path.isdir(full):
                roots.append(full)
    return roots


def modules_under(project, roots):
    files = []
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP and not d.startswith("."))
            for f in sorted(filenames):
                ext = os.path.splitext(f)[1].lower()
                if ext in LANG and not TEST_NAME.search(f):
                    files.append(rel(project, os.path.join(dirpath, f)))
    return sorted(files)


def load_json(path):
    try:
        text = read(path)
        text = re.sub(r"/\*.*?\*/|(^|[^:\"'])//[^\n]*", r"\1", text, flags=re.S)
        text = re.sub(r",(\s*[}\]])", r"\1", text)
        return json.loads(text)
    except (OSError, ValueError):
        return {}


def aliases(project):
    """[(prefix, [target dirs])] from tsconfig paths and package.json imports."""
    out = []
    ts = load_json(os.path.join(project, "tsconfig.json")).get("compilerOptions", {}) or {}
    base = os.path.join(project, ts.get("baseUrl", "."))
    for pattern, targets in (ts.get("paths") or {}).items():
        out.append((pattern.rstrip("*"), [os.path.join(base, t.rstrip("*")) for t in targets]))
    for pattern, target in (load_json(os.path.join(project, "package.json")).get("imports") or {}).items():
        if isinstance(target, str):
            out.append((pattern.rstrip("*"), [os.path.join(project, target.lstrip("./").rstrip("*"))]))
    return out


def resolve_file(candidate):
    candidates = [candidate]
    if re.search(r"\.[cm]?jsx?$", candidate):
        stem = re.sub(r"\.[cm]?jsx?$", "", candidate)
        candidates += [stem + ".ts", stem + ".tsx", stem + ".mts", stem + ".cts"]
    candidates += [candidate + e for e in RESOLVE_EXT]
    candidates += [os.path.join(candidate, "index" + e) for e in RESOLVE_EXT]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def resolve_ts(project, importer, spec, alias_list, known):
    if spec.startswith("."):
        found = resolve_file(os.path.normpath(os.path.join(os.path.dirname(os.path.join(project, importer)), spec)))
    else:
        found = None
        for prefix, targets in alias_list:
            if spec.startswith(prefix):
                for t in targets:
                    found = resolve_file(os.path.normpath(os.path.join(t, spec[len(prefix):])))
                    if found:
                        break
            if found:
                break
    if found:
        r = rel(project, found)
        return r if r in known or os.path.isfile(found) else None
    return None


def package_name(spec):
    if spec.startswith("node:"):
        return spec
    if spec.startswith("@"):
        return "/".join(spec.split("/")[:2])
    head = spec.split("/")[0]
    return "node:" + head if head in NODE_BUILTINS else head


def extract_ts(project, module, alias_list, known):
    text = strip_comments(read(os.path.join(project, module)))
    edges, externals = {}, set()
    for m in IMPORT_RE.finditer(text):
        is_type = bool(m.group(1) or m.group(3))
        spec = m.group(2) or m.group(4) or m.group(5) or m.group(6)
        if not spec:
            continue
        target = resolve_ts(project, module, spec, alias_list, known)
        if target and target != module:
            edges[target] = edges.get(target, True) and is_type
        elif not spec.startswith(".") and not target:
            externals.add(package_name(spec))
    exports = set()
    for m in EXPORT_RE.finditer(text):
        exports.add("default" if m.group(1) else m.group(3))
    for m in EXPORT_BRACE_RE.finditer(text):
        for part in m.group(1).split(","):
            part = part.strip().replace("type ", "")
            if part:
                exports.add(part.split(" as ")[-1].strip())
    if EXPORT_DEFAULT_RE.search(text):
        exports.add("default")
    for m in EXPORT_STAR_RE.finditer(text):
        exports.add("* from " + m.group(1))
    for m in CJS_RE.finditer(text):
        exports.add(m.group(1) or "default")
    return edges, externals, exports


def py_roots(project, roots):
    return [project] + roots


def resolve_py(project, importer, dotted, member, roots):
    """A module path for `dotted` (and `dotted.member`), or None."""
    if dotted.startswith("."):
        level = len(dotted) - len(dotted.lstrip("."))
        base = os.path.dirname(os.path.join(project, importer))
        for _ in range(level - 1):
            base = os.path.dirname(base)
        bases = [base]
        tail = dotted.lstrip(".")
    else:
        bases, tail = roots, dotted
    parts = [p for p in tail.split(".") if p]
    for b in bases:
        for candidate in ([parts + [member]] if member else []) + [parts]:
            if not candidate:
                continue
            path = os.path.join(b, *candidate)
            for f in (path + ".py", os.path.join(path, "__init__.py")):
                if os.path.isfile(f):
                    return rel(project, f)
    return None


def extract_py(project, module, roots):
    text = read(os.path.join(project, module))
    edges, externals = {}, set()
    for m in PY_IMPORT_RE.finditer(text):
        if m.group(3):
            for dotted in re.split(r"\s*,\s*", m.group(3).strip()):
                dotted = dotted.split(" as ")[0].strip()
                target = resolve_py(project, module, dotted, None, roots)
                if target and target != module:
                    edges[target] = False
                elif not target:
                    externals.add(dotted.split(".")[0])
            continue
        dotted, members = m.group(1), m.group(2).strip().strip("()")
        names = [n.strip().split(" as ")[0].strip() for n in members.split(",") if n.strip()]
        hit = False
        for name in names or [None]:
            target = resolve_py(project, module, dotted, name if name != "*" else None, roots)
            if target and target != module:
                edges[target] = False
                hit = True
        if not hit and not dotted.startswith("."):
            externals.add(dotted.split(".")[0])
    m = PY_ALL_RE.search(text)
    if m:
        exports = set(re.findall(r"['\"]([^'\"]+)['\"]", m.group(1)))
    else:
        exports = {a or b for a, b in PY_DEF_RE.findall(text) if not (a or b).startswith("_")}
    return edges, externals, exports


NOTHING = {"", "—", "–", "-", "none", "n/a", "(none)"}


def cell_names(text):
    """The names in a prior row's cell, or None when it cannot be read.
    Between backticks when the cell has any (the form this script
    writes); else a plain cell split on commas and semicolons, since a
    map written or edited by hand often has no backticks; a dash or
    `none` is no name. A plain entry with a space in it (a sentence, not
    a name) makes the cell unreadable: read as names, every real edge
    would then look new."""
    ticked = re.findall(r"`([^`]+)`", text)
    if ticked:
        return {n.replace(" (type)", "") for n in ticked}
    plain = text.replace("\\|", "|").strip()
    if plain.lower() in NOTHING:
        return set()
    names = {part.strip().replace(" (type)", "") for part in re.split(r"[;,]", plain) if part.strip()}
    return None if any(re.search(r"\s", n) for n in names) else names


def parse_prior(path):
    """{module: {"tier", "edges", "externals", "exports"}}, the carried
    wrong-direction bullets. A row that cannot be read (too few cells, or
    a cell that is prose) keeps its tier and carries `"unreadable": why`:
    the changes section names it and compares nothing against it."""
    prior, wrong = {}, []
    text = read(path) if path and os.path.isfile(path) else ""
    section = ""
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
            continue
        if section.startswith("modules") and line.startswith("|"):
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
            if not cells or cells[0] in ("Path", "") or set(cells[0]) <= {"-", ":", " "}:
                continue
            name = cells[0].strip("`")
            entry = {"tier": cells[1].strip("`") if len(cells) > 1 else "untiered", "edges": set(), "externals": set(), "exports": set()}
            if len(cells) < 5:
                entry["unreadable"] = f"{len(cells)} cells, five expected"
            else:
                read_cells = [cell_names(c) for c in cells[2:5]]
                if any(c is None for c in read_cells):
                    which = [label for label, c in zip(("internal edges", "external packages", "exports"), read_cells) if c is None]
                    entry["unreadable"] = "its " + " and ".join(which) + " cell is not a list of names"
                else:
                    entry["edges"], entry["externals"], entry["exports"] = read_cells
            prior[name] = entry
        elif section.startswith("wrong-direction") and line.startswith("- ") and "→" in line and "untiered" not in line:
            wrong.append(line[2:].split(" — ")[0].strip())
    return prior, wrong


def tier_number(tier):
    m = re.search(r"\d+", tier or "")
    return int(m.group(0)) if m else None


def cell(items):
    return "; ".join(f"`{i}`" for i in sorted(items)).replace("|", "\\|") if items else "—"


def render(project, date, modules, prior, prior_wrong, no_extractor):
    lines = [f"# Architecture map — updated {date}", "",
             "Generated by `architecture-cartographer:map-update` with the skill's `extract_map.py`: "
             "import, export and require statements read from the source files, tests left out, tiers carried from the prior map. "
             "Edges are facts of the text; nothing here is a verdict.", "",
             "## Modules", "| Path | Tier | Internal edges (imports) | External packages | Public exports |", "|---|---|---|---|---|"]
    for name, m in modules.items():
        if m["lang"] in no_extractor:
            lines.append(f"| `{name}` | {m['tier']} | no extractor | no extractor | no extractor |")
            continue
        edge_cell = "; ".join(f"`{t}`" + (" (type)" if is_type else "") for t, is_type in sorted(m["edges"].items())) or "—"
        lines.append(f"| `{name}` | {m['tier']} | {edge_cell} | {cell(m['externals'])} | {cell(m['exports'])} |")
    if no_extractor:
        lines += ["", "## Coverage", f"No extractor for: {', '.join(sorted(no_extractor))}. Those modules are listed from the tree with no "
                  "edges and no exports; their dependencies are unknown, not absent."]
    lines += ["", "## Changes since the prior map"]
    if not prior:
        lines.append("No prior map; everything is new.")
    else:
        new_mods = sorted(set(modules) - set(prior))
        gone = sorted(set(prior) - set(modules))
        gone_mods = [m for m in gone if os.path.isfile(os.path.join(project, m)) is False]
        out_of_scope = [m for m in gone if m not in gone_mods]
        changes = []
        if new_mods:
            changes.append("- New modules: " + ", ".join(f"`{m}`" for m in new_mods))
        if gone_mods:
            changes.append("- Removed modules: " + ", ".join(f"`{m}`" for m in gone_mods))
        if out_of_scope:
            changes.append("- No longer in the map's scope (the file exists, outside the source roots or a test): "
                           + ", ".join(f"`{m}`" for m in out_of_scope))
        for name, m in modules.items():
            if name not in prior:
                continue
            p = prior[name]
            if p.get("unreadable"):
                changes.append(f"- `{name}`: the prior map's row could not be read ({p['unreadable']}); "
                               "its edges, packages and exports are not compared, and none is reported as new")
                continue
            for label, now, before in (("internal edges", set(m["edges"]), p["edges"]), ("external packages", m["externals"], p["externals"]),
                                       ("exports", m["exports"], p["exports"])):
                added, removed = sorted(now - before), sorted(before - now)
                if added:
                    changes.append(f"- `{name}`: new {label}: " + ", ".join(f"`{x}`" for x in added))
                if removed:
                    changes.append(f"- `{name}`: removed {label}: " + ", ".join(f"`{x}`" for x in removed))
        lines += changes or ["No change in modules, edges or exports."]
    lines += ["", "## Duplication candidates"]
    by_export = {}
    for name, m in modules.items():
        for e in m["exports"]:
            if e != "default" and not e.startswith("* from") and len(e) > 2:
                by_export.setdefault(e, []).append(name)
    groups = {}
    for e, owners in by_export.items():
        if len(owners) > 1:
            groups.setdefault(tuple(sorted(owners)), []).append(e)
    dup = [f"- {' and '.join(f'`{o}`' for o in owners)} share exports: {', '.join(f'`{e}`' for e in sorted(es))}. Real duplicate or coincidence: not decided here."
           for owners, es in sorted(groups.items())]
    names = list(modules)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ea, eb = set(modules[a]["edges"]), set(modules[b]["edges"])
            shared = ea & eb
            if len(shared) >= 3 and len(shared) / len(ea | eb) >= 0.6:
                dup.append(f"- `{a}` and `{b}` import the same targets: {', '.join(f'`{t}`' for t in sorted(shared))}. Real duplicate or coincidence: not decided here.")
    lines += dup or ["None found."]
    lines += ["", "## Wrong-direction candidates"]
    wrong, unknown = [], []
    for name, m in modules.items():
        if m["tier"] == "test-support":
            continue  # a test helper importing the source is the expected direction, never a candidate
        for target in sorted(m["edges"]):
            if target not in modules:
                continue
            a, b = tier_number(m["tier"]), tier_number(modules[target]["tier"])
            label = f"`{name}` ({m['tier']}) → `{target}` ({modules[target]['tier']})"
            if a is None or b is None:
                unknown.append("- " + label)
            elif a < b:
                carried = name in prior and target in prior[name]["edges"]
                wrong.append("- " + label + (" — carried forward" if carried or label in prior_wrong else " — new"))
    lines += wrong or ["None found."]
    lines += ["", "Untiered, direction unknown:"] + (unknown or ["- none"])
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True)
    p.add_argument("--prior", help="the prior map (default <project>/docs/architecture-map.md)")
    p.add_argument("--write", action="store_true")
    p.add_argument("--date", default=datetime.date.today().isoformat())
    p.add_argument("--json")
    p.add_argument("--tier", action="append", default=[], metavar="PATH=TIER",
                   help="a module's tier as the slice's design states it (lending/cancel-hold.ts=1); repeatable; "
                        "it replaces the prior map's tier for that module")
    a = p.parse_args()
    given = {}
    for item in a.tier:
        path, sep, tier = item.partition("=")
        tier = tier.strip().lower()
        if tier.isdigit():
            tier = f"tier {tier}"
        if not sep or not re.fullmatch(r"tier \d+|untiered", tier):
            print(f"map: --tier takes <path>=<number>, as in lending/cancel-hold.ts=1 (got {item!r})")
            return 1
        given[path.strip().strip("`").replace("\\", "/")] = tier
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    project = os.path.abspath(a.project)
    if not os.path.isdir(project):
        print(f"map: {a.project} is not a directory")
        return 1
    prior_path = a.prior or os.path.join(project, "docs", "architecture-map.md")
    prior, prior_wrong = parse_prior(prior_path)
    roots = source_roots(project)
    support_roots = test_support_roots(project)
    known = modules_under(project, roots) + modules_under(project, support_roots)
    support = set(modules_under(project, support_roots))
    alias_list = aliases(project)
    pyroots = py_roots(project, roots)
    modules, no_extractor = {}, set()
    for name in known:
        ext = os.path.splitext(name)[1].lower()
        lang = LANG.get(ext, ext)
        tier = "test-support" if name in support else given.get(name) or prior.get(name, {}).get("tier", "untiered")
        if ext in TS_EXT:
            edges, externals, exports = extract_ts(project, name, alias_list, set(known))
        elif ext == ".py":
            edges, externals, exports = extract_py(project, name, pyroots)
        else:
            edges, externals, exports = {}, set(), set()
            no_extractor.add(lang)
        modules[name] = {"tier": tier, "lang": lang, "edges": edges, "externals": externals, "exports": exports}
    unknown = sorted(set(given) - set(modules))
    if unknown:
        print(f"map: --tier names no module of this project: {', '.join(unknown)}")
        return 1
    text = render(project, a.date, modules, prior, prior_wrong, no_extractor)
    print(text)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({n: {"tier": m["tier"], "language": m["lang"], "edges": m["edges"], "externals": sorted(m["externals"]),
                           "exports": sorted(m["exports"])} for n, m in modules.items()}, f, indent=2)
    edges = sum(len(m["edges"]) for m in modules.values())
    externals = len({x for m in modules.values() for x in m["externals"]})
    figures = f"({len(modules)} modules, {edges} internal edges, {externals} externals; no extractor for: {', '.join(sorted(no_extractor)) or 'none'})"
    if a.write:
        out = os.path.join(project, "docs", "architecture-map.md")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"map written: {out} {figures}")
    else:
        print(f"map: {figures}")
    untiered_new = sorted(n for n, m in modules.items() if m["tier"] == "untiered" and n not in prior)
    if untiered_new and prior:
        print(f"new and untiered: {', '.join(untiered_new)} (a tier the slice's design states goes in with --tier <path>=<n>, and the script is run again)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
