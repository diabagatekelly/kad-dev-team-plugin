"""The scratch launcher's refusals and its environment, without an app.

1. a data path that resolves inside the scratch folder: the command runs
   with HOME, TMPDIR and the variable inside the folder;
2. a `--env` path that resolves outside: refused, exit 3, nothing run;
3. a command argument naming a path under the real home directory
   outside the scratch folder and the project: refused, exit 3;
4. `--hash` is stable over the same files and changes when one changes;
5. `--clean` removes only a folder the script created.

Usage: python3 -I evals/tools/scratch_run_test.py
"""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "skills", "orchestrator", "scripts", "scratch_run.py")


def run(*args, env=None):
    return subprocess.run([sys.executable, "-I", SCRIPT, *args], capture_output=True, text=True, env=env)


class ScratchRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.home = os.path.join(self.tmp, "home")
        self.project = os.path.join(self.tmp, "project")
        self.scratch = os.path.join(self.tmp, "scratch")
        os.makedirs(self.home)
        os.makedirs(self.project)
        self.env = dict(os.environ, HOME=self.home)

    def test_inside_path_runs_with_scratch_home(self):
        r = run("--scratch", self.scratch, "--project", self.project, "--env", "LEDGER_PATH=data/ledger.json", "--",
                sys.executable, "-c", "import os; print(os.environ['HOME']); print(os.environ['LEDGER_PATH']); print(os.environ['TMPDIR'])", env=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        lines = r.stdout.strip().splitlines()
        self.assertTrue(lines[0].startswith("scratch run: "), lines)
        self.assertEqual(os.path.realpath(lines[1]), os.path.realpath(self.scratch))
        self.assertTrue(lines[2].startswith(os.path.realpath(self.scratch)), lines)
        self.assertTrue(lines[3].startswith(os.path.realpath(self.scratch)), lines)
        self.assertTrue(os.path.isfile(os.path.join(self.scratch, ".scratch-run")))

    def test_env_path_outside_is_refused(self):
        r = run("--scratch", self.scratch, "--project", self.project, "--env", f"LEDGER_PATH={self.home}/ledger.json", "--",
                sys.executable, "-c", "print('ran')", env=self.env)
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("refused", r.stdout)
        self.assertNotIn("ran", r.stdout)

    def test_argument_under_home_is_refused(self):
        r = run("--scratch", self.scratch, "--project", self.project, "--",
                sys.executable, "-c", "print('ran')", f"--ledger={self.home}/Library/ledger.json", env=self.env)
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertNotIn("ran", r.stdout)
        # the project's own paths are fine as arguments
        r = run("--scratch", self.scratch, "--project", self.project, "--",
                sys.executable, "-c", "print('ran')", os.path.join(self.project, "dist", "main.js"), env=self.env)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_scratch_inside_project_is_refused(self):
        r = run("--scratch", os.path.join(self.project, "scratch"), "--project", self.project, "--", "true", env=self.env)
        self.assertEqual(r.returncode, 3)

    def test_hash_changes_with_content(self):
        data = os.path.join(self.tmp, "data")
        os.makedirs(data)
        with open(os.path.join(data, "ledger.json"), "w") as f:
            f.write("{}")
        a = run("--hash", data).stdout.strip()
        b = run("--hash", data).stdout.strip()
        self.assertEqual(a, b)
        self.assertIn("over 1 files", a)
        with open(os.path.join(data, "ledger.json"), "w") as f:
            f.write("{\"x\":1}")
        self.assertNotEqual(a, run("--hash", data).stdout.strip())
        self.assertIn("absent", run("--hash", os.path.join(self.tmp, "nowhere")).stdout)

    def test_clean_removes_only_its_own_folder(self):
        run("--scratch", self.scratch, "--project", self.project, "--", "true", env=self.env)
        self.assertEqual(run("--clean", self.home).returncode, 3)
        self.assertTrue(os.path.isdir(self.home))
        self.assertEqual(run("--clean", self.scratch).returncode, 0)
        self.assertFalse(os.path.exists(self.scratch))


if __name__ == "__main__":
    unittest.main(verbosity=1)
