#!/usr/bin/env python3
"""`cost_by_role.py` and a session with no transcript, without a model
(TODO.md's F4): a session the log names whose transcript is nowhere is
skipped and named on the last line, and the rest is totalled; the
caller's own session (`--session`) stays required, and so does finding
at least one.

Usage: python3 -I evals/tools/cost_by_role_test.py
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cost_by_role.py")
KEPT = "11111111-1111-4111-8111-111111111111"
LOST = "22222222-2222-4222-8222-222222222222"
OWN = "33333333-3333-4333-8333-333333333333"


class ASessionWithNoTranscript(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.audit = os.path.join(self.tmp, "audit")
        os.makedirs(os.path.join(self.audit, "transcripts"))
        self.log = os.path.join(self.tmp, "orchestrator-log.md")
        with open(self.log, "w", encoding="utf-8") as f:
            f.write("## 9. 2026-11-01 — slice ready for implementation\n\n**Routed to:** chunk loop\n"
                    f"- **A. Start:** sandbox — `PASS`; session — `{LOST}`; audit — `off`\n"
                    f"  - Resumed 2026-11-02 at C, session `{KEPT}`, transcript `kept`\n")

    def transcript(self, sid, output_tokens):
        row = {"type": "assistant", "timestamp": "2026-11-02T10:00:00Z",
               "message": {"id": f"msg-{sid[:8]}", "model": "claude-sonnet-5-5",
                           "usage": {"input_tokens": 0, "output_tokens": output_tokens}}}
        with open(os.path.join(self.audit, "transcripts", f"{sid}.jsonl"), "w", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    def run_tool(self, *args):
        r = subprocess.run([sys.executable, "-I", SCRIPT, "--audit-dir", self.audit, "--projects-dir", os.path.join(self.tmp, "none"),
                            "--price", "claude-sonnet-5-5=0,10,0,0", *args], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip().splitlines()

    def test_the_lost_session_is_named_and_the_rest_totalled(self):
        self.transcript(KEPT, 1_000_000)
        out = self.run_tool("--log", self.log)
        self.assertEqual(out[-1], f"cost $10.00, not covering {LOST} (no transcript)")
        self.assertTrue(any(line.startswith(f"transcript missing for {LOST}: looked at ") for line in out))

    def test_every_session_found_is_a_plain_total(self):
        self.transcript(KEPT, 1_000_000)
        self.transcript(LOST, 500_000)
        self.assertEqual(self.run_tool("--log", self.log)[-1], "cost $15.00")

    def test_the_callers_own_session_is_never_skipped(self):
        self.transcript(KEPT, 1_000_000)
        out = self.run_tool("--log", self.log, "--session", OWN)
        self.assertEqual(out[-1], f"cost not measured: transcript missing for {OWN}")

    def test_an_earlier_loop_in_the_same_log_is_not_counted(self):
        # a log holds every slice's loop: the E step's cost is the last one's
        earlier = "44444444-4444-4444-8444-444444444444"
        text = open(self.log, encoding="utf-8").read()
        with open(self.log, "w", encoding="utf-8") as f:
            f.write("## 3. 2026-10-20 — slice ready for implementation\n\n**Routed to:** chunk loop\n"
                    f"- **A. Start:** sandbox — `PASS`; session — `{earlier}`; audit — `off`\n- **E. Delivery:** pushed\n\n" + text
                    + "\n## 10. 2026-11-02 — Owner direction\n\n- a bullet under a later entry of the same loop\n")
        self.transcript(earlier, 5_000_000)
        self.transcript(KEPT, 1_000_000)
        self.transcript(LOST, 1_000_000)
        out = self.run_tool("--log", self.log)
        self.assertEqual(out[-1], "cost $20.00")

    def test_no_session_found_at_all_is_no_total(self):
        out = self.run_tool("--log", self.log)
        self.assertEqual(out[-1], f"cost not measured: transcript missing for {LOST}, {KEPT}")

    def test_the_json_names_what_the_total_leaves_out(self):
        self.transcript(KEPT, 1_000_000)
        dest = os.path.join(self.tmp, "cost.json")
        self.run_tool("--log", self.log, "--json", dest)
        with open(dest, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual((data["total"], data["not_covered"]), (10.0, [LOST]))


class TheRoleOfALaunch(unittest.TestCase):
    """S7 (the slice 4 review, F13): the slice reviewers were launched as
    "Slice 4 review: security" and filed as consults by their agent type,
    $8.66 of one slice under the wrong heading."""

    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("cost_by_role", SCRIPT)
        self.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.tool)

    def test_a_slice_reviewer_named_after_a_colon_is_a_reviewer(self):
        for description, agent_type, role in (
                ("Slice 4 review: security", "kad-dev-team:devsecops-engineer:AGENT", "reviewer:security"),
                ("Slice 4 review: reliability", "kad-dev-team:devsecops-engineer:AGENT", "reviewer:reliability"),
                ("Slice 4 review: architecture", "kad-dev-team:software-architect:AGENT", "reviewer:architecture"),
                ("Slice 4 review: accessibility", "kad-dev-team:accessibility-engineer:AGENT", "reviewer:accessibility"),
                ("Slice 4 review: code", "kad-dev-team:code-reviewer:AGENT", "reviewer:code"),
                ("Slice 4 review: test quality", "kad-dev-team:code-reviewer:AGENT", "reviewer:test-quality"),
                ("Slice 4 r1 re-review: security", "kad-dev-team:devsecops-engineer:AGENT", "reviewer:security"),
                ("Slice 4 r1 re-review: accessibility", "kad-dev-team:accessibility-engineer:AGENT", "reviewer:accessibility"),
                ("Slice 4 r1 re-review: test quality", "kad-dev-team:code-reviewer:AGENT", "reviewer:test-quality"),
                ("Security review of slice 3", "kad-dev-team:devsecops-engineer:AGENT", "reviewer:security")):
            self.assertEqual(self.tool.role_of(description, agent_type), role, description)

    def test_a_fixer_named_in_the_middle_and_the_capture_fixer_are_fixers(self):
        for description in ("Slice 4 second fixer (regressions)", "Gate fixer: lint error", "Add slice 4 screen captures",
                            "Fix CI screens r1 captures", "Fix chunk 6 gate failure"):
            self.assertEqual(self.tool.role_of(description, "kad-dev-team:tdd-coach:AGENT"), "fixer", description)

    def test_what_was_right_stays(self):
        for description, agent_type, role in (
                ("Build slice 004 chunk 3", "kad-dev-team:tdd-coach:AGENT", "builder/planner"),
                ("Plan slice 4 chunks", "kad-dev-team:tdd-coach:AGENT", "builder/planner"),
                ("Chunk 5 of 7 runner (light)", "kad-dev-team:chunk-runner:AGENT", "runner"),
                ("Re-review fix r1 chunk 1", "kad-dev-team:code-reviewer:AGENT", "reviewer:chunk"),
                ("Slice 4 criteria walk", "kad-dev-team:accessibility-engineer:AGENT", "walk"),
                ("Slice 4 cold read", "kad-dev-team:tdd-coach:AGENT", "reviewer:cold"),
                ("Comments-only review, slice 4", "kad-dev-team:code-reviewer:AGENT", "reviewer:comments"),
                ("Slice 4 last-fix review", "kad-dev-team:code-reviewer:AGENT", "reviewer:code"),
                ("UX decision for chunk 2", "kad-dev-team:ux-designer:AGENT", "consult"),
                ("Reliability decision: complete during close", "kad-dev-team:devsecops-engineer:AGENT", "consult"),
                ("Triage PR #72 comments", "kad-dev-team:code-reviewer:AGENT", "triage")):
            self.assertEqual(self.tool.role_of(description, agent_type), role, description)


if __name__ == "__main__":
    unittest.main(verbosity=1)
