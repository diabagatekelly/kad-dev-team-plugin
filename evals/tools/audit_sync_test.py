"""The audit sync's transcript rules, without a model: a session's transcript
found by its id, withheld when it holds a listed source's value, refreshed
when it grew, open until its SessionEnd, and one sync at a time.

Every value here is invented: the "sheet" is
`evals/fixtures/library-app/source-plants/desk-fees.csv`, seven made-up fee
rows, listed from outside the project tree. Each test builds a project, an
audit directory with session logs and transcripts, a bare audit remote and
its clone, and runs `skills/orchestrator/scripts/audit_sync.py`.

 1. a live transcript the hook never snapshotted is copied by session id,
    with its subagents', and the session is listed as complete;
 2. a transcript holding a value of the sheet is withheld: nothing of it in
    the clone, the log still copied, the line and the last line say so,
    and no value is printed or written anywhere;
 3. a hit in the log itself withholds the whole session;
 4. the larger of the live copy and the snapshot is taken, and a copy
    whose source grew since is refreshed by the next sync;
 5. a session without a SessionEnd is listed as open;
 6. a transcript the scan cannot read is withheld, not copied as clean; so
    is every session when a listed source cannot be read;
 7. without a sources.md nothing is scanned and the line says so;
 8. a second sync cannot interleave: the lock refuses it with exit 5 and
    nothing copied; a stale lock is taken over.

Usage: python3 -I evals/tools/audit_sync_test.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "skills", "orchestrator", "scripts", "audit_sync.py")
SHEET = os.path.join(ROOT, "evals", "fixtures", "library-app", "source-plants", "desk-fees.csv")
SID_A = "aaaaaaaa-0000-4000-8000-000000000001"
SID_B = "bbbbbbbb-0000-4000-8000-000000000002"
A_VALUE = "Odalys Brennecke"       # a text cell of the sheet (invented)
A_WORD = "Brennecke"


def git(cwd, *args):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, check=True).stdout


class AuditSync(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.project = os.path.join(self.tmp, "app")
        self.docs = os.path.join(self.project, "docs", "unit")
        self.audit = os.path.join(self.tmp, "audit")
        self.projects = os.path.join(self.tmp, "projects")
        self.folder = os.path.join(self.projects, re.sub(r"[^A-Za-z0-9]", "-", self.project))
        self.remote = os.path.join(self.tmp, "audit-remote.git")
        self.clone = os.path.join(self.audit, "repo")
        os.makedirs(self.docs)
        os.makedirs(os.path.join(self.audit, "sessions"))
        os.makedirs(os.path.join(self.audit, "transcripts"))
        os.makedirs(self.folder)
        # the project: one commit, a planning directory with the log
        git(self.tmp, "init", "-q", "-b", "main", self.project)
        git(self.project, "config", "user.email", "t@example.invalid")
        git(self.project, "config", "user.name", "T")
        with open(os.path.join(self.docs, "orchestrator-log.md"), "w") as f:
            f.write("# Orchestrator log\n\n## 1. 2026-11-10 — a state\n\n**Routed to:** `x`\n**Artifact:** `y`\n")
        with open(os.path.join(self.project, "README.md"), "w") as f:
            f.write("app\n")
        git(self.project, "add", "-A")
        git(self.project, "commit", "-qm", "start")
        # the sheet, outside the tree, listed with no commit (everything counts)
        self.sheet = os.path.join(self.tmp, "desk-fees.csv")
        shutil.copy(SHEET, self.sheet)
        self.write_sources()
        # the audit remote and its clone
        git(self.tmp, "init", "-q", "--bare", "-b", "main", self.remote)
        git(self.tmp, "clone", "-q", self.remote, self.clone)
        with open(os.path.join(self.clone, "README.md"), "w") as f:
            f.write("audit\n")
        git(self.clone, "add", "README.md")
        git(self.clone, "-c", "user.email=t@example.invalid", "-c", "user.name=T", "commit", "-qm", "start")
        git(self.clone, "push", "-q", "-u", "origin", "main")
        self.env = dict(os.environ, KAD_AUDIT_REPO=self.remote, KAD_AUDIT_DIR=self.audit)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_sources(self, location=None):
        with open(os.path.join(self.docs, "sources.md"), "w") as f:
            f.write("# Sources\n| Source | Location | Tab or range | Read on | Listed at |\n|---|---|---|---|---|\n"
                    f"| desk fees | `{location or self.sheet}` | all | 2026-11-10 | - |\n")

    def log(self, sid, ended=True, prompt="what's next"):
        """A session log of this project naming its transcript."""
        path = os.path.join(self.audit, "sessions", f"{sid}.jsonl")
        transcript = os.path.join(self.folder, f"{sid}.jsonl")
        base = {"session_id": sid, "transcript_path": transcript, "cwd": self.project}
        events = [dict(base, hook_event_name="SessionStart", source="startup"),
                  dict(base, hook_event_name="UserPromptSubmit", prompt=prompt),
                  dict(base, hook_event_name="PostToolUse", tool_name="Skill",
                       tool_input={"skill": "kad-dev-team:orchestrator"})]
        if ended:
            events.append(dict(base, hook_event_name="SessionEnd", reason="exit"))
        with open(path, "w") as f:
            for e in events:
                f.write(json.dumps({"ts": "2026-11-10T10:00:00Z", "payload": e}) + "\n")
        return path

    def transcript(self, sid, lines, where=None, subagents=()):
        """A live transcript (default) or a snapshot, with subagent files."""
        where = where or self.folder
        path = os.path.join(where, f"{sid}.jsonl")
        with open(path, "w") as f:
            for text in lines:
                f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}) + "\n")
        for name, text in subagents:
            d = os.path.join(where, sid, "subagents")
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, name), "w") as f:
                f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}) + "\n")
        return path

    def sync(self, *extra, expect=0):
        r = subprocess.run([sys.executable, "-I", SCRIPT, "--project", self.project, "--slice", "1",
                            "--audit-dir", self.audit, "--projects-dir", self.projects, "--transcripts", *extra],
                           capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, expect, r.stdout + r.stderr)
        return r.stdout

    def in_clone(self, *parts):
        return os.path.join(self.clone, "app-slice-1", "implementation-docs", "transcripts", *parts)

    def clone_text(self):
        """Every text file of the clone's slice folder, concatenated."""
        out = []
        for d, _, fs in os.walk(os.path.join(self.clone, "app-slice-1")):
            for f in fs:
                with open(os.path.join(d, f), encoding="utf-8", errors="replace") as fh:
                    out.append(fh.read())
        return "\n".join(out)

    def sync_log(self):
        with open(os.path.join(self.clone, "app-slice-1", "sync-log.md"), encoding="utf-8") as f:
            return f.read()

    # 1
    def test_live_transcript_is_copied_by_session_id(self):
        self.log(SID_A)
        self.transcript(SID_A, ["the hold is cancelled"], subagents=[("agent-1.jsonl", "a builder's turn")])
        out = self.sync()
        self.assertTrue(os.path.isfile(self.in_clone(SID_A, f"{SID_A}.jsonl")), out)
        self.assertTrue(os.path.isfile(self.in_clone(SID_A, SID_A, "subagents", "agent-1.jsonl")), out)
        self.assertTrue(os.path.isfile(self.in_clone(SID_A, "calls.jsonl")), out)
        self.assertRegex(out.strip().splitlines()[-1], r"^audit commit [0-9a-f]{7,}$")
        self.assertNotIn("open", out)
        self.assertIn("1 session log(s), 1 with a transcript (0 refreshed, 0 open)", self.sync_log())
        self.assertEqual(git(self.remote, "log", "--oneline").count("\n"), 2)

    # 2
    def test_transcript_with_a_source_value_is_withheld(self):
        self.log(SID_A)
        self.log(SID_B)
        self.transcript(SID_A, ["a clean turn"])
        self.transcript(SID_B, ["the member is " + A_VALUE + ", fee 7.35"], subagents=[("agent-2.jsonl", "clean")])
        out = self.sync()
        self.assertTrue(os.path.isfile(self.in_clone(SID_A, f"{SID_A}.jsonl")))
        self.assertFalse(os.path.exists(self.in_clone(SID_B, f"{SID_B}.jsonl")), out)
        self.assertFalse(os.path.exists(self.in_clone(SID_B, SID_B)), out)
        self.assertTrue(os.path.isfile(self.in_clone(SID_B, "calls.jsonl")), out)
        self.assertIn(f"{SID_B} (withheld: 2 source value(s) in 1 entries of 1 file(s))", out)
        self.assertEqual(out.strip().splitlines()[-1].split(";")[1].strip(), f"withheld: {SID_B}")
        self.assertIn(f"withheld: {SID_B} (2 source value(s)", self.sync_log())
        for text in (out, self.clone_text()):
            self.assertNotIn(A_WORD, text)
            self.assertNotIn("7.35", text)

    # 3
    def test_a_hit_in_the_log_withholds_the_session(self):
        self.log(SID_A, prompt="use " + A_VALUE + " as the example")
        self.transcript(SID_A, ["a clean turn"])
        out = self.sync()
        self.assertFalse(os.path.exists(self.in_clone(SID_A)), out)
        self.assertIn(f"withheld: {SID_A}", out)
        self.assertNotIn(A_WORD, self.clone_text())

    # 4
    def test_larger_copy_wins_and_growth_is_refreshed(self):
        self.log(SID_A)
        snap = self.transcript(SID_A, ["one"], where=os.path.join(self.audit, "transcripts"))
        live = self.transcript(SID_A, ["one", "two"])
        self.sync()
        with open(self.in_clone(SID_A, f"{SID_A}.jsonl")) as f:
            self.assertEqual(len(f.read().splitlines()), 2)
        # the live copy grows: the next sync refreshes it and commits
        time.sleep(1.1)
        self.transcript(SID_A, ["one", "two", "three"])
        out = self.sync()
        with open(self.in_clone(SID_A, f"{SID_A}.jsonl")) as f:
            self.assertEqual(len(f.read().splitlines()), 3)
        self.assertIn("(1 refreshed, 0 open)", self.sync_log().splitlines()[-1])
        self.assertRegex(out.strip().splitlines()[-1], r"^audit commit [0-9a-f]{7,}$")
        # nothing grew: nothing new
        out = self.sync()
        self.assertEqual(out.strip().splitlines()[-1], "audit commit none")
        self.assertTrue(os.path.isfile(snap) and os.path.isfile(live))

    # 5
    def test_session_without_an_end_is_open(self):
        self.log(SID_A, ended=False)
        self.transcript(SID_A, ["still running"])
        out = self.sync()
        self.assertIn(f"{SID_A} (open: no SessionEnd yet)", out)
        self.assertIn("(0 refreshed, 1 open)", self.sync_log())
        self.assertTrue(os.path.isfile(self.in_clone(SID_A, f"{SID_A}.jsonl")))

    # 6
    def test_unreadable_transcript_and_unreadable_source_withhold(self):
        self.log(SID_A)
        live = self.transcript(SID_A, ["a clean turn"])
        os.chmod(live, 0)  # a file nothing can read
        if os.access(live, os.R_OK):
            self.skipTest("running as a user that reads a mode-0 file")
        out = self.sync()
        os.chmod(live, 0o600)
        self.assertIn(f"{SID_A} (withheld: {SID_A}.jsonl could not be read; not copied as clean)", out)
        self.assertFalse(os.path.exists(self.in_clone(SID_A, f"{SID_A}.jsonl")))
        self.write_sources(os.path.join(self.tmp, "missing.csv"))
        out = self.sync()
        self.assertIn("withheld: the scan could not run (source not readable here: desk fees", out)
        self.assertFalse(os.path.exists(self.in_clone(SID_A, f"{SID_A}.jsonl")))
        self.assertTrue(os.path.isfile(self.in_clone(SID_A, "calls.jsonl")))

    # 7
    def test_without_sources_nothing_is_scanned(self):
        os.remove(os.path.join(self.docs, "sources.md"))
        self.log(SID_A)
        self.transcript(SID_A, ["the member is " + A_VALUE])
        out = self.sync()
        self.assertIn("no sources.md in", out)
        self.assertIn("transcripts not scanned for source values", self.sync_log())
        self.assertTrue(os.path.isfile(self.in_clone(SID_A, f"{SID_A}.jsonl")))
        self.assertNotIn("withheld", out)

    # 8
    def test_lock_refuses_a_second_sync_and_a_stale_one_is_taken_over(self):
        self.log(SID_A)
        self.transcript(SID_A, ["a clean turn"])
        lock = os.path.join(self.clone, ".kad-sync.lock")
        with open(lock, "w") as f:
            f.write("pid 1 on elsewhere since 2026-11-10T00:00:00+00:00\n")
        out = self.sync(expect=5)
        self.assertIn("another sync holds", out)
        self.assertFalse(os.path.exists(self.in_clone(SID_A)))
        self.assertTrue(os.path.isfile(lock))
        os.utime(lock, (time.time() - 7200, time.time() - 7200))
        out = self.sync()
        self.assertRegex(out.strip().splitlines()[-1], r"^audit commit [0-9a-f]{7,}$")
        self.assertFalse(os.path.exists(lock))


if __name__ == "__main__":
    unittest.main(verbosity=1)
