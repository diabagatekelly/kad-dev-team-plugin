"""Is anything from a file the owner provided written down by value?

A planning stage that reads a sheet, an export or any other file of the
owner's records it in `sources.md` in the target directory (a location, a
tab or range, a date; never a value) and writes every example with
invented names and amounts. This script is the mechanical half of that
rule: it reads each listed source where it is, and looks for its text and
numeric cells in everything that could be committed. It never prints a
value: a hit is a file, a line, a column span and the cell it matches.
Slice 2 took one real merchant and its fee from the owner's budget
workbook into a requirements sentence; the slice, the design, the story,
the plan's test names and thirteen test files carried it, a criterion
saying "nothing from the workbook in the repository" was written five
minutes after two documents already broke it, and the removal from
history named the removed values in its own record.

`sources.md`, as the planning skills write it:

    # Sources
    | Source | Location | Tab or range | Read on | Listed at |
    |---|---|---|---|---|
    | desk fees export | `~/Documents/library/desk-fees.csv` | all | 2026-11-09 | `4fc83e4` |

    ## Allowed by the owner
    - `Late return` — "that is the app's own wording, keep it" (2026-11-09)

Every table row whose Location cell is a path is a source (`~` and
environment variables expanded; a relative path is taken from the project
root, then from the planning directory). `.csv`, `.tsv`, `.txt` (delimited)
and `.xlsx`/`.xlsm` are read, with the standard library alone (a workbook
is a zip of XML; no `openpyxl` is needed, and under `python3 -I` a user
install of it would not be visible anyway). Anything else (a screenshot, a
PDF) is listed as `not scannable`. A listed source that cannot be read is
a failure, never a pass: a scan that could not run must not read as
"nothing found". So is a listed source that git tracks or would track,
and a byte-for-byte copy of one anywhere in the tree or in a commit
(found by digest, since a workbook is binary and never matches as text).
Files the scan cannot read as text are counted and said.

What is matched, from the tab each source's row names (`all`, a range or
an empty cell: every tab; a tab name the file does not have is reported
and every tab is read):

- **Text cells**, as whole words whatever their length: a cell's words
  (runs of letters and digits, case folded) found in the same order with
  nothing but punctuation or space between them. `netflixFee`,
  `NETFLIX_FEE` and `Netflix fee` all hold the word `netflix`. A single
  **word of a longer cell** (a surname from a full name, a brand from a
  card statement line; three letters or more, letters only, not a
  stop-word) is matched too, and counted only when it is a word of 1% of
  the source's rows or fewer (a name, not a descriptor like `payment`)
  and something else of its own row is in the same file: a whole cell of
  as few rows, or an amount of that row. A word alone is printed as not
  counted. A **cell of one word** counts on its own only when it is a
  name (four letters or more, in a tenth of the rows or fewer); a label
  (a category in a third of the rows, a three-letter code) is counted
  like a word of a longer cell, beside something else of its row. Matching every word of every cell on its
  own would match the language.
- **Numeric cells**, as amounts: in cents and in their formatted forms.
  12.5 is found as `12.50`, `12.5`, `12,50` and `1250`; 1234.5 also as
  `1,234.50` and `1.234,50`. A whole amount (15) is found only where it is
  written as money (`15.00`, `15,00`, `$15`, `15 EUR`), since a bare `15`
  or `1500` is every other number in a codebase. A whole number of five
  digits or more (an account number) is also found bare.

What is not matched, and printed with every result so nobody has to guess:

- the **stop-words**: a fixed list of function words, table words (`total`,
  `yes`, `n/a`), month and day names, printed in full; and the lines under
  `## Allowed by the owner` in `sources.md`, which only the owner's own
  words add to;
- each tab's **first non-empty row** (the column names, which the rule lets
  a session see);
- **date cells** (a date-formatted workbook cell, a date-shaped text cell)
  and, as the cents form only, a bare four-digit year (1900 to 2099).

What is matched and not counted, with the number of each printed (measured
on the slice 2 workbook, tens of thousands of cells: matching alone gave
thousands of hits on the planning directory after it had been scrubbed,
every one a coincidence, so a check without these two rules would have
been switched off on its first run; `--strict` turns both off):

- **Already there when the source was listed.** A value found in the tree
  at the commit in the row's `Listed at` cell cannot have come from a file
  nobody had read yet. No commit in the cell, or no repository: everything
  counts.
- **An amount alone in a source too dense for one to mean anything.** An
  amount counts on its own when fewer than 1 in 100 of all amounts of its
  length are in the sources (a sheet of seven fees: every one counts; the
  workbook held nearly half of all three-digit amounts of cents, so there
  a `7.35` alone is any number). Otherwise it counts
  where the same file also holds a counted text value from the same row of
  the source: the merchant and its fee.

A hit that counts and is a coincidence all the same (a category the app
also calls `Groceries`) is the owner's to allow, in their words, under
`## Allowed by the owner`.

Commands (every path in single quotes; `python3 -I` throughout):

  scan      --planning DIR [--project DIR] [--files F ...] [--history RANGE]
            [--map MAP] [--also FILE ...] [--strict] [--show] [--json OUT]
            The tree: every file git tracks or would track (untracked and
            not ignored) under the project root, plus the planning
            directory; lockfiles, `node_modules` and the like are skipped,
            and so are binary files. `--files` narrows it to those paths
            (the chunk gate passes the chunk's changed files). `--history
            <range>` scans every commit in `git rev-list <range>` instead:
            its message and every file it touched, each blob once.
            `--map MAP` looks for the keys of a replacement map (below)
            instead of the sources, which is the check after a removal.
            `--also FILE` adds files outside the tree (a pull request body
            in the scratchpad). Prints one `hit:` line per place, then
            `sources: PASS` or `sources: FAIL`. Exit 0, 1, or 2 when there
            is no `sources.md` (and no `--map`). `--show` adds the
            document's own text at each hit, for the one question that
            puts the places to the owner; output with `--show` is never
            saved to a file.
  describe  PATH [--tab NAME] [--range A1:D40] [--extract SCRATCH.csv]
            The shape of a source and nothing in it: per tab the row
            count, the column names, and how many cells of each kind each
            column holds. `--extract` copies the named tab or range to a
            scratch file, refused inside a git work tree.
  map       --planning DIR [--project DIR] [--history RANGE] --out MAP
            Writes a replacement map for every source value the scan
            finds: an invented word for each text value, an invented
            amount for each amount. The map holds the values, so `--out`
            is refused inside a git work tree. Prints counts only.
  apply     --map MAP (--tree DIR | --stdin)
            Rewrites the map's keys to their replacements in every text
            file under DIR, or in standard input. Prints counts only.
  rewrite   --project DIR --map MAP --range RANGE
            `git filter-branch` over the range with `apply` as the tree
            and message filter (file and directory names holding a value are
            renamed too), then removes the backup refs this rewrite made
            under `refs/original/`; refused when backups already exist
            there. Needs a clean tree. The old commits stay in the local reflog
            until the owner expires it, and in every copy made before
            (a remote, a transcript, an audit repository): the script says
            so and removes nothing else.

Imported by `readiness_check.py` (its tenth check) and `validation_gate.py`
(its `sources` check and its transcript line), which add this directory to
`sys.path` themselves since `-I` leaves it out.
"""
import argparse
import bisect
import csv
import io
import json
import os
import re
import shlex
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET
import hashlib

STOPWORDS = set("""
a an and are as at be been but by can did do does for from had has have he her his i if in into is it its
me my no nor not of off on or our she so than that the their them then there these they this those to too
up us was we were what when where which who whom why will with would you your yes ok okay true false none
null nil na n y x tbd tba todo other others misc miscellaneous total totals subtotal sum average count all
any each every per new old same more most less least first last next previous
jan january feb february mar march apr april may jun june jul july aug august sep sept september oct
october nov november dec december mon monday tue tues tuesday wed wednesday thu thur thurs thursday fri
friday sat saturday sun sunday today tomorrow yesterday
""".split())
SKIP_DIRS = {".git", "node_modules", "dist", "build", "coverage", "__pycache__", ".venv", "venv", ".next",
             ".turbo", ".cache", "vendor", ".idea", ".vscode"}
SKIP_FILES = re.compile(r"(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb?|npm-shrinkwrap\.json|"
                        r"Cargo\.lock|poetry\.lock|uv\.lock|Pipfile\.lock|composer\.lock|Gemfile\.lock|go\.sum)$")
READABLE = (".csv", ".tsv", ".txt", ".xlsx", ".xlsm")
MAX_BYTES = 5 * 1024 * 1024
HITS_SHOWN = 40

WORD = re.compile(r"[^\W_]+")
CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
CURRENCY = r"[$€£¥]|USD|EUR|GBP|CAD|AUD|CHF|JPY|dollars?|euros?|pounds?"
NUMBER = re.compile(
    r"(?<!\w)(?<!\d[.,])(?<!\d[-/:])(?P<pre>(?:[$€£¥]|USD|EUR|GBP|CAD|AUD|CHF|JPY)\s?)?"
    r"(?P<num>\d+(?:[.,]\d+)*)"
    r"(?P<post>\s?(?:" + CURRENCY + r")(?![^\W_]))?"
    r"(?![^\W_]|[.,]\d|[-/:]\d)")
DATE_TEXT = re.compile(
    r"^\s*(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}(?:[ T]\d{1,2}:\d{2}.*)?|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|"
    r"\d{1,2}:\d{2}(?::\d{2})?(?:\s?[AaPp][Mm])?|\d{1,2}(?:st|nd|rd|th)?[ -][A-Za-z]{3,9}\.?,?[ -]\d{2,4}|"
    r"[A-Za-z]{3,9}\.?[ -]\d{1,2}(?:st|nd|rd|th)?,?[ -]\d{2,4}|[A-Za-z]{3,9}\.?[ -]\d{2,4})\s*$")
CELL_NUMBER = re.compile(r"^\(?\s*[-+]?\s*(?:[$€£¥]|[A-Z]{3})?\s*[-+]?\s*(\d[\d.,' ]*)\s*(?:[$€£¥%]|[A-Z]{3})?\s*\)?$")
NAMES = ("Alder Birch Cedar Dogwood Elder Fennel Gorse Hazel Iris Juniper Kestrel Larch Maple Nettle Osier "
         "Privet Quince Rowan Sorrel Teasel Umber Vetch Willow Yarrow Zinnia Bramble Clover Damson Fescue "
         "Heather").split()
SUFFIXES = ("", "ford", "field", "wick", "stead", "holt", "mere", "combe")


def read_text(path):
    """A file's text, or None for a binary, oversized or unreadable one."""
    try:
        if os.path.getsize(path) > MAX_BYTES or not os.path.isfile(path):
            return None
        with open(path, "rb") as f:
            raw = f.read()
    except OSError:
        return None
    return decode(raw)


def decode(raw):
    if b"\0" in raw[:8192]:
        return None
    return raw.decode("utf-8", errors="replace")


def fold(word):
    return word.casefold()


def words(text):
    """The words of a cell value: runs of letters and digits, case folded."""
    return tuple(fold(m.group(0)) for m in WORD.finditer(text))


def text_tokens(line):
    """Two readings of a text, each a list of (start, end, folded word):
    whole runs, and runs split at camelCase boundaries when that differs."""
    plain, split, differs = [], [], False
    for m in WORD.finditer(line):
        plain.append((m.start(), m.end(), fold(m.group(0))))
        parts, last = [], 0
        for b in CAMEL.finditer(m.group(0)):
            if b.start() > last:
                parts.append((last, b.start()))
            last = b.start()
        parts.append((last, len(m.group(0))))
        if len(parts) > 1:
            differs = True
        for a, b in parts:
            split.append((m.start() + a, m.start() + b, fold(m.group(0)[a:b])))
    return [plain, split] if differs else [plain]


def to_cents(num):
    """(cents, form) for a number as written, or None. Forms: `int`,
    `decimal` (two places), `tenth` (one place)."""
    if re.fullmatch(r"\d+", num):
        return int(num) * 100, "int"
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+", num):
        return int(num.replace(",", "")) * 100, "int"
    m = (re.fullmatch(r"(\d+)[.,](\d{1,2})", num) or re.fullmatch(r"(\d{1,3}(?:,\d{3})+)\.(\d{1,2})", num)
         or re.fullmatch(r"(\d{1,3}(?:\.\d{3})+),(\d{1,2})", num))
    if not m:
        return None
    whole = int(re.sub(r"[.,]", "", m.group(1)))
    frac = m.group(2)
    return whole * 100 + (int(frac) * 10 if len(frac) == 1 else int(frac)), "tenth" if len(frac) == 1 else "decimal"


def cell_number(text):
    """A text cell that is a number (currency signs, thousands separators,
    a bracketed negative) as a float, else None."""
    m = CELL_NUMBER.match(text)
    if not m:
        return None
    digits = re.sub(r"[' ]", "", m.group(1)).rstrip(".,")
    parsed = to_cents(digits)
    if parsed is None:
        if re.fullmatch(r"\d+[.,]\d{3,}", digits):
            try:
                return float(digits.replace(",", "."))
            except ValueError:
                return None
        return None
    return parsed[0] / 100


# ---- reading a source ------------------------------------------------------

def col_letter(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def col_number(letters):
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch.upper()) - 64
    return n


def parse_range(rng):
    """`A1:D40` -> (col1, row1, col2, row2); None for no range."""
    if not rng:
        return None
    m = re.fullmatch(r"\$?([A-Za-z]+)\$?(\d+)(?::\$?([A-Za-z]+)\$?(\d+))?", rng.strip())
    if not m:
        raise SystemExit(f"not a range: {rng} (expected A1:D40)")
    c1, r1 = col_number(m.group(1)), int(m.group(2))
    c2, r2 = (col_number(m.group(3)), int(m.group(4))) if m.group(3) else (c1, r1)
    return min(c1, c2), min(r1, r2), max(c1, c2), max(r1, r2)


def read_delimited(path):
    with open(path, "rb") as f:
        raw = f.read()
    # A spreadsheet's "Unicode text" export is UTF-16 with a byte-order mark;
    # read as UTF-8 its cells would be NUL-ridden and never match.
    encoding = "utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    text = raw.decode(encoding, errors="replace")
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel_tab if path.lower().endswith(".tsv") else csv.excel
    cells = []
    for r, row in enumerate(csv.reader(io.StringIO(text), dialect), 1):
        for c, value in enumerate(row, 1):
            value = value.strip()
            if not value:
                continue
            number = cell_number(value)
            if DATE_TEXT.match(value):
                cells.append((r, c, "date", value))
            elif number is not None:
                cells.append((r, c, "number", number))
            else:
                cells.append((r, c, "text", value))
    return {"": cells}


def local(tag):
    return tag.rsplit("}", 1)[-1]


BUILTIN_DATE_FORMATS = set(range(14, 23)) | set(range(27, 37)) | set(range(45, 48)) | set(range(50, 59))


def workbook_date_styles(z):
    """The cell-style indexes whose number format is a date or a time."""
    if "xl/styles.xml" not in z.namelist():
        return set()
    root = ET.fromstring(z.read("xl/styles.xml"))
    custom = {}
    for el in root.iter():
        if local(el.tag) == "numFmt":
            code = re.sub(r'"[^"]*"|\[[^\]]*\]|\\.', "", el.get("formatCode", ""))
            custom[int(el.get("numFmtId", "0"))] = bool(re.search(r"[dmyhs]", code, re.I)) and not re.search(r"[0#]", code)
    styles = set()
    for el in root.iter():
        if local(el.tag) == "cellXfs":
            for i, xf in enumerate(el):
                fmt = int(xf.get("numFmtId", "0"))
                if fmt in BUILTIN_DATE_FORMATS or custom.get(fmt):
                    styles.add(i)
    return styles


def read_workbook(path):
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")):
                if local(si.tag) != "si":
                    continue
                parts = []
                for child in si:  # <t>, or rich-text runs <r><t>; phonetic runs (<rPh>) are not the text
                    if local(child.tag) == "t":
                        parts.append(child.text or "")
                    elif local(child.tag) == "r":
                        parts += [t.text or "" for t in child if local(t.tag) == "t"]
                shared.append("".join(parts))
        dates = workbook_date_styles(z)
        rels = {}
        if "xl/_rels/workbook.xml.rels" in names:
            for rel in ET.fromstring(z.read("xl/_rels/workbook.xml.rels")):
                target = rel.get("Target", "")
                rels[rel.get("Id")] = target.lstrip("/") if target.startswith("/") else "xl/" + target
        tabs = {}
        for el in ET.fromstring(z.read("xl/workbook.xml")).iter():
            if local(el.tag) != "sheet":
                continue
            rid = next((v for k, v in el.attrib.items() if local(k) == "id"), None)
            member = rels.get(rid)
            if not member or member not in names:
                continue
            cells = []
            for c in ET.fromstring(z.read(member)).iter():
                if local(c.tag) != "c":
                    continue
                ref = re.fullmatch(r"([A-Z]+)(\d+)", c.get("r", ""))
                if not ref:
                    continue
                kind = c.get("t", "n")
                v = next((x.text for x in c if local(x.tag) == "v"), None)
                if kind == "inlineStr":
                    v = "".join(t.text or "" for t in c.iter() if local(t.tag) == "t")
                if v is None or not str(v).strip():
                    continue
                row, col = int(ref.group(2)), col_number(ref.group(1))
                if kind == "s":
                    try:
                        text = shared[int(v)].strip()
                    except (ValueError, IndexError):
                        continue
                elif kind in ("str", "inlineStr"):
                    text = v.strip()
                elif kind == "n":
                    try:
                        number = float(v)
                    except ValueError:
                        continue
                    cells.append((row, col, "date" if int(c.get("s", "0")) in dates else "number", number))
                    continue
                else:  # booleans, errors
                    continue
                if not text:
                    continue
                number = cell_number(text)
                if DATE_TEXT.match(text):
                    cells.append((row, col, "date", text))
                elif number is not None:
                    cells.append((row, col, "number", number))
                else:
                    cells.append((row, col, "text", text))
            tabs[el.get("name", "")] = cells
        return tabs


def read_source(path):
    """{tab name: [(row, col, kind, value)]}; raises OSError/ValueError on a
    file that cannot be read."""
    if path.lower().endswith((".xlsx", ".xlsm")):
        try:
            return read_workbook(path)
        except (zipfile.BadZipFile, ET.ParseError, KeyError) as e:
            raise ValueError(f"not a readable workbook ({type(e).__name__})")
    return read_delimited(path)


def header_row(cells):
    return min((r for r, _, _, _ in cells), default=None)


# ---- sources.md --------------------------------------------------------------

def parse_sources(path):
    """([{name, location, tab}], [allowed text]) from a sources.md."""
    sources, allowed, section, header = [], [], "", None
    for line in (read_text(path) or "").splitlines():
        s = line.strip()
        if re.match(r"^#{1,6}\s", s):
            section, header = s.lstrip("#").strip().lower(), None
            continue
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            if header is None:
                header = [c.lower() for c in cells]
                continue
            row = dict(zip(header, cells))
            loc = next((v for k, v in row.items() if re.search(r"location|path|file", k)), None)
            if loc is None and len(cells) > 1:
                loc = cells[1]
            loc = (loc or "").strip().strip("`").strip("'\"").strip()
            if not loc or loc.startswith("<") or loc in ("-", "—"):
                continue
            tab = next((v for k, v in row.items() if re.search(r"tab|range|sheet", k)), "")
            listed = next((v for k, v in row.items() if re.search(r"listed|commit", k)), "")
            listed = re.search(r"\b[0-9a-f]{7,40}\b", listed)
            sources.append({"name": cells[0].strip("`* ") or os.path.basename(loc), "location": loc,
                            "tab": tab.strip("`"), "listed": listed.group(0) if listed else None})
            continue
        if "allowed" in section:
            m = re.match(r"^[-*+]\s+(.*)", s)
            if m:
                item = m.group(1)
                ticked = re.match(r"`([^`]+)`", item)
                allowed.append(ticked.group(1) if ticked else re.split(r"\s+[—–-]\s+|\s+\(", item, 1)[0].strip("\"' "))
    return sources, allowed


def resolve(location, project, planning):
    p = os.path.expanduser(os.path.expandvars(location))
    if os.path.isabs(p):
        return p
    bases, up = [project, planning], planning
    while up and os.path.dirname(up) != up:
        up = os.path.dirname(up)
        bases.append(up)
    bases.append(os.getcwd())
    for base in bases:
        if base and os.path.exists(os.path.join(base, p)):
            return os.path.join(base, p)
    return os.path.join(project or planning or ".", p)


# ---- the catalog of what to look for -------------------------------------------

class Catalog:
    """The values of every readable source, indexed for matching. Nothing
    in it is ever printed; a hit carries a cell reference instead."""

    def __init__(self):
        self.sources = []      # {name, location, path, status, counts}
        self.problems = []     # lines that fail the check on their own
        self.allowed = []      # the owner's allowed entries, as written
        self.phrases = {}      # first word -> [(words, ref)]
        self.amounts = {}      # cents -> ref
        self.long_ints = {}    # whole number of 5+ digits -> ref
        self.allowed_words = set()
        self.allowed_cents = set()
        self.rows = {}         # ("text", words joined), ("word", word) or ("amount", cents) -> {(source index, tab, row)}
        self.partials = {}     # a word of a multi-word cell -> ref (the surname of a full name, the brand of a card line)
        self.rows_per_source = {}  # source index -> rows under its column names
        self.owner = {}        # the same key -> index of the first source that holds it
        self.baseline = {}     # source index -> keys already in the tree when it was listed
        self.strict = False    # every match counts
        self.skipped = 0       # files or blobs not read as text (binary, over the size limit)

    def allow(self, entry):
        self.allowed.append(entry)
        w = words(entry)
        if w:
            self.allowed_words.add(w)
        n = cell_number(entry)
        if n is not None:
            self.allowed_cents.add(int(round(abs(n) * 100)))

    def add_text(self, text, ref, row=None):
        w = words(text)
        if not w or all(x in STOPWORDS for x in w) or w in self.allowed_words:
            return False
        key = ("text", " ".join(w))
        if key not in self.rows:
            self.phrases.setdefault(w[0], []).append((w, ref))
        self._place(key, row)
        parts = [tok[2] for tok in text_tokens(text)[-1]]  # camel-case runs split, as scanned text is
        if len(parts) > 1:
            for x in parts:
                if len(x) >= 3 and x.isalpha() and x not in STOPWORDS and (x,) not in self.allowed_words:
                    self.partials.setdefault(x, ref)
                    self._place(("word", x), row)
        return True

    def add_number(self, value, ref, row=None):
        cents = int(round(abs(value) * 100))
        if cents == 0 or cents in self.allowed_cents:
            return False
        self.amounts.setdefault(cents, ref)
        if cents % 100 == 0 and cents >= 10000 * 100:
            self.long_ints.setdefault(cents // 100, ref)
        self._place(("amount", cents), row)
        return True

    def _place(self, key, row):
        self.rows.setdefault(key, set())
        if row is not None:
            self.rows[key].add(row)
            self.owner.setdefault(key, row[0])

    def dense(self, cents):
        """True when 1 in 100 or more of all amounts of this length are in
        the sources: one alone then says nothing."""
        digits = len(str(cents))
        if not hasattr(self, "_by_length"):
            self._by_length = {}
            for c in self.amounts:
                self._by_length[len(str(c))] = self._by_length.get(len(str(c)), 0) + 1
        return self._by_length.get(digits, 0) * 100 >= 9 * 10 ** (digits - 1)

    def judge(self, hits):
        """(counted hits, {reason: number not counted}). Works file by file,
        since an amount in a dense source counts beside its own row's text."""
        if self.strict:
            return list(hits), {}
        counted, skipped = [], {}

        def sources_of(key):
            return {r[0] for r in self.rows.get(key, ())} or {self.owner.get(key)}

        def listed_before(h):
            # Already there for every source that holds the value: a source
            # listed earlier, before the value appeared, keeps its claim.
            key = h["key"][:2]
            return all(key in self.baseline.get(src, ()) for src in sources_of(key))

        def skip(reason):
            skipped[reason] = skipped.get(reason, 0) + 1

        def few(key):
            # A word of 1% of its source's rows or fewer is a name, not a
            # descriptor; a floor of three keeps a seven-row sheet's names in.
            return max(3, min(self.rows_per_source.get(src, 0) for src in sources_of(key)) // 100)

        def label_rows(key):
            # A one-word cell in more than a tenth of its source's rows is a
            # label, not a name; the same floor of three.
            return max(3, min(self.rows_per_source.get(src, 0) for src in sources_of(key)) // 10)
        for file_hits in by_file(hits).values():
            live = [h for h in file_hits if not (listed_before(h) and skip("already in the tree when the source was listed") is None)]
            texts = [h for h in live if h["kind"] == "text"]
            amounts = [h for h in live if h["kind"] == "amount"]
            wordhits = [h for h in live if h["kind"] == "word"]
            # A cell of one word counts on its own only when it is a name:
            # four letters or more, in a tenth of its source's rows or fewer
            # (a merchant in six rows of three hundred is a name; a category
            # in a third of them, or a three-letter code, is a label that
            # matches the language of any repository and counts like a word
            # of a longer cell: beside something else of its row).
            loose = [h for h in texts if " " not in h["key"][1]
                     and (len(h["key"][1]) < 4 or len(self.rows.get(h["key"][:2], set())) > label_rows(h["key"][:2]))]
            loose_ids = {id(h) for h in loose}
            texts = [h for h in texts if id(h) not in loose_ids]
            counted += texts
            rows_here = set().union(*(self.rows.get(h["key"][:2], set()) for h in texts)) if texts else set()
            # A word of a longer cell counts beside a whole cell of its row, or,
            # when it is a word of few rows, beside an amount of its row.
            # Only a word of few rows pairs, and only with a whole cell of few
            # rows or an amount of its row: a label in hundreds of rows pairs
            # with everything and says nothing.
            named_rows = set().union(*(self.rows.get(h["key"][:2], set()) for h in texts
                                       if len(self.rows.get(h["key"][:2], set())) <= few(h["key"][:2]))) if texts else set()
            word_rows, taken = set(), set()
            for h in wordhits + loose:
                rows = self.rows.get(h["key"][:2], set())
                rare = len(rows) <= (label_rows(h["key"][:2]) if id(h) in loose_ids else few(h["key"][:2]))
                paired = rare and bool(rows & named_rows)
                if not paired and rare:
                    for a in amounts:
                        if self.rows.get(a["key"][:2], set()) & rows:
                            paired = True
                            taken.add(id(a))
                if paired:
                    counted.append(h)
                    word_rows |= rows
                elif id(h) in loose_ids:
                    skip("a one-word cell, a label of many rows or short, with nothing else of its row in the file")
                else:
                    skip("a word of a longer cell, with nothing else of its row in the file")
            rows_here |= word_rows
            for a in amounts:
                key = a["key"][:2]
                if id(a) in taken or not self.dense(key[1]) or self.rows.get(key, set()) & rows_here:
                    counted.append(a)
                else:
                    skip("an amount alone, in a source too dense for one to mean anything")
        counted.sort(key=lambda h: (h["file"], h["line"], h["col"]))
        return counted, skipped

    def empty(self):
        return not self.phrases and not self.amounts

    # -- matching ------------------------------------------------------------

    def find(self, line):
        """[(start, end, kind, ref, key)] over a text, offsets into it; key is
        what a map is keyed by and is never printed. A value's words may be
        wrapped over a line break, as prose is, never over a blank line."""
        found, seen = [], set()
        for toks in text_tokens(line):
            for i, (start, end, word) in enumerate(toks):
                for phrase, ref in self.phrases.get(word, ()):
                    n = len(phrase)
                    if i + n <= len(toks) and all(toks[i + k][2] == phrase[k] for k in range(1, n)) \
                            and all(line.count("\n", toks[i + k - 1][1], toks[i + k][0]) <= 1 for k in range(1, n)):
                        span = (start, toks[i + n - 1][1])
                        if span not in seen:
                            seen.add(span)
                            found.append((span[0], span[1], "text", ref, ("text", " ".join(phrase))))
                if word in self.partials and (start, end) not in seen:
                    seen.add((start, end))
                    found.append((start, end, "word", self.partials[word], ("word", word)))
        # A hit inside a longer one is the longer one's (a word inside its
        # whole cell; a map's one-word key inside its two-word key), so a
        # rewrite never replaces the part and skips the whole.
        found = [f for f in found if not any((a < f[0] or f[1] < b) and a <= f[0] and f[1] <= b
                                              for a, b, _, _, _ in found)]
        for m in NUMBER.finditer(line):
            parsed = to_cents(m.group("num"))
            if parsed is None:
                continue
            cents, form = parsed
            money = bool(m.group("pre") or m.group("post"))
            ref = key = None
            if form == "int":
                n = cents // 100
                if money and cents in self.amounts:
                    ref, key = self.amounts[cents], ("amount", cents, "units")
                elif n in self.amounts and n % 100 and n >= 100 and not 1900 <= n <= 2099:
                    ref, key = self.amounts[n], ("amount", n, "cents")
                elif n in self.long_ints:
                    ref, key = self.long_ints[n], ("amount", cents, "units")
            elif cents in self.amounts and (form == "decimal" or cents % 100):
                ref, key = self.amounts[cents], ("amount", cents, form)
            if ref:
                found.append((m.start("num"), m.end("num"), "amount", ref, key))
        return sorted(found, key=lambda f: (f[0], f[1]))


def load(planning, project=None, sources_file=None, strict=False):
    """The catalog for `<planning>/sources.md`, or None when there is none."""
    path = sources_file or os.path.join(planning, "sources.md")
    if not os.path.isfile(path):
        return None
    cat = Catalog()
    listed, allowed = parse_sources(path)
    for entry in allowed:
        cat.allow(entry)
    for src in listed:
        full = resolve(src["location"], project, planning)
        info = {"name": src["name"], "location": src["location"], "path": full, "tab": src["tab"], "counts": {},
                "listed": src.get("listed")}
        index = len(cat.sources)
        cat.sources.append(info)
        if not full.lower().endswith(READABLE):
            info["status"] = "not scannable"
            continue
        if not os.path.isfile(full):
            info["status"] = "not readable"
            cat.problems.append(f"source not readable here: {src['name']} ({src['location']}); the scan could not run on it")
            continue
        try:
            tabs = read_source(full)
        except (OSError, ValueError) as e:
            info["status"] = "not readable"
            cat.problems.append(f"source not readable: {src['name']} ({src['location']}): {e}")
            continue
        info["status"] = "read"
        wanted = (src.get("tab") or "").strip()
        if wanted and wanted.lower() != "all" and not re.fullmatch(r"[A-Za-z]+\d+:[A-Za-z]+\d+", wanted):
            # The row names a tab: only that tab is read. A workbook of many
            # tabs listed as `all` matches the language of the repository.
            named = next((t for t in tabs if t == wanted), None) or next((t for t in tabs if t.lower() == wanted.lower()), None)
            if named is not None:
                tabs = {named: tabs[named]}
            else:
                cat.problems.append(f"source {src['name']}: no tab named {wanted!r} (tabs: {', '.join(repr(t) for t in tabs)}); every tab read")
        counts = {"tabs": len(tabs), "text": 0, "amounts": 0, "dates": 0, "column names": 0, "excluded": 0}
        for tab, cells in tabs.items():
            head = header_row(cells)
            cat.rows_per_source[index] = cat.rows_per_source.get(index, 0) + len({r for r, _, _, _ in cells if r != head})
            for row, col, kind, value in cells:
                ref = f"{src['name']} {tab + '!' if tab else ''}{col_letter(col)}{row}"
                if row == head:
                    counts["column names"] += 1
                elif kind == "date":
                    counts["dates"] += 1
                elif kind == "text":
                    counts["text" if cat.add_text(value, ref, (index, tab, row)) else "excluded"] += 1
                else:
                    counts["amounts" if cat.add_number(value, ref, (index, tab, row)) else "excluded"] += 1
        info["counts"] = counts
    if not strict and project:
        for index, info in enumerate(cat.sources):
            if info.get("listed") and info["status"] == "read":
                keys = tree_keys(cat, project, info["listed"])
                if keys is None:
                    info["listed"] = None
                else:
                    cat.baseline[index] = keys
    cat.strict = strict
    return cat


def tree_keys(cat, project, commit):
    """Every key of the catalog found in the tree of a commit, or None when
    the commit is not in this repository."""
    if git(project, "rev-parse", "--verify", "--quiet", commit + "^{commit}") is None:
        return None
    listing = git(project, "ls-tree", "-r", "-z", commit) or ""
    blobs = {}
    for entry in listing.split("\0"):
        meta, _, rel = entry.partition("\t")
        parts = meta.split()
        if len(parts) == 3 and parts[1] == "blob" and not skipped(rel):
            blobs.setdefault(parts[2], rel)
    if not blobs:
        return set()
    r = subprocess.run([find_git(), "-C", project, "cat-file", "--batch"], input="\n".join(blobs).encode() + b"\n",
                       capture_output=True)
    keys, data, pos = set(), r.stdout, 0
    while pos < len(data):
        end = data.find(b"\n", pos)
        if end < 0:
            break
        header = data[pos:end].split()
        if len(header) < 3:
            pos = end + 1
            continue
        size = int(header[2])
        raw = data[end + 1:end + 1 + size]
        pos = end + 1 + size + 1
        text = decode(raw) if size <= MAX_BYTES else None
        if text is None:
            continue
        for _, _, _, _, key in cat.find(text):
            keys.add(key[:2])
    return keys


def from_map(path):
    """A catalog whose values are a replacement map's keys."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    cat = Catalog()
    cat.strict = True
    cat.sources.append({"name": "replacement map", "location": path, "path": path, "status": "read", "tab": "",
                        "counts": {"text": len(data.get("text", {})), "amounts": len(data.get("amount", {}))}})
    for i, key in enumerate(data.get("text", {}), 1):
        w = tuple(key.split())
        cat.phrases.setdefault(w[0], []).append((w, f"map text {i}"))
    for i, key in enumerate(data.get("amount", {}), 1):
        cents = int(key)
        cat.amounts[cents] = f"map amount {i}"
        if cents % 100 == 0 and cents >= 10000 * 100:
            cat.long_ints[cents // 100] = f"map amount {i}"
    return cat, data


# ---- what is scanned -----------------------------------------------------------

_GIT = None


def find_git():
    """`git`, or a working one when the name resolves to a shim that cannot
    run where this script is (the eval sandbox on macOS)."""
    global _GIT
    if _GIT:
        return _GIT
    for cand in ("git", "/opt/homebrew/bin/git", "/usr/local/bin/git", "/opt/homebrew/sbin/git", "/usr/bin/git"):
        try:
            if subprocess.run([cand, "--version"], capture_output=True, timeout=20).returncode == 0:
                _GIT = cand
                return cand
        except (OSError, subprocess.SubprocessError):
            continue
    _GIT = "git"
    return _GIT


def git(project, *args, binary=False, check=False, env=None):
    r = subprocess.run([find_git(), "-C", project, *args], capture_output=True, env=env)
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(args[:3])} failed: {r.stderr.decode('utf-8', 'replace').strip()[:400]}")
    if r.returncode != 0:
        return None
    return r.stdout if binary else r.stdout.decode("utf-8", errors="replace")


def repo_root(path):
    out = git(path, "rev-parse", "--show-toplevel") if os.path.isdir(path) else None
    return out.strip() if out else None


def skipped(rel):
    parts = rel.replace(os.sep, "/").split("/")
    return any(p in SKIP_DIRS for p in parts[:-1]) or bool(SKIP_FILES.search(rel.replace(os.sep, "/")))


def tree_files(project, planning):
    """(files, tracked by git): project-relative paths of everything that
    could be committed, plus the planning directory when it lies outside
    the project."""
    rels = set()
    listed = git(project, "ls-files", "-z", "-co", "--exclude-standard") if project else None
    if listed is not None:
        rels.update(p for p in listed.split("\0") if p)
    roots = [] if listed is not None or not project else [project]
    if planning and (not project or os.path.relpath(planning, project).startswith("..")):
        roots.append(planning)
    files = [(r, os.path.join(project, r)) for r in sorted(rels) if not skipped(r)]
    for root in roots:
        if not root:
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in sorted(filenames):
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, project or root).replace(os.sep, "/")
                if not skipped(rel):
                    files.append((rel, full))
    return files, listed is not None


def scan_text(cat, text, where):
    """Every match in a text. `_text` is the document's own wording at the
    match, kept for `--show` and never written to a file."""
    starts = [0]
    for m in re.finditer("\n", text):
        starts.append(m.end())
    hits = []
    for start, end, kind, ref, key in cat.find(text):
        line = bisect.bisect_right(starts, start)
        last = bisect.bisect_right(starts, end - 1)
        hits.append({"file": where, "line": line, "col": start - starts[line - 1] + 1, "end": end - starts[last - 1],
                     "to_line": last if last != line else None, "kind": kind, "cell": ref, "key": key,
                     "_text": " ".join(text[start:end].split())})
    return hits


def source_digests(cat):
    """sha256 and size of every readable source, to recognise a copy of the
    file itself (a workbook committed whole is binary and never matched by
    text)."""
    out = {}
    for src in cat.sources:
        if src.get("status") != "read":
            continue
        try:
            with open(src["path"], "rb") as f:
                raw = f.read()
        except OSError:
            continue
        out[(hashlib.sha256(raw).hexdigest(), len(raw))] = src["name"]
    return out


def copy_of_source(cat, digests, raw):
    if not digests or raw is None:
        return None
    return digests.get((hashlib.sha256(raw).hexdigest(), len(raw)))


def scan_tree(cat, project, planning, only=None):
    """(hits, files scanned). A source that sits inside the tree is never
    scanned against itself; one git would commit is a problem of its own,
    and so is a copy of it under another name. Files the scan cannot read
    as text (binary, over the size limit) are counted on `cat.skipped`."""
    own = {os.path.realpath(s["path"]) for s in cat.sources}
    digests = source_digests(cat)
    candidates, tracked = tree_files(project, planning)
    if only is not None:
        wanted = {f.replace(os.sep, "/") for f in only}
        candidates = [(rel, full) for rel, full in candidates if rel in wanted]
    hits, scanned = [], 0
    for rel, full in candidates:
        if os.path.realpath(full) in own:
            if tracked:
                msg = f"source inside the repository and not ignored: {rel}; one `git add` from being committed"
                if msg not in cat.problems:
                    cat.problems.append(msg)
            continue
        text = read_text(full)
        if text is None:
            try:
                with open(full, "rb") as f:
                    raw = f.read(MAX_BYTES + 1)
            except OSError:
                raw = None
            name = copy_of_source(cat, digests, raw)
            if name:
                cat.problems.append(f"a copy of the source {name} is in the repository as {rel}")
            cat.skipped += 1
            continue
        scanned += 1
        hits += scan_text(cat, text, rel)
        for start, end, kind, ref, key in cat.find(rel):
            hits.append({"file": rel, "line": 0, "col": start + 1, "end": end, "to_line": None, "kind": kind, "cell": ref,
                         "key": key, "_text": rel[start:end]})
    return hits, scanned


def scan_history(cat, project, rng):
    """(hits, commits scanned): each commit's message and every blob it
    introduced, each blob once."""
    listed = git(project, "rev-list", rng, check=True)
    commits = [c for c in listed.split() if c]
    source_in_tree(cat, project)
    digests = source_digests(cat)
    hits, seen = [], set()
    for commit in commits:
        short = commit[:7]
        hits += scan_text(cat, git(project, "log", "-1", "--format=%B", commit) or "", f"{short} (message)")
        names = git(project, "diff-tree", "--root", "-m", "-r", "-z", "--no-commit-id", "--name-only", commit) or ""
        for rel in sorted({n for n in names.split("\0") if n}):
            for start, end, kind, ref, key in cat.find(rel):
                hits.append({"file": f"{short}:{rel}", "line": 0, "col": start + 1, "end": end, "to_line": None,
                             "kind": kind, "cell": ref, "key": key, "_text": rel[start:end]})
            if skipped(rel):
                continue
            blob = git(project, "rev-parse", "--verify", "--quiet", f"{commit}:{rel}")
            if not blob or blob.strip() in seen:
                continue
            seen.add(blob.strip())
            raw = git(project, "cat-file", "blob", blob.strip(), binary=True)
            text = decode(raw) if raw is not None and len(raw) <= MAX_BYTES else None
            if text is not None:
                hits += scan_text(cat, text, f"{short}:{rel}")
            else:
                name = copy_of_source(cat, digests, raw)
                if name:
                    cat.problems.append(f"a copy of the source {name} is in commit {short} as {rel}")
                cat.skipped += 1
    return hits, len(commits)


def source_in_tree(cat, project):
    """A listed source that git tracks, or would track, is a problem on its
    own, whichever way the scan runs."""
    if not project:
        return
    listed = git(project, "ls-files", "-z", "-co", "--exclude-standard")
    if listed is None:
        return
    tracked = {os.path.realpath(os.path.join(project, p)) for p in listed.split("\0") if p}
    for src in cat.sources:
        if os.path.realpath(src["path"]) in tracked:
            rel = os.path.relpath(src["path"], project).replace(os.sep, "/")
            msg = f"source inside the repository and not ignored: {rel}; one `git add` from being committed"
            if msg not in cat.problems:
                cat.problems.append(msg)


def strings_of(value):
    """Every string of a JSON value, keys and numbers included (a value
    serialised as a number or used as a key is a value all the same)."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, bool) or value is None:
        return
    elif isinstance(value, (int, float)):
        yield repr(value)
    elif isinstance(value, dict):
        for k, v in value.items():
            yield str(k)
            yield from strings_of(v)
    elif isinstance(value, list):
        for v in value:
            yield from strings_of(v)


def scan_transcript(cat, path):
    """(counted hits, entries holding one) over a session or agent
    transcript, or (None, None) when it cannot be read: every string of
    every JSON line, decoded first, since a raw line glues an escaped
    newline's `n` to the word after it; a line that is not JSON is scanned
    as it is, so nothing in the file goes unread. The audit sync's
    "withheld" rule reads the same answer."""
    hits = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for n, raw in enumerate(f, 1):
                try:
                    entry = json.loads(raw)
                except ValueError:
                    hits += scan_text(cat, raw, f"entry {n}")
                    continue
                for text in strings_of(entry):
                    hits += scan_text(cat, text, f"entry {n}")
    except OSError:
        return None, None
    counted, _ = cat.judge(hits)
    return counted, len(by_file(counted))


def hit_lines(hits, shown=HITS_SHOWN, show=False):
    lines = []
    for h in hits[:shown]:
        place = (f"{h['file']} (the path itself)" if not h["line"]
                 else f"{h['file']}:{h['line']} col {h['col']} to line {h['to_line']} col {h['end']}" if h.get("to_line")
                 else f"{h['file']}:{h['line']} col {h['col']}-{h['end']}")
        lines.append(f"hit: {place} — {h['kind']}, {h['cell']}" + (f" — written there as: {h['_text']}" if show else ""))
    if len(hits) > shown:
        lines.append(f"hit: … and {len(hits) - shown} more")
        lines += [f"in: {name} — {len(found)} hit(s)" for name, found in by_file(hits).items()]
    if show:
        # One line per distinct value, as the documents write it: what the
        # one question to the owner lists.
        groups = {}
        for h in hits:
            groups.setdefault(h["key"][:2], []).append(h)
        for found in groups.values():
            first = found[0]
            lines.append(f"value: {first['_text']} — {first['kind']}, {len(found)} place(s) in "
                         f"{len(by_file(found))} file(s), first {first['file']}:{first['line']}")
    return lines


def exclusion_lines(cat, skipped=None):
    lines = []
    for s in cat.sources:
        c = s["counts"]
        if s["status"] == "read" and "tabs" in c:
            listed = ("everything counts (--strict)" if cat.strict else f"listed at {s['listed']}" if s.get("listed")
                      else "no commit under Listed at, so everything counts")
            lines.append(f"source: {s['name']} — read; {c['tabs']} tab(s), {c['text']} text values, {c['amounts']} amounts; "
                         f"not matched: {c['column names']} column names (each tab's first row), {c['dates']} dates, "
                         f"{c['excluded']} stop-word or allowed cells; {listed}")
        elif s["status"] == "read":
            lines.append(f"source: {s['name']} — {c.get('text', 0)} text keys, {c.get('amounts', 0)} amount keys")
        else:
            lines.append(f"source: {s['name']} — {s['status']}")
    lines.append("not matched: a whole amount unless written as money (15.00, $15); a bare year 1900-2099 as cents")
    lines.append(f"stop-words ({len(STOPWORDS)}): " + " ".join(sorted(STOPWORDS)))
    lines.append("allowed by the owner (" + str(len(cat.allowed)) + ")" + (": " + "; ".join(cat.allowed) if cat.allowed else ""))
    for reason, n in sorted((skipped or {}).items()):
        lines.append(f"matched and not counted: {n} — {reason}")
    if cat.skipped:
        lines.append(f"not read as text, so not matched: {cat.skipped} file(s) or blob(s) (binary, or over {MAX_BYTES // (1024 * 1024)} MB); "
                     "a byte-for-byte copy of a source among them is a problem line")
    return lines


def by_file(hits):
    out = {}
    for h in hits:
        out.setdefault(h["file"], []).append(h)
    return out


def public(hits):
    return [{k: v for k, v in h.items() if k != "key" and not k.startswith("_")} for h in hits]


# ---- replacement maps --------------------------------------------------------------

def invent_amount(cents, taken):
    """Another amount of the same length and roundness that no source holds."""
    digits = len(str(cents))
    lo, hi = 10 ** (digits - 1), 10 ** digits
    step = 100 if cents % 100 == 0 else 10 if cents % 10 == 0 else 1
    lo = max(lo, step)
    span = max(1, (hi - lo) // step)
    for k in range(1, span + 1):
        cand = lo + (((cents - lo) // step + k * 7919) % span) * step
        if step == 10 and cand % 100 == 0:
            cand += 10
        if step == 1 and cand % 10 == 0:
            cand += 1
        if lo <= cand < hi and cand not in taken:
            taken.add(cand)
            return cand
    return cents + step


def build_map(cat, hits):
    """{"text": {words: replacement}, "amount": {cents: replacement cents}}
    for the values the hits name."""
    text_keys = sorted({h["key"][1] for h in hits if h["key"][0] in ("text", "word")})
    amount_keys = sorted({h["key"][1] for h in hits if h["key"][0] == "amount"})
    known = {w for entries in cat.phrases.values() for phrase, _ in entries for w in phrase}
    names = (n + s for s in SUFFIXES for n in NAMES)
    out = {"version": 1, "text": {}, "amount": {}}
    for key in text_keys:
        for cand in names:
            if fold(cand) not in known:
                out["text"][key] = cand
                break
        else:
            out["text"][key] = f"Example{len(out['text']) + 1}"
    taken = set(cat.amounts)
    for cents in amount_keys:
        out["amount"][str(cents)] = invent_amount(cents, taken)
    return out


def shaped(replacement, original):
    if original.isupper() and len(original) > 1:
        return replacement.upper()
    if original.islower():
        return replacement.lower()
    return replacement


def amount_text(original, new_cents, form):
    if form == "cents":
        return str(new_cents)
    if form == "units":
        return str(new_cents // 100)
    sep = "," if re.search(r",\d{1,2}$", original) else "."
    if form == "tenth":
        return f"{new_cents // 100}{sep}{(new_cents % 100) // 10}"
    return f"{new_cents // 100}{sep}{new_cents % 100:02d}"


def apply_text(cat, data, text):
    """(new text, replacements made)."""
    count, last = 0, len(text) + 1
    for start, end, kind, _, key in reversed(cat.find(text)):
        if end > last:
            continue  # overlaps the replacement to its right
        if kind in ("text", "word"):
            new = shaped(data["text"][key[1]], text[start:end])
        else:
            new = amount_text(text[start:end], int(data["amount"][str(key[1])]), key[2])
        text, last, count = text[:start] + new + text[end:], start, count + 1
    return text, count


def rename_if_hit(cat, data, full):
    """A file or directory whose own name holds a value is renamed with the
    same map (a value in a path survives every content rewrite otherwise)."""
    name = os.path.basename(full)
    new, count = apply_text(cat, data, name)
    if not count or new == name or not new.strip():
        return 0
    target = os.path.join(os.path.dirname(full), new)
    if os.path.exists(target):
        return 0
    os.rename(full, target)
    return 1


def inside_work_tree(path):
    """The git root the path's real destination lies in, symlinks resolved
    on the path and on its parents, or None."""
    d = os.path.dirname(os.path.realpath(path)) or "."
    while not os.path.isdir(d) and os.path.dirname(d) != d:
        d = os.path.dirname(d)
    return repo_root(d)


def private_file(path):
    """Open a file for writing that only this user can read, created with
    mode 0600 before a byte is written, never through a symlink."""
    if os.path.islink(path):
        raise SystemExit(f"refused: {path} is a symbolic link")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        os.chmod(path, 0o600)
    except OSError as e:
        os.close(fd)
        raise SystemExit(f"refused: cannot make {path} private: {e}")
    return os.fdopen(fd, "w", encoding="utf-8", newline="")


# ---- commands ------------------------------------------------------------------------

def project_of(planning, given=None):
    """The project a planning directory belongs to: as given, else its git
    root, else the working directory when the planning directory is in it."""
    if given:
        return os.path.abspath(given)
    root = repo_root(planning) if planning else None
    if root:
        return root
    cwd = os.getcwd()
    if planning and not os.path.relpath(planning, cwd).startswith(".."):
        return cwd
    return None


def cmd_scan(a):
    planning = os.path.abspath(a.planning) if a.planning else None
    project = project_of(planning, a.project)
    if a.map:
        cat, _ = from_map(a.map)
    else:
        cat = load(planning, project, strict=a.strict) if planning else None
        if cat is None:
            print(f"sources: no sources.md under {a.planning}; nothing to scan for")
            return 2
    if a.history:
        hits, n = scan_history(cat, project or planning, a.history)
        scope = f"{n} commit(s) in {a.history}"
    else:
        hits, n = scan_tree(cat, project, planning, a.files)
        scope = f"{n} file(s)"
    for extra in a.also or []:
        text = read_text(extra)
        if text is None:
            cat.problems.append(f"--also file not readable: {extra}")
        else:
            hits += scan_text(cat, text, extra)
            scope += f", {os.path.basename(extra)}"
    hits, not_counted = cat.judge(hits)
    for line in exclusion_lines(cat, not_counted):
        print(line)
    for line in hit_lines(hits, show=a.show):
        print(line)
    for p in cat.problems:
        print("problem:", p)
    passed = not hits and not cat.problems
    files = by_file(hits)
    print(f"sources: {'PASS' if passed else 'FAIL'} — {len(hits)} hit(s) in {len(files)} place(s) over {scope}"
          + (f"; {len(cat.problems)} problem(s)" if cat.problems else ""))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"passed": passed, "hits": public(hits), "problems": cat.problems,
                       "sources": [{k: v for k, v in s.items() if k != "path"} for s in cat.sources]}, f, indent=2)
    return 0 if passed else 1


def cmd_describe(a):
    path = os.path.abspath(os.path.expanduser(a.path))
    if not path.lower().endswith(READABLE):
        print(f"{os.path.basename(path)}: not a kind this script reads ({', '.join(READABLE)}); list it in sources.md as it is")
        return 1
    tabs = read_source(path)
    rng = parse_range(a.range)
    if a.tab is not None and a.tab not in tabs and not (a.tab in ("all", "") and len(tabs) >= 1):
        print(f"no tab named {a.tab!r}; tabs: {', '.join(repr(t) for t in tabs)}")
        return 1
    chosen = {t: c for t, c in tabs.items() if a.tab in (None, "all", "") or t == a.tab}
    print(f"{os.path.basename(path)}: {len(tabs)} tab(s)" + (f", describing {len(chosen)}" if len(chosen) != len(tabs) else ""))
    for tab, cells in chosen.items():
        if rng:
            cells = [c for c in cells if rng[1] <= c[0] <= rng[3] and rng[0] <= c[1] <= rng[2]]
        head = header_row(cells)
        rows = sorted({r for r, _, _, _ in cells if r != head})
        names = {c: str(v) for r, c, k, v in cells if r == head}
        print(f"tab {tab or '(the file)'}: {len(rows)} row(s) under the column names")
        for col in sorted({c for _, c, _, _ in cells}):
            kinds = {}
            for r, c, k, _ in cells:
                if c == col and r != head:
                    kinds[k] = kinds.get(k, 0) + 1
            name = names.get(col, "")
            name = name if name and len(name) <= 40 and cell_number(name) is None else "(no name)"
            print(f"  column {col_letter(col)} {name}: " + (", ".join(f"{n} {k}" for k, n in sorted(kinds.items())) or "empty"))
    if a.extract:
        if inside_work_tree(a.extract):
            print(f"refused: {a.extract} is inside a git work tree; a scratch copy of a source goes outside every repository")
            return 1
        with private_file(a.extract) as f:
            w = csv.writer(f)
            for tab, cells in chosen.items():
                if rng:
                    cells = [c for c in cells if rng[1] <= c[0] <= rng[3] and rng[0] <= c[1] <= rng[2]]
                grid = {}
                for r, c, _, v in cells:
                    grid.setdefault(r, {})[c] = v
                width = max((c for row in grid.values() for c in row), default=0)
                for r in sorted(grid):
                    w.writerow([grid[r].get(c, "") for c in range(1, width + 1)])
        print(f"extracted to {a.extract} (never print it; remove it when the document is written)")
    return 0


def cmd_map(a):
    planning = os.path.abspath(a.planning)
    project = project_of(planning, a.project)
    if inside_work_tree(a.out):
        print(f"refused: {a.out} is inside a git work tree; the map holds the values and lives outside every repository")
        return 1
    cat = load(planning, project)
    if cat is None:
        print(f"sources: no sources.md under {a.planning}")
        return 2
    hits, _ = scan_tree(cat, project, planning)
    commits = 0
    if a.history:
        more, commits = scan_history(cat, project, a.history)
        hits += more
    hits, _ = cat.judge(hits)
    data = build_map(cat, hits)
    with private_file(a.out) as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    for p in cat.problems:
        print("problem:", p)
    print(f"map: {len(data['text'])} text value(s) and {len(data['amount'])} amount(s) from {len(hits)} hit(s) in "
          f"{len(by_file(hits))} place(s)" + (f" over the tree and {commits} commit(s)" if a.history else " over the tree")
          + f"; written to {a.out}")
    return 1 if cat.problems else 0


def cmd_apply(a):
    cat, data = from_map(a.map)
    if a.stdin:
        raw = sys.stdin.buffer.read()
        text = decode(raw)
        if text is None:
            sys.stdout.buffer.write(raw)
            return 0
        new, _ = apply_text(cat, data, text)
        sys.stdout.buffer.write(new.encode("utf-8"))
        return 0
    total = files = renamed = 0
    for dirpath, dirnames, filenames in os.walk(a.tree, topdown=False):
        # Bottom-up, so a directory is renamed after everything in it.
        for name in filenames:
            full = os.path.join(dirpath, name)
            if os.path.islink(full):
                continue
            text = read_text(full)
            if text is not None:
                new, count = apply_text(cat, data, text)
                if count:
                    with open(full, "w", encoding="utf-8", newline="") as f:
                        f.write(new)
                    total, files = total + count, files + 1
            renamed += rename_if_hit(cat, data, full)
        for name in dirnames:
            if name != ".git":
                renamed += rename_if_hit(cat, data, os.path.join(dirpath, name))
    print(f"apply: {total} replacement(s) in {files} file(s); {renamed} path(s) renamed")
    return 0


def cmd_rewrite(a):
    project = os.path.abspath(a.project)
    mapfile = os.path.abspath(a.map)
    if inside_work_tree(mapfile):
        print(f"refused: {a.map} is inside a git work tree")
        return 1
    if (git(project, "status", "--porcelain") or "").strip():
        print("refused: the working tree is not clean; commit or set aside what is there first")
        return 1
    before = (git(project, "rev-list", "--count", a.range, check=True) or "0").strip()
    earlier_backups = (git(project, "for-each-ref", "--format=%(refname)", "refs/original/") or "").split()
    if earlier_backups:
        # filter-branch -f would delete these; without -f it refuses. Either
        # way they are someone's recovery points, so the owner moves them.
        print("refused: earlier backup refs exist under refs/original/ (" + ", ".join(earlier_backups)
              + "); the owner moves or drops them first, this script deletes none of them")
        return 1
    me = " ".join(shlex.quote(x) for x in (sys.executable, "-I", os.path.abspath(__file__), "apply", "--map", mapfile))
    env = dict(os.environ, FILTER_BRANCH_SQUELCH_WARNING="1")
    r = subprocess.run([find_git(), "-C", project, "filter-branch", "-f", "--tree-filter", me + " --tree . >/dev/null",
                        "--msg-filter", me + " --stdin", "--", a.range], capture_output=True, env=env)
    if r.returncode != 0:
        print("rewrite: git filter-branch failed:\n" + r.stderr.decode("utf-8", "replace")[-1500:])
        return 1
    for ref in (git(project, "for-each-ref", "--format=%(refname)", "refs/original/") or "").split():
        git(project, "update-ref", "-d", ref)  # only this rewrite's: none existed before (checked above)
    head = (git(project, "rev-parse", "--short", "HEAD") or "").strip()
    print(f"rewrite: {before} commit(s) in {a.range} rewritten; HEAD is now {head}")
    print("left as they are, for the owner to decide: the old commits in this clone's reflog (until `git reflog expire "
          "--expire=now --all && git gc --prune=now`), and every copy made before the rewrite (a remote that was "
          "pushed to, the session transcripts, the audit repository)")
    return 0


def main():
    p = argparse.ArgumentParser(description="Find the owner's source values where they could be committed; never print one.")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--planning")
    s.add_argument("--project")
    s.add_argument("--files", nargs="*")
    s.add_argument("--history", metavar="RANGE")
    s.add_argument("--map")
    s.add_argument("--also", action="append")
    s.add_argument("--strict", action="store_true", help="count every match: no listed-commit rule, no dense-amount rule")
    s.add_argument("--show", action="store_true", help="add the document's own text at each hit (for the owner's question; never save this output)")
    s.add_argument("--json")
    d = sub.add_parser("describe")
    d.add_argument("path")
    d.add_argument("--tab")
    d.add_argument("--range")
    d.add_argument("--extract", metavar="SCRATCH")
    m = sub.add_parser("map")
    m.add_argument("--planning", required=True)
    m.add_argument("--project")
    m.add_argument("--history", metavar="RANGE")
    m.add_argument("--out", required=True)
    ap = sub.add_parser("apply")
    ap.add_argument("--map", required=True)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--tree")
    group.add_argument("--stdin", action="store_true")
    rw = sub.add_parser("rewrite")
    rw.add_argument("--project", default=".")
    rw.add_argument("--map", required=True)
    rw.add_argument("--range", required=True)
    a = p.parse_args()
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if a.cmd == "scan" and not a.planning and not a.map:
        p.error("scan needs --planning (or --map)")
    return {"scan": cmd_scan, "describe": cmd_describe, "map": cmd_map, "apply": cmd_apply, "rewrite": cmd_rewrite}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
