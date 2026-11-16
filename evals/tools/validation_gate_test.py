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


if __name__ == "__main__":
    unittest.main(verbosity=1)
