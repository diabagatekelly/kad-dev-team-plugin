"""The source scan, its two gates and the rule's wording, without a model.

Every value here is invented: the "sheet" is
`evals/fixtures/library-app/source-plants/desk-fees.csv`, seven made-up
fee rows.

 1. `describe` prints the shape of a source and none of its cells;
 2. a text cell, an amount in each of its forms and a camelCase identifier
    are found, as file, line and cell, and the output never holds a value;
 3. a whole amount is found only where written as money; a date and a
    column name are never matched;
 4. the owner's allowed line takes a value out; the stop-words are printed;
 5. a listed source that cannot be read fails; no `sources.md` is exit 2;
 6. a workbook is read with the standard library: shared and inline
    strings, numbers, a date-styled cell left out;
 7. a value already in the tree at the `Listed at` commit is not counted,
    a new one is, and `--strict` counts both;
 8. an amount alone in a dense source is not counted, and is beside a text
    value from its own row;
 9. `--history` finds a value in an earlier commit and in a message when
    the tree is clean;
10. `map` and `--extract` refuse a path inside a work tree; `map`,
    `rewrite` and the checks after it leave no value in any commit, with
    an amount replaced the same way in every form;
11. the readiness gate's tenth check and the chunk gate's `sources` check
    fail on a planted value, route to the owner, and print none;
12. the transcript scan decodes JSON strings before matching;
13. the five planning skills carry the rule in the same words;
14. a value wrapped over a line break is found and one split by a blank
    line is not; a relative location resolves outside a repository, where
    the working directory is the project;
15. a value in a path is found in history and renamed by the rewrite,
    which is refused while earlier backup refs exist;
16. a UTF-16 export is read; a byte-for-byte copy of a source in the tree
    is a problem, and so is a listed source git would commit, in a history
    scan too;
17. the map and an extract are created with mode 0600 and never through a
    symlink;
18. a transcript's keys and numbers are scanned, and one that cannot be
    read is not reported clean;
19. a word of a longer cell (a surname) counts beside an amount of its own
    row and not alone, not beside another row's amount, and not when it is
    a word of many rows.

Usage: python3 -I evals/tools/source_scan_test.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(ROOT, "skills", "orchestrator", "scripts")
SCAN = os.path.join(SCRIPTS, "source_scan.py")
SHEET = os.path.join(ROOT, "evals", "fixtures", "library-app", "source-plants", "desk-fees.csv")
VALUES = ["Odalys", "Brennecke", "Tavish", "Quennell", "Vantongeren", "Marchetti", "Nkemelu", "Salt Road", "Skelder Harbour Lights",
          "Winter Bees of Thrupp", "Tidewater", "7.35", "12.80", "18.60", "RKV", "LC-204417"]
RULE_SKILLS = ["requirements-refinement", "vertical-slicing", "acceptance-criteria", "screen-design", "architecture-design"]
RULE_START = "**A file the owner provides is described, never quoted.**"
RULE_END = "chunk gate run the same scan."


def run(*args, cwd=None):
    return subprocess.run([sys.executable, "-I", SCAN, *args], capture_output=True, text=True, cwd=cwd)


def git(cwd, *args):
    r = subprocess.run(["git", "-C", cwd, "-c", "user.email=t@example.com", "-c", "user.name=t", *args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(f"git {' '.join(args)}: {r.stderr}")
    return r.stdout.strip()


class SourceScan(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.owner = os.path.join(self.tmp, "owner")
        self.project = os.path.join(self.tmp, "project")
        self.planning = os.path.join(self.project, "planning")
        os.makedirs(self.owner)
        os.makedirs(os.path.join(self.project, "test"))
        os.makedirs(self.planning)
        self.sheet = os.path.join(self.owner, "desk-fees.csv")
        shutil.copy(SHEET, self.sheet)
        git(self.project, "init", "-q", "-b", "main", ".")

    def sources(self, location=None, listed="—", allowed=()):
        with open(os.path.join(self.planning, "sources.md"), "w", encoding="utf-8") as f:
            f.write("# Sources\n\n| Source | Location | Tab or range | Read on | Listed at |\n|---|---|---|---|---|\n"
                    f"| desk fees | `{location or self.sheet}` | all | 2026-11-09 | {listed} |\n\n## Allowed by the owner\n\n")
            for a in allowed:
                f.write(f"- `{a}` — \"that is ours\" (2026-11-09)\n")

    def write(self, rel, text):
        full = os.path.join(self.project, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)

    def commit(self, message):
        git(self.project, "add", "-A")
        git(self.project, "commit", "-q", "-m", message)
        return git(self.project, "rev-parse", "--short", "HEAD")

    def scan(self, *args):
        return run("scan", "--planning", self.planning, *args, cwd=self.project)

    def assertNoValue(self, text):
        for v in VALUES:
            self.assertNotIn(v.lower(), text.lower(), f"a value of the sheet is printed: {v}")

    def test_01_describe_prints_the_shape_and_no_cell(self):
        r = run("describe", self.sheet)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("7 row(s)", r.stdout)
        for name in ("card_number", "member", "title", "fee", "paid_on", "collected_by"):
            self.assertIn(name, r.stdout)
        self.assertIn("7 number", r.stdout)
        self.assertNoValue(r.stdout)

    def test_02_text_amount_forms_and_identifiers_are_found_and_never_printed(self):
        self.sources()
        self.write("planning/slice-001.md", "# Slice\n\n- Given Odalys Brennecke owes 7.35, when she pays, then it is paid.\n")
        self.write("test/fee.test.ts", "const rkvTotal = 735;\nconst other = '12,80';\ntest('charges TAVISH_QUENNELL_ODUYA', () => {});\n")
        r = self.scan()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertRegex(r.stdout, r"hit: planning/slice-001\.md:3 col \d+-\d+ — text, desk fees B2")
        self.assertRegex(r.stdout, r"hit: planning/slice-001\.md:3 col \d+-\d+ — amount, desk fees D2")
        self.assertRegex(r.stdout, r"hit: test/fee\.test\.ts:1 col 7-9 — text, desk fees F2")
        self.assertRegex(r.stdout, r"hit: test/fee\.test\.ts:1 col \d+-\d+ — amount, desk fees D2")
        self.assertRegex(r.stdout, r"hit: test/fee\.test\.ts:2 col \d+-\d+ — amount, desk fees D3")
        self.assertRegex(r.stdout, r"hit: test/fee\.test\.ts:3 col \d+-\d+ — text, desk fees B3")
        self.assertIn("sources: FAIL — 6 hit(s) in 2 place(s)", r.stdout)
        self.assertNoValue(r.stdout)
        shown = self.scan("--show")
        self.assertIn("written there as: Odalys Brennecke", shown.stdout)
        self.assertIn("value: 7.35 — amount", shown.stdout)

    def test_03_whole_amounts_dates_and_column_names(self):
        self.sources()
        self.write("planning/a.md", "A fee of 24 on title 7 takes 2400 ms on 2026-08-04; the member and the fee and the title columns.\n")
        self.assertEqual(self.scan().returncode, 0)
        self.write("planning/a.md", "A fee of 24.00 is whole.\nOr $24 as money.\nOr 24 EUR.\n")
        r = self.scan()
        self.assertEqual(r.returncode, 1)
        self.assertEqual(len(re.findall(r"^hit: ", r.stdout, re.M)), 3, r.stdout)

    def test_04_allowed_by_the_owner_and_the_printed_stop_words(self):
        self.sources(allowed=["Winter Bees of Thrupp", "9.15"])
        self.write("planning/a.md", "Winter bees of Thrupp appear in winter, at 9.15 a jar.\n")
        r = self.scan()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("allowed by the owner (2): Winter Bees of Thrupp; 9.15", r.stdout)
        self.assertRegex(r.stdout, r"stop-words \(\d+\): a all an and")
        self.write("planning/a.md", "Skelder Harbour lights on the water.\n")
        self.assertEqual(self.scan().returncode, 1)

    def test_05_unreadable_source_fails_and_no_sources_is_exit_2(self):
        self.assertEqual(self.scan().returncode, 2)
        self.sources(location=os.path.join(self.owner, "gone.csv"))
        r = self.scan()
        self.assertEqual(r.returncode, 1)
        self.assertIn("problem: source not readable here: desk fees", r.stdout)
        self.sources(location=os.path.join(self.owner, "photo.png"))
        r = self.scan()
        self.assertEqual(r.returncode, 0)
        self.assertIn("not scannable", r.stdout)

    def workbook(self):
        path = os.path.join(self.owner, "fees.xlsx")
        ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("xl/workbook.xml", f'<workbook {ns} xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                       '<sheets><sheet name="Fees" sheetId="1" r:id="rId1"/></sheets></workbook>')
            z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                       '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
            z.writestr("xl/sharedStrings.xml", f'<sst {ns}><si><t>member</t></si><si><t>fee</t></si><si><t>paid</t></si>'
                       '<si><r><t>Zebedee </t></r><r><t>Quillfeather</t></r></si></sst>')
            z.writestr("xl/styles.xml", f'<styleSheet {ns}><cellXfs count="2"><xf numFmtId="0"/><xf numFmtId="14"/></cellXfs></styleSheet>')
            z.writestr("xl/worksheets/sheet1.xml", f'<worksheet {ns}><sheetData>'
                       '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c><c r="C1" t="s"><v>2</v></c></row>'
                       '<row r="2"><c r="A2" t="s"><v>3</v></c><c r="B2"><v>41.07</v></c><c r="C2" s="1"><v>46000</v></c></row>'
                       '<row r="3"><c r="A3" t="inlineStr"><is><t>Ottoline Farrowby</t></is></c><c r="B3"><v>16.5</v></c></row>'
                       '</sheetData></worksheet>')
        return path

    def test_06_a_workbook_is_read_with_the_standard_library(self):
        book = self.workbook()
        d = run("describe", book)
        self.assertEqual(d.returncode, 0, d.stderr)
        self.assertIn("tab Fees: 2 row(s)", d.stdout)
        self.assertIn("column C paid: 1 date", d.stdout)
        self.assertNotIn("Quillfeather", d.stdout)
        self.sources(location=book)
        self.write("planning/a.md", "Zebedee Quillfeather owes 41.07; Ottoline Farrowby 1650 cents; nothing on 46000.\n")
        r = self.scan()
        self.assertEqual(len(re.findall(r"^hit: ", r.stdout, re.M)), 4, r.stdout)
        self.assertIn("Fees!A2", r.stdout)
        self.assertIn("1 dates", r.stdout)

    def test_07_already_in_the_tree_when_listed_is_not_counted(self):
        self.write("planning/problem.md", "The desk closes at Skelder Harbour Lights.\n")
        listed = self.commit("before the sheet was listed")
        self.sources(listed=f"`{listed}`")
        self.write("planning/slice-001.md", "Skelder Harbour lights again, and Winter Bees of Thrupp.\n")
        r = self.scan()
        self.assertEqual(r.returncode, 1)
        self.assertEqual(len(re.findall(r"^hit: ", r.stdout, re.M)), 1, r.stdout)
        self.assertIn("matched and not counted: 2 — already in the tree when the source was listed", r.stdout)
        self.assertEqual(len(re.findall(r"^hit: ", self.scan("--strict").stdout, re.M)), 3)

    def test_08_an_amount_alone_in_a_dense_source(self):
        with open(self.sheet, "w", encoding="utf-8") as f:
            f.write("member,fee\n")
            for cents in range(100, 400):
                f.write(f"Member{cents},{cents / 100:.2f}\n")
            f.write("Quenby Ashgrove,5.17\n")
        self.sources()
        self.write("planning/a.md", "An invented fee of 5.17.\n")
        r = self.scan()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("matched and not counted: 1 — an amount alone", r.stdout)
        self.write("planning/a.md", "Quenby Ashgrove owes 5.17.\n")
        r = self.scan()
        self.assertEqual(len(re.findall(r"^hit: ", r.stdout, re.M)), 2, r.stdout)

    def test_09_history_finds_what_the_tree_no_longer_holds(self):
        self.sources()
        self.write("test/fee.test.ts", "const fee = 1860;\n")
        self.commit("the Vesk Tidewater Almanac fee")
        self.write("test/fee.test.ts", "const fee = 4410;\n")
        self.commit("an invented fee")
        self.assertEqual(self.scan().returncode, 0)
        r = self.scan("--history", "main")
        self.assertEqual(r.returncode, 1)
        self.assertRegex(r.stdout, r"hit: [0-9a-f]{7} \(message\):1 col \d+-\d+ — text, desk fees C8")
        self.assertRegex(r.stdout, r"hit: [0-9a-f]{7}:test/fee\.test\.ts:1 col \d+-\d+ — amount, desk fees D5")
        self.assertNoValue(r.stdout)

    def test_10_map_rewrite_and_the_checks_after_it(self):
        self.sources()
        self.write("planning/slice-001.md", "- Given Mirela Vantongeren owes 3.45, then 345 cents are due.\n")
        self.write("test/fee.test.ts", "test('charges mirela vantongeren 3,45', () => {});\n")
        self.commit("Chunk 1: the Mirela Vantongeren fee")
        self.write("test/other.test.ts", "const x = 1;\n")
        self.commit("Chunk 2")
        inside = run("map", "--planning", self.planning, "--history", "main", "--out", os.path.join(self.planning, "map.json"), cwd=self.project)
        self.assertEqual(inside.returncode, 1)
        self.assertIn("refused", inside.stdout)
        extract = run("describe", self.sheet, "--extract", os.path.join(self.project, "scratch.csv"))
        self.assertIn("refused", extract.stdout)
        mapfile = os.path.join(self.tmp, "map.json")
        m = run("map", "--planning", self.planning, "--history", "main", "--out", mapfile, cwd=self.project)
        self.assertEqual(m.returncode, 0, m.stdout + m.stderr)
        self.assertRegex(m.stdout, r"map: 1 text value\(s\) and 1 amount\(s\)")
        self.assertNoValue(m.stdout)
        rw = run("rewrite", "--project", self.project, "--map", mapfile, "--range", "main")
        self.assertEqual(rw.returncode, 0, rw.stdout + rw.stderr)
        self.assertIn("2 commit(s) in main rewritten", rw.stdout)
        self.assertNoValue(rw.stdout)
        after = run("scan", "--map", mapfile, "--project", self.project, "--history", "main", cwd=self.project)
        self.assertEqual(after.returncode, 0, after.stdout)
        self.assertIn("0 hit(s) in 0 place(s) over 2 commit(s)", after.stdout)
        self.assertEqual(self.scan("--history", "main").returncode, 0)
        for needle in ("Vantongeren", "3.45", "345", "3,45"):
            self.assertEqual(git(self.project, "log", "--all", "--oneline", f"-S{needle}", "main"), "", needle)
        with open(mapfile, encoding="utf-8") as f:
            new = int(json.load(f)["amount"]["345"])
        with open(os.path.join(self.planning, "slice-001.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn(f"{new // 100}.{new % 100:02d}", text)
        self.assertIn(f"{new} cents", text)
        with open(os.path.join(self.project, "test", "fee.test.ts"), encoding="utf-8") as f:
            self.assertIn(f"{new // 100},{new % 100:02d}", f.read())
        self.assertEqual(git(self.project, "for-each-ref", "refs/original/"), "")

    def test_11_the_two_gates(self):
        shutil.copytree(os.path.join(ROOT, "evals", "fixtures", "library-app", "route-plants", "cancel-hold"), self.planning, dirs_exist_ok=True)
        self.write("package.json", '{"scripts": {"test": "true"}}\n')
        base = self.commit("planning")
        ready = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "readiness_check.py"), "--planning", self.planning, "--slice", "001"],
                               capture_output=True, text=True)
        self.assertIn("PASS  no-source-values: no sources.md", ready.stdout)
        self.sources()
        self.write("test/fee.test.ts", "test('charges Ysolde Marchetti 9.15', () => {});\n")
        self.commit("Chunk 1")
        ready = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "readiness_check.py"), "--planning", self.planning, "--slice", "001"],
                               capture_output=True, text=True)
        self.assertRegex(ready.stdout, r"FAIL  no-source-values: 2 place\(s\) in 1 file\(s\) hold a value of a listed source: test/fee\.test\.ts \(2\) -> the owner \(source values\)")
        self.assertIn("route: no-source-values -> the owner (source values)", ready.stdout)
        self.assertIn("INFO  no-source-values: stop-words", ready.stdout)
        self.assertNoValue(ready.stdout)
        gate = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "validation_gate.py"), "--project", self.project, "--base", base,
                               "--test-cmd", "true", "--allow", "test/", "--allow", "planning/", "--planning", self.planning],
                              capture_output=True, text=True)
        self.assertEqual(gate.returncode, 1, gate.stdout + gate.stderr)
        self.assertRegex(gate.stdout, r"FAIL  sources 2 place\(s\) in 1 changed file\(s\) hold a value of a listed source: test/fee\.test\.ts \(2\)")
        self.assertRegex(gate.stdout, r"hit: test/fee\.test\.ts:1 col \d+-\d+ — text, desk fees B6")
        self.assertNoValue(gate.stdout)
        self.write("test/fee.test.ts", "test('charges an invented member 4.40', () => {});\n")
        self.commit("Fix")
        gate = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "validation_gate.py"), "--project", self.project, "--base", base,
                               "--test-cmd", "true", "--allow", "test/", "--allow", "planning/", "--planning", self.planning],
                              capture_output=True, text=True)
        self.assertIn("PASS  sources no value of a listed source", gate.stdout)
        self.assertEqual(gate.returncode, 0, gate.stdout)
        shutil.rmtree(self.planning)
        self.commit("no planning")
        gate = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "validation_gate.py"), "--project", self.project, "--base", "HEAD~1",
                               "--test-cmd", "true"], capture_output=True, text=True)
        self.assertIn("SKIP  sources: no sources.md under planning", gate.stdout)

    def test_12_a_transcript_is_decoded_before_it_is_matched(self):
        self.sources()
        transcript = os.path.join(self.tmp, "agent.jsonl")
        with open(transcript, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "user", "message": {"content": [{"type": "tool_result", "content": "member,fee\nPer Lindqvist-Amara,18.60\n"}]}}) + "\n")
            f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "nothing here"}]}}) + "\n")
        sys.path.insert(0, SCRIPTS)
        import source_scan
        cat = source_scan.load(self.planning, self.project)
        hits, entries = source_scan.scan_transcript(cat, transcript)
        self.assertEqual((len(hits), entries), (2, 1))

    def test_14_a_value_wrapped_over_a_line_and_a_relative_location(self):
        plain = os.path.join(self.tmp, "plain")          # no repository: a planning stage's eval directory
        os.makedirs(os.path.join(plain, "docs", "x"))
        os.makedirs(os.path.join(plain, "owner-files"))
        shutil.copy(SHEET, os.path.join(plain, "owner-files", "desk-fees.csv"))
        with open(os.path.join(plain, "docs", "x", "sources.md"), "w", encoding="utf-8") as f:
            f.write("# Sources\n\n| Source | Location | Tab or range | Read on | Listed at |\n|---|---|---|---|---|\n"
                    "| desk fees | `owner-files/desk-fees.csv` | all | 2026-11-09 | — |\n")
        with open(os.path.join(plain, "docs", "x", "slice-001.md"), "w", encoding="utf-8") as f:
            f.write("She asks about The Quennock Salt\nRoad Atlas today.\n\nGlassmaking at\n\nHembry Forge is two paragraphs.\n")
        os.makedirs(os.path.join(plain, "test"))
        with open(os.path.join(plain, "test", "a.test.ts"), "w", encoding="utf-8") as f:
            f.write("const fee = 915;\n")
        r = run("scan", "--planning", "docs/x", cwd=plain)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertRegex(r.stdout, r"hit: docs/x/slice-001\.md:1 col 16 to line 2 col 10 — text, desk fees C2")
        self.assertRegex(r.stdout, r"hit: test/a\.test\.ts:1 col 13-15 — amount, desk fees D6")
        self.assertEqual(len(re.findall(r"^hit: ", r.stdout, re.M)), 2, r.stdout)
        self.assertNotIn("problem:", r.stdout)

    def test_15_paths_are_scanned_and_renamed_and_only_this_rewrites_backups_go(self):
        self.sources()
        self.write("test/bartholomew-nkemelu-fees.test.ts", "const x = 1;\n")
        self.commit("a test named after Nkemelu")
        r = self.scan("--history", "main")
        self.assertRegex(r.stdout, r"hit: [0-9a-f]{7}:test/bartholomew-nkemelu-fees\.test\.ts \(the path itself\)")
        mapfile = os.path.join(self.tmp, "map.json")
        run("map", "--planning", self.planning, "--history", "main", "--out", mapfile, cwd=self.project)
        rw = run("rewrite", "--project", self.project, "--map", mapfile, "--range", "main")
        self.assertEqual(rw.returncode, 0, rw.stdout + rw.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.project, "test", "bartholomew-nkemelu-fees.test.ts")))
        self.assertEqual(len([f for f in os.listdir(os.path.join(self.project, "test")) if f.endswith("-fees.test.ts")]), 1)
        self.assertEqual(self.scan("--history", "main").returncode, 0)
        self.assertEqual(git(self.project, "for-each-ref", "--format=%(refname)", "refs/original/"), "")
        git(self.project, "update-ref", "refs/original/refs/heads/keep-me", "HEAD")
        rw = run("rewrite", "--project", self.project, "--map", mapfile, "--range", "main")
        self.assertEqual(rw.returncode, 1)
        self.assertIn("refused: earlier backup refs exist", rw.stdout)
        self.assertEqual(git(self.project, "for-each-ref", "--format=%(refname)", "refs/original/"), "refs/original/refs/heads/keep-me")

    def test_16_utf16_source_and_a_copy_of_the_source_in_the_tree(self):
        with open(self.sheet, "rb") as f:
            raw = f.read()
        with open(self.sheet, "wb") as f:
            f.write(raw.decode("utf-8").encode("utf-16"))
        self.sources()
        self.write("planning/a.md", "Bartholomew Nkemelu again.\n")
        r = self.scan()
        self.assertRegex(r.stdout, r"hit: planning/a\.md:1 col 1-19 — text, desk fees B7")
        shutil.copy(self.sheet, os.path.join(self.project, "test", "export.bin"))
        r = self.scan()
        self.assertIn("problem: a copy of the source desk fees is in the repository as test/export.bin", r.stdout)
        self.assertIn("not read as text, so not matched: 1 file(s)", r.stdout)
        os.remove(os.path.join(self.project, "test", "export.bin"))
        inside = os.path.join(self.project, "owner-files")
        os.makedirs(inside)
        shutil.copy(self.sheet, os.path.join(inside, "desk-fees.csv"))
        self.sources(location="owner-files/desk-fees.csv")
        self.commit("the export committed by mistake")
        r = self.scan("--history", "main")
        self.assertIn("problem: source inside the repository and not ignored: owner-files/desk-fees.csv", r.stdout)
        self.assertEqual(r.returncode, 1)

    def test_17_outputs_are_private_and_never_through_a_symlink(self):
        self.sources()
        mapfile = os.path.join(self.tmp, "map.json")
        run("map", "--planning", self.planning, "--out", mapfile, cwd=self.project)
        self.assertEqual(oct(os.stat(mapfile).st_mode & 0o777), "0o600")
        link = os.path.join(self.tmp, "link.json")
        os.symlink(os.path.join(self.project, "inner.json"), link)
        r = run("map", "--planning", self.planning, "--out", link, cwd=self.project)
        self.assertEqual(r.returncode, 1)
        self.assertIn("refused", r.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.project, "inner.json")))
        extract = os.path.join(self.tmp, "rows.csv")
        run("describe", self.sheet, "--extract", extract)
        self.assertEqual(oct(os.stat(extract).st_mode & 0o777), "0o600")

    def test_18_transcript_keys_numbers_and_an_unreadable_one(self):
        self.sources()
        sys.path.insert(0, SCRIPTS)
        import source_scan
        cat = source_scan.load(self.planning, self.project)
        transcript = os.path.join(self.tmp, "t.jsonl")
        with open(transcript, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "user", "message": {"content": {"Odalys Brennecke": 7.35}}}) + "\n")
        hits, entries = source_scan.scan_transcript(cat, transcript)
        self.assertEqual((len(hits), entries), (2, 1))
        self.assertEqual(source_scan.scan_transcript(cat, os.path.join(self.tmp, "missing.jsonl")), (None, None))

    def test_19_a_word_of_a_longer_cell_counts_beside_its_row(self):
        self.sources()
        self.write("planning/a.md", "Vantongeren asked about her fine.\n")
        r = self.scan()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("matched and not counted: 1 — a word of a longer cell, with nothing else of its row in the file", r.stdout)
        self.write("planning/a.md", "Vantongeren asked about her 3.45 fine.\n")
        r = self.scan()
        self.assertRegex(r.stdout, r"hit: planning/a\.md:1 col 1-11 — word, desk fees B4")
        self.assertRegex(r.stdout, r"hit: planning/a\.md:1 col 29-32 — amount, desk fees D4")
        self.assertEqual(len(re.findall(r"^hit: ", r.stdout, re.M)), 2, r.stdout)
        self.write("planning/a.md", "Vantongeren owes 12.80 (another row's fee), and Brennecke's title is The Quennock Salt Road Atlas.\n")
        r = self.scan()
        self.assertEqual(len(re.findall(r"^hit: ", r.stdout, re.M)), 3, r.stdout)  # the title and Brennecke (row 2) and 12.80 (alone counts in a sparse sheet); not Vantongeren
        self.assertNotRegex(r.stdout, r"hit: [^\n]*— word, desk fees B4")
        with open(self.sheet, "a", encoding="utf-8") as f:
            for i in range(400):
                f.write(f"LC-3{i:05d},Card payment {i},Payment to desk,{(i % 90) + 1}.{(i * 7) % 100:02d},2026-11-01,TMD\n")
        self.write("planning/a.md", "A payment of 1.00 at the desk.\n")
        r = self.scan()
        self.assertEqual(r.returncode, 0, r.stdout)  # `payment` is a word of hundreds of rows: no pairing with an amount

    def test_13_the_five_planning_skills_carry_the_rule_in_the_same_words(self):
        blocks = {}
        for skill in RULE_SKILLS:
            with open(os.path.join(ROOT, "skills", skill, "SKILL.md"), encoding="utf-8") as f:
                text = f.read()
            self.assertEqual(text.count(RULE_START), 1, f"{skill}: the rule's first sentence, once")
            start = text.index(RULE_START)
            end = text.index(RULE_END, start) + len(RULE_END)
            blocks[skill] = text[start:end]
        first = blocks[RULE_SKILLS[0]]
        self.assertGreater(len(first), 800)
        for skill, block in blocks.items():
            self.assertEqual(block, first, f"{skill} words the rule differently from {RULE_SKILLS[0]}")


if __name__ == "__main__":
    unittest.main(verbosity=1)
