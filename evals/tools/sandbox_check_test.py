"""The sandbox check's write probe against the launcher's own folders, run
without a sandbox (the probe's refusal is faked), so the one FAIL that every
`bin/kad` session hit since 0.10.0 is reproduced and shown fixed:

1. the launcher's settings (the project, Claude Code's paths, temp, npm's
   cache, the gh config directory and the audit directory in
   `filesystem.allowWrite`) with the launcher's variables in the
   environment: PASS, the launcher's folders named on the line;
2. the same settings without the launcher's variables (a runtime file
   written by hand, or the launcher before 0.14.0, which exported neither
   `KAD_GH_DIR` nor named its folders): FAIL on the two folders, as before;
3. the launcher's variables set and the settings opening a folder that is
   none of the launcher's (`~/Documents`): FAIL, still.

Usage: python3 -I evals/tools/sandbox_check_test.py
"""
import errno
import importlib.util
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "skills", "orchestrator", "scripts", "sandbox_check.py")


def load():
    spec = importlib.util.spec_from_file_location("sandbox_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class WriteCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.home = os.path.join(self.tmp, "home")
        self.project = os.path.join(self.tmp, "proj")
        # The audit directory sits outside ~/.claude here (its default is under
        # it, which the check allows anyway) so that it, too, must be named.
        for d in (self.home, self.project, os.path.join(self.home, ".config", "kad-dev-team", "gh"),
                  os.path.join(self.home, ".config", "kad-dev-team", "srt"), os.path.join(self.home, "kad-audit")):
            os.makedirs(d, exist_ok=True)
        self.saved = dict(os.environ)
        os.environ["HOME"] = self.home
        for var in ("KAD_SRT_SETTINGS", "KAD_GH_DIR", "GH_CONFIG_DIR", "KAD_AUDIT_DIR", "CLAUDE_CONFIG_DIR", "CLAUDE_CODE_TMPDIR"):
            os.environ.pop(var, None)
        os.environ["SANDBOX_RUNTIME"] = "1"
        self.mod = load()
        # The probe: a write outside the project refused by the fence.
        real_open = os.open

        def denied(path, *a, **k):
            if path.startswith(os.path.realpath(self.home)):
                raise OSError(errno.EPERM, "Operation not permitted")
            return real_open(path, *a, **k)
        self.mod.os.open = denied
        # The scratch tree is itself under the system temp directory, which the
        # check allows wholesale; the check's temp root is a sibling folder here.
        self.mod.tempfile.gettempdir = lambda: os.path.join(self.tmp, "tmp")
        os.makedirs(os.path.join(self.tmp, "tmp"), exist_ok=True)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.saved)

    def srt(self, extra=()):
        allow = [self.project, os.path.join(self.home, ".claude"), "~/.claude.json", os.path.join(self.tmp, "tmp"), "~/.npm",
                 os.path.join(self.home, ".config", "kad-dev-team", "gh"), os.path.join(self.home, "kad-audit")] + list(extra)
        return {"filesystem": {"allowWrite": allow}}

    def launcher_env(self):
        os.environ["KAD_SRT_SETTINGS"] = os.path.join(self.home, ".config", "kad-dev-team", "srt", "proj-abc.json")
        os.environ["KAD_GH_DIR"] = os.path.join(self.home, ".config", "kad-dev-team", "gh")
        os.environ["KAD_AUDIT_DIR"] = os.path.join(self.home, "kad-audit")

    def test_launcher_folders_pass_and_are_named(self):
        self.launcher_env()
        ok, detail = self.mod.check_write(os.path.realpath(self.project), {}, self.srt())
        self.assertTrue(ok, detail)
        self.assertIn("the launcher's own folders, allowed: gh config ", detail)
        self.assertIn("audit directory ", detail)
        self.assertIn("runtime settings ", detail)

    def test_without_the_launcher_the_same_folders_fail(self):
        ok, detail = self.mod.check_write(os.path.realpath(self.project), {}, self.srt())
        self.assertFalse(ok, detail)
        self.assertIn("opens paths outside the project and temp", detail)
        self.assertIn("kad-dev-team/gh", detail)
        self.assertIn("kad-audit", detail)

    def test_a_folder_that_is_not_the_launchers_still_fails(self):
        self.launcher_env()
        ok, detail = self.mod.check_write(os.path.realpath(self.project), {}, self.srt([os.path.join(self.home, "Documents")]))
        self.assertFalse(ok, detail)
        self.assertIn("Documents", detail)
        self.assertNotIn("kad-dev-team/gh", detail)

    def test_gh_config_dir_from_an_older_launcher(self):
        self.launcher_env()
        os.environ.pop("KAD_GH_DIR")
        os.environ["GH_CONFIG_DIR"] = os.path.join(self.home, ".config", "kad-dev-team", "gh")
        ok, detail = self.mod.check_write(os.path.realpath(self.project), {}, self.srt())
        self.assertTrue(ok, detail)


if __name__ == "__main__":
    unittest.main(verbosity=1)
