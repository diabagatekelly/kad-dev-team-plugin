#!/usr/bin/env python3
"""The validation gate's scope check and the flow's own records, without a
model: the orchestrator's log and the rounds sidecar are appended to at
every step and committed outside the chunk, so a gate that no `--allow`
names them for must not fail scope on them, and a file that really is
outside the slice must still fail.

Usage: python3 -I evals/tools/validation_gate_test.py
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "skills", "orchestrator", "scripts", "validation_gate.py")

spec = importlib.util.spec_from_file_location("validation_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
sys.path.insert(0, os.path.dirname(SCRIPT))
spec.loader.exec_module(gate)


def git(cwd, *args):
    subprocess.run([gate.find_git(), "-C", cwd, *args], check=True, capture_output=True)


class ScopeAndTheFlowsRecords(unittest.TestCase):
    def test_the_log_and_the_sidecar_are_in_scope_without_an_allow(self):
        files = ["lending/cancel-hold.ts", "docs/cancel-hold/orchestrator-log.md",
                 "docs/cancel-hold/implementation/rounds-slice-001.jsonl", "planning/implementation/rounds-issue14.jsonl"]
        r = gate.check_scope(files[:3], ["lending/cancel-hold.ts"], planning="docs/cancel-hold")
        self.assertTrue(r["passed"], r)
        self.assertEqual(len(r["records"]), 2)
        r = gate.check_scope(files[3:], ["lending/"], planning="planning")
        self.assertTrue(r["passed"], r)

    def test_a_record_name_outside_the_target_directory_is_outside(self):
        for name in ("src/orchestrator-log.md", "orchestrator-log.md", "lib/rounds-slice-001.jsonl",
                     "docs/cancel-hold/implementation/orchestrator-log.md", "docs/other/orchestrator-log.md"):
            r = gate.check_scope([name], ["lending/"], planning="docs/cancel-hold")
            self.assertEqual(r["outside"], [name], name)
        self.assertEqual(gate.check_scope(["docs/orchestrator-log.md"], ["lending/"])["outside"], ["docs/orchestrator-log.md"])

    def test_a_file_outside_the_slice_still_fails(self):
        files = ["lending/cancel-hold.ts", "docs/cancel-hold/orchestrator-log.md", "utils/card-number.ts"]
        r = gate.check_scope(files, ["lending/cancel-hold.ts"], module_dirs=["lending/"], planning="docs/cancel-hold")
        self.assertFalse(r["passed"])
        self.assertEqual(r["outside"], ["utils/card-number.ts"])

    def test_a_name_that_only_resembles_a_record_is_outside(self):
        for name in ("docs/orchestrator-log.md.bak", "docs/my-orchestrator-log.md", "src/rounds.jsonl",
                     "src/rounds-slice-001.json", "docs/orchestrator-log.md/notes.txt"):
            r = gate.check_scope([name], ["lending/"], planning="docs")
            self.assertEqual(r["outside"], [name], name)

    def test_another_planning_document_is_not_a_record(self):
        r = gate.check_scope(["docs/cancel-hold/design-001.md"], ["lending/"], planning="docs/cancel-hold")
        self.assertEqual(r["outside"], ["docs/cancel-hold/design-001.md"])

    def test_an_absolute_path_inside_the_project_is_read_relative_to_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = os.path.join(tmp, "app")
            os.makedirs(os.path.join(project, "docs", "feature", "implementation"))
            rel = gate.project_relative
            self.assertEqual(rel(project, os.path.join(project, "docs", "feature", "implementation") + "/"), "docs/feature/implementation/")
            self.assertEqual(rel(project, os.path.join(project, "lending", "hold.py")), "lending/hold.py")
            self.assertEqual(rel(project, "lending/"), "lending/")
            self.assertEqual(rel(project, "lending\\hold.py"), "lending/hold.py")
            # outside the project it is left alone, and matches no changed file
            outside = os.path.join(tmp, "elsewhere") + "/"
            self.assertEqual(rel(project, outside), outside)
            self.assertEqual(rel(project, project + "/"), project + "/")

    def test_the_gate_takes_absolute_allow_module_dir_zone_and_protect(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            git(tmp, "init", "-q")
            git(tmp, "config", "user.name", "t")
            git(tmp, "config", "user.email", "t@example.test")
            git(tmp, "config", "commit.gpgsign", "false")
            for d in ("lending", "main", os.path.join("docs", "feature", "implementation")):
                os.makedirs(os.path.join(tmp, d))
            design = os.path.join(tmp, "docs", "feature", "design.md")
            for path, text in ((os.path.join(tmp, "lending", "hold.py"), "A = 1\n"), (design, "# Design\n")):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
            git(tmp, "add", "-A")
            git(tmp, "commit", "-qm", "base")
            records = os.path.join(tmp, "docs", "feature", "implementation")
            for path, text in ((os.path.join(tmp, "lending", "hold.py"), "A = 2\n"), (os.path.join(tmp, "lending", "queue.py"), "B = 1\n"),
                               (os.path.join(tmp, "main", "wiring.py"), "C = 1\n"), (os.path.join(records, "chunk-1-r0-review.md"), "# Review\n")):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
            out = os.path.join(tempfile.gettempdir(), f"kad-gate-abs-test-{os.getpid()}.json")

            def run(*extra):
                r = subprocess.run([sys.executable, "-I", SCRIPT, "--project", tmp, "--base", "HEAD", "--test-cmd", "true",
                                    "--allow", os.path.join(tmp, "lending", "hold.py"), "--allow", records + "/",
                                    "--module-dir", os.path.join(tmp, "lending") + "/", "--deviation-zone", os.path.join(tmp, "main") + "/",
                                    "--protect", design, "--planning", os.path.join(tmp, "docs", "feature"), "--json", out, *extra],
                                   capture_output=True, text=True)
                with open(out, encoding="utf-8") as f:
                    return r, json.load(f)["checks"]

            try:
                r, checks = run()
                # the records directory, handed absolute, is in scope; the module and the zone are deviations
                self.assertTrue(checks["scope"]["passed"], r.stdout)
                self.assertEqual(checks["scope"]["outside"], [])
                self.assertEqual(sorted(checks["scope"]["deviations"]), ["lending/queue.py", "main/wiring.py"])
                self.assertTrue(checks["protected"]["passed"], r.stdout)
                # and a protected document named by its absolute path still fails when it changes
                with open(design, "a", encoding="utf-8") as f:
                    f.write("An edit.\n")
                r, checks = run("--allow", design)
                self.assertFalse(checks["protected"]["passed"], r.stdout)
            finally:
                if os.path.exists(out):
                    os.remove(out)

    def test_the_whole_gate_passes_on_a_dirty_log_and_fails_on_a_stray_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            git(tmp, "init", "-q")
            git(tmp, "config", "user.name", "t")
            git(tmp, "config", "user.email", "t@example.test")
            git(tmp, "config", "commit.gpgsign", "false")
            os.makedirs(os.path.join(tmp, "lending"))
            os.makedirs(os.path.join(tmp, "docs", "feature", "implementation"))
            log = os.path.join(tmp, "docs", "feature", "orchestrator-log.md")
            sidecar = os.path.join(tmp, "docs", "feature", "implementation", "rounds-slice-001.jsonl")
            for path, text in ((os.path.join(tmp, "lending", "hold.py"), "A = 1\n"), (log, "# Log\n"), (sidecar, "")):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
            git(tmp, "add", "-A")
            git(tmp, "commit", "-qm", "base")
            with open(os.path.join(tmp, "lending", "hold.py"), "a", encoding="utf-8") as f:
                f.write("B = 2\n")
            with open(log, "a", encoding="utf-8") as f:
                f.write("- **C. Chunk 1/3:** a line the orchestrator appended\n")
            with open(sidecar, "a", encoding="utf-8") as f:
                f.write("{}\n")

            def run(out):
                r = subprocess.run([sys.executable, "-I", SCRIPT, "--project", tmp, "--base", "HEAD", "--test-cmd", "true",
                                    "--allow", "lending/hold.py", "--planning", os.path.join(tmp, "docs", "feature"), "--json", out], capture_output=True, text=True)
                with open(out, encoding="utf-8") as f:
                    return r, json.load(f)["checks"]["scope"]

            out = os.path.join(tempfile.gettempdir(), f"kad-gate-test-{os.getpid()}.json")
            try:
                r, scope = run(out)
                self.assertTrue(scope["passed"], r.stdout)
                self.assertIn("PASS  scope", r.stdout)
                with open(os.path.join(tmp, "stray.py"), "w", encoding="utf-8") as f:
                    f.write("C = 3\n")
                r, scope = run(out)
                self.assertFalse(scope["passed"], r.stdout)
                self.assertEqual(scope["outside"], ["stray.py"])
                self.assertEqual(r.returncode, 1)
            finally:
                if os.path.exists(out):
                    os.remove(out)


class ATestAFixRenamed(unittest.TestCase):
    """The plan's test names, read with the renames a fix declared."""

    def plan(self, fixes=""):
        d = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, d, True)
        path = os.path.join(d, "implementation-report.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Implementation\n\n### Chunk 1: cancel a hold\n\n"
                    '- **Done when**: "refuses a hold that is not mine" and seam "cancels my hold and frees the copy" pass\n'
                    "- **Commit**: abc1234\n" + fixes + "\n### Chunk 2: the list\n\n- **Done when**: \"lists my holds\" passes\n")
        return path

    def test_without_a_rename_the_plans_names_stand(self):
        self.assertEqual(gate.done_when_tests(self.plan(), 1), ["refuses a hold that is not mine", "cancels my hold and frees the copy"])

    def test_a_declared_rename_is_the_name_the_gate_looks_for(self):
        # the fix changed what the test checks; left under its old title the next review faulted the name
        fixes = ('- **Fix r1**: def5678; the refusal now names the member; renamed test "refuses a hold that is not mine" → '
                 '"refuses a hold that is not mine and names its member"\n')
        self.assertEqual(gate.done_when_tests(self.plan(fixes), 1),
                         ["refuses a hold that is not mine and names its member", "cancels my hold and frees the copy"])

    def test_two_renames_of_one_test_follow_each_other_and_an_ascii_arrow_reads(self):
        fixes = ('- **Fix r1**: def5678; renamed test "refuses a hold that is not mine" -> "refuses another member\'s hold"\n'
                 '- **Fix r2**: 0a1b2c3; renamed test "refuses another member\'s hold" → "refuses another member\'s hold with 403"\n')
        self.assertEqual(gate.done_when_tests(self.plan(fixes), 1)[0], "refuses another member's hold with 403")
        self.assertEqual(gate.done_when_tests(self.plan(fixes), 2), ["lists my holds"])


    def two_sections(self, chunk_1_fixes="", chunk_2_fixes=""):
        """The report as a real one stands: a plan section per chunk, then a
        report section per chunk under the same number, where the Fix lines go."""
        d = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, d, True)
        path = os.path.join(d, "implementation-report.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Implementation\n\n## Chunk plan\n\n### Chunk 1\n\n"
                    '- **Done when**: "lists my holds" and seam "cancels my hold" pass\n\n'
                    '### Chunk 2\n\n- **Done when**: "lists my holds" and "sorts them by date" pass\n\n'
                    "### Chunk 1: cancel a hold\n\n- **Commit**: abc1234\n" + chunk_1_fixes
                    + "\n### Chunk 2: the list\n\n- **Commit**: def5678\n" + chunk_2_fixes)
        return path

    def test_a_rename_is_read_from_the_chunks_report_section_too(self):
        fixes = '- **Fix r0**: this commit; renamed test "cancels my hold" → "cancels my hold and frees the copy"\n'
        self.assertEqual(gate.done_when_tests(self.two_sections(fixes), 1), ["lists my holds", "cancels my hold and frees the copy"])

    def test_another_chunks_rename_of_the_same_name_is_not_this_chunks(self):
        # S5 (deferred from the external review of #67): the map was read from the whole report, so chunk 2's
        # rename of a title both chunks quote sent chunk 1's gate looking for chunk 2's new name
        one = '- **Fix r0**: this commit; renamed test "lists my holds" → "lists my holds, newest first"\n'
        two = '- **Fix r0**: this commit; renamed test "lists my holds" → "lists my holds by date"\n'
        report = self.two_sections(one, two)
        self.assertEqual(gate.done_when_tests(report, 1)[0], "lists my holds, newest first")
        self.assertEqual(gate.done_when_tests(report, 2)[0], "lists my holds by date")

    def test_a_rename_declared_under_another_chunk_applies_when_this_chunk_declares_none(self):
        # a slice-level fixer writes its Fix line under the last chunk it touched
        two = '- **Fix r1**: this commit; renamed test "cancels my hold" → "cancels my hold and says so"\n'
        self.assertEqual(gate.done_when_tests(self.two_sections("", two), 1)[1], "cancels my hold and says so")


class TheCaptureFiles(unittest.TestCase):
    def test_only_the_captures_two_files_are_exempt_from_coverage(self):
        # the loop's own capture fixer writes screens/states.mjs at delivery, and no test can load it;
        # anything else under screens/ is code a test can load (S5, deferred from the external review of #67)
        self.assertTrue(gate.capture_file("screens/states.mjs"))
        self.assertTrue(gate.capture_file("screens/capture.mjs"))
        self.assertFalse(gate.capture_file("screens/format-amount.mjs"))
        self.assertFalse(gate.capture_file("screens/lib/states.mjs"))
        self.assertFalse(gate.capture_file("src/screens/list.ts"))
        self.assertFalse(gate.capture_file("src/web/server.ts"))


def tool_use(i, name, **inp):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": f"t{i}", "name": name, "input": inp}]}}


def tool_result(i, text, error=False):
    return {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": f"t{i}", "content": text, "is_error": error}]}}


DENIED = ("Permission for this action was denied by the Claude Code auto mode classifier. Reason: [Undermining Oversight]. "
          "If you have other tasks that don't depend on this action, continue working on those.")


class TheShellEditCount(unittest.TestCase):
    """S3 (the slice 4 review, F7). A chunk's builder commits four files; a
    gate fixer then commits one. The fix gate replays the fixer's
    transcript over the same base: the builder's files are not the
    fixer's shell edits, and a shell write the permission classifier
    refused never happened."""

    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)
        git(self.tmp, "init", "-q")
        git(self.tmp, "config", "user.name", "t")
        git(self.tmp, "config", "user.email", "t@example.test")
        git(self.tmp, "config", "commit.gpgsign", "false")
        os.makedirs(os.path.join(self.tmp, "lending"))
        self.write("lending/hold.py", "A = 1\n")
        self.base = self.commit("base")
        for name in ("lending/hold.py", "lending/queue.py", "lending/copy.py", "lending/member.py"):
            self.write(name, "B = 2\n")
        self.build = self.commit("the build")
        self.write("lending/test_hold.py", "def test_hold(): pass\n")
        self.fix = self.commit("the gate fix")

    def write(self, rel, text):
        with open(os.path.join(self.tmp, rel), "w", encoding="utf-8") as f:
            f.write(text)

    def commit(self, message):
        git(self.tmp, "add", "-A")
        git(self.tmp, "commit", "-qm", message)
        return subprocess.run([gate.find_git(), "-C", self.tmp, "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()

    def transcript(self, rows):
        path = os.path.join(self.tmp, "agent.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
        return path

    def fixer_rows(self, edited=True):
        rows = []
        if edited:
            rows += [tool_use(1, "Edit", file_path=os.path.join(self.tmp, "lending", "test_hold.py"), old_string="x", new_string="y"),
                     tool_result(1, "The file has been updated.")]
        rows += [tool_use(2, "Bash", command='git add lending/test_hold.py && git commit -q -m "Register the test" && git rev-parse --short HEAD'),
                 tool_result(2, self.fix + "\n M planning/orchestrator-log.md"),
                 {"type": "assistant", "message": {"content": [{"type": "text", "text": f"Commit {self.fix}; shell edits 0."}]}}]
        return rows

    def test_a_fix_gate_counts_the_fixers_own_commits_not_the_builders_files(self):
        c = gate.check_transcript(self.tmp, self.transcript(self.fixer_rows()), self.base, "true")
        self.assertEqual(c["catch_all"], [])
        self.assertEqual(c["shell_edits"], 0)

    def test_a_file_of_the_agents_own_commit_that_no_edit_names_is_still_counted(self):
        c = gate.check_transcript(self.tmp, self.transcript(self.fixer_rows(edited=False)), self.base, "true")
        self.assertEqual(c["catch_all"], ["lending/test_hold.py"])
        self.assertEqual(c["shell_edits"], 1)
        self.assertIn("INFO  shell edit: lending/test_hold.py (changed in the agent's commits with no Edit or Write naming it)",
                      gate.transcript_lines(c))

    def test_a_transcript_that_names_no_commit_is_read_over_the_whole_range_as_before(self):
        rows = [tool_use(1, "Bash", command="echo hello"), tool_result(1, "hello")]
        c = gate.check_transcript(self.tmp, self.transcript(rows), self.base, "true")
        self.assertEqual(len(c["catch_all"]), 5)
        self.assertIn("INFO  shell edit: lending/copy.py (changed in the range with no Edit or Write naming it)", gate.transcript_lines(c))

    def test_a_shell_write_the_classifier_refused_is_not_counted_and_one_that_ran_is(self):
        rows = self.fixer_rows() + [
            tool_use(3, "Bash", command="cp lending/hold.py /tmp/x && sed -i '' 's/A/B/' lending/hold.py"), tool_result(3, DENIED, error=True),
            tool_use(4, "Bash", command="cat >> lending/test_hold.py <<'E'\nx = 1\nE"), tool_result(4, DENIED, error=True),
            tool_use(5, "Bash", command="sed -i '' 's/B/C/' lending/queue.py"), tool_result(5, ""),
        ]
        c = gate.check_transcript(self.tmp, self.transcript(rows), self.base, "true")
        self.assertEqual([rel for rel, _ in c["edits"]], ["lending/queue.py"])
        self.assertEqual(c["shell_edits"], 1)
        self.assertEqual(c["denied"], 2)
        self.assertIn("INFO  transcript: 2 shell write(s) refused by a permission check, not counted", gate.transcript_lines(c))


class TheFailingTestsName(unittest.TestCase):
    """S4 (the slice 4 review, F16): `suite exit 1, summary fail count 1`
    cost two full suite runs to learn which test."""

    NODE = ("✔ lists my holds (1.2ms)\n✖ refuses a hold that is not mine (3.4ms)\n✖ seam \"cancels my hold\" (12ms)\n"
            "ℹ tests 3\nℹ pass 1\nℹ fail 2\n\n✖ failing tests:\n\ntest at test/hold.test.ts:4:1\n"
            "✖ refuses a hold that is not mine (3.4ms)\n  AssertionError\n")

    def test_the_names_are_read_once_each_from_the_runners_output(self):
        self.assertEqual(gate.failing_tests(self.NODE), ["refuses a hold that is not mine", 'seam "cancels my hold"'])
        self.assertEqual(gate.failing_tests("not ok 3 - refuses a hold # TODO\nFAILED tests/test_hold.py::test_refuses\n"),
                         ["refuses a hold", "tests/test_hold.py::test_refuses"])
        self.assertEqual(gate.failing_tests("ℹ fail 0\n"), [])

    def test_the_gates_suite_line_names_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            git(tmp, "init", "-q")
            git(tmp, "config", "user.name", "t")
            git(tmp, "config", "user.email", "t@example.test")
            git(tmp, "config", "commit.gpgsign", "false")
            with open(os.path.join(tmp, "out.txt"), "w", encoding="utf-8") as f:
                f.write(self.NODE)
            with open(os.path.join(tmp, "run.py"), "w", encoding="utf-8") as f:
                f.write("import sys\nsys.stdout.reconfigure(encoding='utf-8')\nprint(open('out.txt', encoding='utf-8').read())\nsys.exit(1)\n")
            git(tmp, "add", "-A")
            git(tmp, "commit", "-qm", "base")
            with open(os.path.join(tmp, "hold.py"), "w", encoding="utf-8") as f:
                f.write("A = 1\n")
            r = subprocess.run([sys.executable, "-I", SCRIPT, "--project", tmp, "--base", "HEAD", "--test-cmd", f"{sys.executable} run.py"],
                               capture_output=True, text=True)
            self.assertIn('FAIL  suite exit 1, summary fail count 2; failing: "refuses a hold that is not mine"; "seam \\"cancels my hold\\""',
                          r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
