#!/usr/bin/env python3
"""Stand-ins for the tools the fixture's `gate-checks.json` names.

The eval sandbox cannot install jscpd, knip, a type-aware linter or a
secret scanner, and the gate only needs each category to have a command
that prints its violations, so that the count can be held against the
baseline. Each check here is a small real detector, narrow on purpose:
it finds the one shape its category's planted violation has, counts the
same shapes already in the fixture's older code (the baseline), and is
no judge of anything else. One `violation: <file>:<line> <what>` line
per finding; exit 1 when there is one.

Usage: python3 tools/gate-check.py <floating-promise | any-type | deep-nesting | duplication | unused-export | secrets>
"""
import os
import re
import sys

SKIP = {"node_modules", "dist", ".git", "coverage", "docs", "tools"}
WINDOW = 6


def files(suffixes, tests):
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP)
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)[2:].replace(os.sep, "/")
            is_test = path.startswith("test/") or ".test." in name
            if name.endswith(suffixes) and (tests or not is_test):
                yield path


def lines_of(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read().split("\n")


def floating_promise():
    for path in files((".ts",), False):
        for n, line in enumerate(lines_of(path), 1):
            if re.match(r"\s*[\w.]+\([^)]*\)\.then\(", line):
                yield path, n, "a promise nothing awaits"


def any_type():
    for path in files((".ts",), False):
        for n, line in enumerate(lines_of(path), 1):
            code = line.split("//")[0]
            if re.search(r":\s*any\b|\bas any\b", code):
                yield path, n, "an `any`"


def deep_nesting():
    for path in files((".ts",), False):
        depth = 0
        for n, line in enumerate(lines_of(path), 1):
            code = re.sub(r"'[^']*'|\"[^\"]*\"|`[^`]*`|//.*$", "", line)
            if depth >= 5 and code.strip() and not code.strip().startswith("}"):
                yield path, n, f"a line at nesting depth {depth}"
            depth = max(0, depth + code.count("{") - code.count("}"))


def duplication():
    seen = {}
    for path in files((".ts",), False):
        rows = [(n, l.strip()) for n, l in enumerate(lines_of(path), 1)]
        rows = [(n, l) for n, l in rows if l and not re.match(r"^(?:[{}()\[\];,]+|import\b.*|//.*|\*.*|/\*.*)$", l)]
        previous_dup = False
        for i in range(len(rows) - WINDOW + 1):
            key = "\n".join(l for _, l in rows[i:i + WINDOW])
            first = seen.setdefault(key, (path, rows[i][0]))
            dup = first != (path, rows[i][0])
            if dup and not previous_dup:
                yield path, rows[i][0], f"{WINDOW} lines repeated from {first[0]}:{first[1]}"
            previous_dup = dup


def unused_export():
    texts = {path: "\n".join(lines_of(path)) for path in files((".ts",), True)}
    for path in files((".ts",), False):
        for n, line in enumerate(lines_of(path), 1):
            m = re.match(r"export\s+(?:async\s+)?(?:function|const|class)\s+([A-Za-z_$][\w$]*)", line)
            if m and not any(re.search(r"\b" + re.escape(m.group(1)) + r"\b", text)
                             for other, text in texts.items() if other != path):
                yield path, n, f"export `{m.group(1)}` nothing imports"


def secrets():
    # The fixture's own made-up key shape: a real scanner's patterns would
    # also fire on this repository.
    for path in files((".ts", ".json", ".yml", ".yaml", ".env", ".md"), True):
        for n, line in enumerate(lines_of(path), 1):
            if re.search(r"LIBKEY-[0-9A-F]{24}", line):
                yield path, n, "a desk API key"


CHECKS = {"floating-promise": floating_promise, "any-type": any_type, "deep-nesting": deep_nesting,
          "duplication": duplication, "unused-export": unused_export, "secrets": secrets}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in CHECKS:
        print(__doc__.strip().splitlines()[-1])
        return 2
    found = list(CHECKS[sys.argv[1]]())
    for path, n, what in found:
        print(f"violation: {path}:{n} {what}")
    print(f"{sys.argv[1]}: {len(found)} found")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
