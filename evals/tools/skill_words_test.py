#!/usr/bin/env python3
"""The skills describe rules, not one project. A skill, agent or hook that
names the domain of a project the plugin was run on (a payee, a provider,
an account store, a run by its number) is anchored to that project: the
rule it carries reads as that project's, and the next reader reaches for
that project's shapes. The story goes in INCIDENTS.md under a number and
the skill cites the number (the owner's coupling check, 2026-11-10).

Usage: python3 -I evals/tools/skill_words_test.py
"""
import glob
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILES = (glob.glob(os.path.join(ROOT, "skills", "*", "SKILL.md"))
         + glob.glob(os.path.join(ROOT, "agents", "*", "AGENT.md"))
         + glob.glob(os.path.join(ROOT, "hooks", "*")))
# Words of the projects the plugin has been run on, and runs by their number.
ANCHORED = re.compile(
    r"\b(?:merchants?|Plaid|ledgers?|Keychain|Chime|Amex|Bank of America|personal-finance|tracker-3"
    r"|[Rr]un [123]'s|[Rr]un [123] (?:learned|left|did|wrote|measured|needed|kept)|[Rr]epo [123]'s"
    r"|[Ss]lice 2's|[Ss]lice 2 (?:measured|needed|deferred|ran|appended|took))\b")


class SkillWords(unittest.TestCase):
    def test_no_skill_names_a_project_the_plugin_ran_on(self):
        hits = []
        for path in sorted(FILES):
            if os.path.isdir(path):
                continue
            with open(path, encoding="utf-8", errors="replace") as f:
                for n, line in enumerate(f, 1):
                    m = ANCHORED.search(line)
                    if m:
                        hits.append(f"{os.path.relpath(path, ROOT)}:{n}: {m.group(0)}")
        self.assertEqual(hits, [], "a skill names a project; move the story to INCIDENTS.md and cite its number:\n" + "\n".join(hits))

    def test_every_cited_incident_exists(self):
        with open(os.path.join(ROOT, "INCIDENTS.md"), encoding="utf-8") as f:
            numbers = {int(m) for m in re.findall(r"^(\d+)\. \*\*", f.read(), re.M)}
        missing = []
        for path in sorted(FILES):
            if os.path.isdir(path):
                continue
            with open(path, encoding="utf-8", errors="replace") as f:
                for n, line in enumerate(f, 1):
                    for m in re.finditer(r"incidents? (\d+(?:(?:, | and )\d+)*)", line):
                        for num in re.findall(r"\d+", m.group(1)):
                            if int(num) not in numbers:
                                missing.append(f"{os.path.relpath(path, ROOT)}:{n}: incident {num}")
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
