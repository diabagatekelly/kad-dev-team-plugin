"""Is the planning complete enough to build from? The design-readiness gate.

Run by the orchestrator at step A.5 of the chunk loop, before any builder is
launched, over the slice's planning documents. Every check is mechanical
text matching, never a model call; each is an approximation of a question a
persona would otherwise answer mid-build, and each names the persona a
failure routes back to. A check that passes proves little; a check that
fails is worth a read, since every one of these gaps cost a mid-build
decision on the first real run (a claim lifecycle nobody designed, "retry
a few times" with no number, two failure states with no mockup, an open
question routed to "the implementer").

Documents, found under `--planning` (and one level into `visual-ux/`) by
the slice number, or named by flag:

  slice           slice-<nnn>.md (an exact name first, then slice-<nnn>*.md)
  design          design-slice-<nnn>*.md or design-<nnn>*.md
  security        security-slice-<nnn>*.md
  reliability     reliability-slice-<nnn>*.md
  accessibility   accessibility-slice-<nnn>*.md or accessibility-review-<nnn>*.md
  screen          visual-ux/screen-slice-<nnn>*.md or screen-design-<nnn>*.md,
                  plus every visual-ux/*.html as a mockup

The slice and the design are required. A missing security, reliability,
accessibility or screen document is reported as `INFO <kind>: not found`
and the checks that need it are skipped, not failed: the state table
routes a missing stage, this gate judges the ones that ran.

A criterion, wherever the checks below read one, is a bullet, numbered
item or table cell that starts with `Given` (continuation lines joined
until the next bullet or blank line), or one that carries an identifier
like `AC-1`, `S1`, `SEC-3`, `R2`, `REL-4`, `A11Y-2`.

The eight checks, how each decides, and where a failure routes:

1. criteria-homed -> software-architect:architecture-design. Every
   criterion in the slice, security, reliability and accessibility files
   is quoted in the design document: its identifier appears there, or the
   first 40 characters after `Given` (whitespace folded, case ignored), or
   any run of 6 consecutive words of its text. Lists what is not.
2. failure-paths-homed -> software-architect:architecture-design. Every
   row of a failure-mode table in the reliability document (a table under
   a heading containing `failure`; the row's first cell names the failure)
   and every security criterion that names a failure (`fails`, `failure`,
   `cannot`, `can't`, `unreachable`, `times out`) has a structural home:
   at least half of its content words (lower-cased, 4+ letters, stopwords
   removed) occur in the design's Structure, Boundaries, Components or
   Decisions sections, or in any section whose heading contains
   `strategic` or `tactical`, case ignored (this roster's designs place
   failure handling in their numbered decisions as often as in Structure,
   and `architecture-design` writes the components as `### Strategic` and
   `### Tactical` under Structure; run 3's design kept its failure paths
   there and failed this check until those headings were renamed). A row
   that passes may still be homed badly; a row that fails is one the
   builder will have to place.
3. numbers-on-waits -> devsecops-engineer:reliability-requirements. No
   criterion paragraph in the reliability document mentions a wait, retry,
   poll, give-up, staleness or timeout in vague words (`a few`, `several`,
   `a while`, `again`, `some time`, `briefly`, `periodically`,
   `eventually`, `shortly`, `repeatedly`, `retry`, `retries`, `poll`,
   `wait`, `give up`, `stale`, `time out`, `times out`) without a digit or
   a number word (one..ten, once, twice) in the same paragraph, or the
   words `unbounded, owner approved`. A phrase that names no wait is
   ignored first: `try again later`, `again later`, `no retry`, `not
   retried`, `never retr…`, `without retry`, `no immediate retry`, `doesn't
   retry`, `retry
   with its attempt number` (the log's content, not a wait).
4. security-reliability-agree -> devsecops-engineer:reliability-requirements.
   For each failure term both the security and the reliability document
   use (`cancel`, `decline`, `exchange fail`, `token`, `unreachable`,
   `timeout`/`times out`, `slow`, `stopped`, `crash`, `partial`, `retry`),
   the reliability document must cite the security document somewhere
   (its filename, `security-slice`, `security criteria`, `security
   requirements`, or one of its criterion identifiers) or hand the overlap
   to the architect (`architect` in a paragraph that holds the term). No
   shared term: pass. Shared terms and no citation: fail, naming them.
5. states-have-mockups -> ux-designer:screen-design. Every state the
   security, reliability and accessibility documents name (`<word> state`
   such as `error state` or `unfinished-attempt state`, and `state 9b`
   style references) appears in the screen design document or in a
   `visual-ux/` file name (hyphens, spaces and case folded). No state
   phrase found anywhere: pass with a note.
6. no-question-to-implementer -> the document's owner (slice:
   product-slicer; requirements: product-manager; design:
   software-architect:architecture-design; security and reliability:
   devsecops-engineer with the matching skill; screen and design-system:
   ux-designer; accessibility: accessibility-engineer;
   technology-bootstrap: software-architect:technology-bootstrap;
   problem-framing and scope-map: docs-writer). In every `*.md` under the
   planning directory, inside a section whose heading contains `open
   question`, `still open`, `unresolved` or `questions`, no line routes to
   `the implementer`, `the builder`, `implementation time`, `during
   implementation`, `tdd-coach`, `tdd-implementation`, `when building` or
   `left to the implementation`. One failure line per document.
7. kept-for-later-slices -> software-architect:architecture-design. The
   design document has a line or heading containing `kept for later
   slices` (also `kept for the next slice`, `persisted for later slices`).
8. unusable-reply-row -> devsecops-engineer:reliability-requirements. When
   the design names an adapter to an external service (`adapter` within 80
   characters of HTTP, API, provider, external, third-party, SDK, vendor,
   bank, Plaid or Stripe), the reliability document must name the
   unusable-reply case (`unusable`, `malformed`, `missing field`, `invalid
   reply`, `unexpected shape`, `lies`, `garbage`, `cannot be parsed`,
   `can't use`). No external adapter named: pass with a note.

Output: one `PASS`/`FAIL` line per check (a FAIL line ends with
`-> <persona:skill>`), then `route: <check> -> <persona:skill>` for each
failure, then `readiness: PASS` or `readiness: FAIL` as the last line.
Exit 0 on PASS, 1 on FAIL, 2 when the slice or design document cannot be
found. `--json FILE` writes {"checks": {name: {passed, detail, route}},
"passed": bool}.

Usage: python3 -I ${CLAUDE_SKILL_DIR}/scripts/readiness_check.py --planning DIR --slice 001
           [--design PATH] [--slice-file PATH] [--security PATH] [--reliability PATH]
           [--accessibility PATH] [--screen PATH] [--json out.json]
"""
import argparse
import glob
import json
import os
import re
import sys

STOPWORDS = {
    "that", "this", "with", "from", "when", "then", "than", "have", "been", "were", "will", "does",
    "into", "only", "also", "each", "what", "which", "their", "there", "where", "while", "after",
    "before", "about", "because", "being", "would", "could", "should", "never", "every", "still",
    "owner", "given", "nothing", "something", "anything", "again", "later", "once", "more", "most",
    "same", "other", "them", "they", "some", "such", "your", "ours", "over", "under", "between",
}
NUMBER_WORDS = r"\b(one|two|three|four|five|six|seven|eight|nine|ten|once|twice)\b"
VAGUE = re.compile(r"\b(a few|several|a while|again|some time|briefly|periodically|eventually|shortly|"
                   r"repeatedly|retry|retries|retried|poll|polls|polling|wait|waits|waiting|give up|gives up|"
                   r"stale|staleness|time out|times out|timed out|timeout)\b", re.I)
NOT_A_WAIT = re.compile(r"try again later|again later|no (immediate )?retry|not retried|never retr\w+|without (a )?retry|does ?n[o']t retry|"
                        r"retry with its attempt|attempt number", re.I)
IDENT = re.compile(r"\b(AC|S|SEC|R|REL|A11Y|ACC)-?\d+[a-z]?\b")
SHARED_TERMS = ["cancel", "decline", "exchange fail", "token", "unreachable", "timeout", "times out",
                "slow", "stopped", "crash", "partial", "retry"]
IMPLEMENTER = re.compile(r"the implementer|the builder|implementation time|during implementation|tdd-coach|"
                         r"tdd-implementation|when building|left to the implementation", re.I)
OWNERS = [
    ("problem-framing", "docs-writer:problem-framing-doc"), ("scope-map", "docs-writer:scope-map"),
    ("requirements", "product-manager:requirements-refinement"), ("user-story", "docs-writer:user-story-writeup"),
    ("design-system", "ux-designer:design-system"), ("design", "software-architect:architecture-design"),
    ("security", "devsecops-engineer:security-requirements"),
    ("reliability", "devsecops-engineer:reliability-requirements"),
    ("screen", "ux-designer:screen-design"), ("accessibility", "accessibility-engineer:accessibility-review"),
    ("technology-bootstrap", "software-architect:technology-bootstrap"), ("adr", "docs-writer:adr"),
    ("slice", "product-slicer:vertical-slicing"),
]


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def find(planning, patterns, exact=None):
    if exact and os.path.isfile(os.path.join(planning, exact)):
        return os.path.join(planning, exact)
    for pat in patterns:
        hits = sorted(glob.glob(os.path.join(planning, pat))) + sorted(glob.glob(os.path.join(planning, "visual-ux", pat)))
        hits = [h for h in hits if not re.search(r"-v\d+\.md$", h)]
        if hits:
            return hits[0]
    return None


def sections(text):
    """[(heading, body)] in document order; text before the first heading has heading ''."""
    out, heading, body = [], "", []
    for line in text.splitlines():
        if re.match(r"^#{1,6}\s", line):
            out.append((heading, "\n".join(body)))
            heading, body = line.lstrip("#").strip(), []
        else:
            body.append(line)
    out.append((heading, "\n".join(body)))
    return out


def criteria(text):
    """Criteria as joined single lines: a bullet/numbered item/table cell starting with
    Given, with its continuation lines, or an item carrying an identifier."""
    items, current = [], None
    for line in text.splitlines():
        stripped = line.strip()
        bullet = re.match(r"^(?:[-*+]|\d+[.)])\s+(.*)", stripped)
        if bullet:
            if current:
                items.append(current)
            current = bullet.group(1)
            continue
        if "|" in stripped and stripped.startswith("|"):
            if current:
                items.append(current)
                current = None
            for cell in stripped.strip("|").split("|"):
                if re.match(r"^\s*\**given\b", cell, re.I):
                    items.append(cell.strip())
            continue
        if not stripped or re.match(r"^#{1,6}\s", stripped):
            if current:
                items.append(current)
                current = None
            continue
        if current is not None:
            current += " " + stripped
        elif re.match(r"^\**given\b", stripped, re.I):
            current = stripped
    if current:
        items.append(current)
    out = []
    for it in items:
        clean = re.sub(r"\s+", " ", it.replace("**", "")).strip()
        if re.match(r"^given\b", clean, re.I) or IDENT.search(clean[:12]):
            out.append(clean)
    return out


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[`*_\"'’“”]", "", s)).strip().lower()


def quoted_in(criterion, design_norm):
    ident = IDENT.search(criterion[:12])
    if ident and ident.group(0).lower() in design_norm:
        return True
    body = norm(re.sub(r"^given\s*", "", criterion, flags=re.I))
    if body[:40] and body[:40] in design_norm:
        return True
    words = body.split()
    for i in range(0, max(0, len(words) - 5)):
        if " ".join(words[i:i + 6]) in design_norm:
            return True
    return False


def content_words(s):
    return {w for w in re.findall(r"[a-z][a-z'-]{3,}", s.lower()) if w not in STOPWORDS}


def check_criteria_homed(docs, design):
    design_norm = norm(design)
    missing = []
    for kind in ("slice", "security", "reliability", "accessibility"):
        if docs.get(kind):
            for c in criteria(docs[kind]):
                if not quoted_in(c, design_norm):
                    missing.append(f"{kind}: {c[:60]}")
    if missing:
        return False, f"{len(missing)} criteria not quoted in the design: " + " | ".join(missing)
    return True, "every criterion is quoted in the design"


def failure_rows(reliability):
    rows = []
    for heading, body in sections(reliability):
        if "failure" not in heading.lower():
            continue
        for line in body.splitlines():
            if line.strip().startswith("|") and not re.match(r"^\|\s*-{2,}", line.strip()):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) >= 2 and cells[0] and not cells[0].lower().startswith(("dependency", "failure", "event", "what")):
                    rows.append(" ".join(cells[:2]))
    return rows


def check_failure_paths(docs, design):
    home = " ".join(body for heading, body in sections(design)
                    if re.search(r"structure|boundar|component|decision|strategic|tactical", heading, re.I)).lower()
    if not home:
        return False, "the design has no Structure, Boundaries, Components, Strategic or Tactical section"
    home_words = content_words(home)
    paths = []
    if docs.get("reliability"):
        paths += [("reliability row", r) for r in failure_rows(docs["reliability"])]
    if docs.get("security"):
        paths += [("security criterion", c) for c in criteria(docs["security"])
                  if re.search(r"\b(fails?|failure|cannot|can't|unreachable|times? out)\b", c, re.I)]
    if not paths:
        return True, "no failure-mode rows or failure criteria found to home"
    misses = []
    for kind, p in paths:
        words = content_words(p)
        if not words:
            continue
        share = len(words & home_words) / len(words)
        if share < 0.5:
            misses.append(f"{kind} ({share:.0%}): {p[:60]}")
    if misses:
        return False, f"{len(misses)} of {len(paths)} failure paths have no home in the design's structure: " + " | ".join(misses)
    return True, f"{len(paths)} failure paths find their words in the design's structure"


def check_numbers(docs):
    vague = []
    for heading, body in sections(docs["reliability"]):
        if "criteria" not in heading.lower() and "acceptance" not in heading.lower():
            continue
        for c in criteria(body):
            if not VAGUE.search(NOT_A_WAIT.sub(" ", c)):
                continue
            # The criterion's own identifier (`R1`, `REL-4`) is not a number
            # on the wait; without this every identified criterion passed.
            unlabelled = IDENT.sub(" ", c)
            if re.search(r"\d", unlabelled) or re.search(NUMBER_WORDS, unlabelled, re.I) or "unbounded, owner approved" in c.lower():
                continue
            vague.append(c[:60])
    if vague:
        return False, f"{len(vague)} criteria name a wait, retry or window with no number: " + " | ".join(vague)
    return True, "every wait, retry, poll, give-up and stale window carries a number"


def check_agree(docs, names):
    sec, rel = docs["security"].lower(), docs["reliability"].lower()
    shared = [t for t in SHARED_TERMS if t in sec and t in rel]
    if not shared:
        return True, "no failure term is shared by the security and reliability documents"
    sec_ids = {m.lower() for m in IDENT.findall(docs["security"])}
    cites = (os.path.basename(names["security"]).lower() in rel or "security-slice" in rel
             or "security criteria" in rel or "security requirements" in rel
             or any(i in rel for i in sec_ids))
    handed = any("architect" in para and any(t in para for t in shared) for para in re.split(r"\n\s*\n", rel))
    if cites or handed:
        return True, f"shared terms ({', '.join(shared)}); the reliability document cites the security document"
    return False, f"shared failure terms ({', '.join(shared)}) and the reliability document never cites the security document or hands the overlap to the architect"


def state_phrases(text):
    found = set()
    for m in re.finditer(r"\b([a-z][a-z]+(?:-[a-z]+)*)\s+state\b", text, re.I):
        w = m.group(1).lower()
        if w not in {"the", "a", "an", "its", "this", "that", "each", "every", "any", "one", "same", "stored",
                     "current", "new", "no", "of", "in", "to", "and", "or", "page", "next", "previous",
                     "plain", "connection", "history", "final", "initial", "which", "whose", "live", "active",
                     "real", "those", "these", "such", "hover", "focus", "visible", "hidden", "default",
                     "component", "panel", "card", "button", "pill", "resting", "disabled", "enabled"}:
            found.add(w)
    for m in re.finditer(r"\bstates?\s+(\d+[a-z]?)\b", text, re.I):
        found.add("state " + m.group(1).lower())
    return found


def check_states(docs, mockups):
    names = set()
    for kind in ("security", "reliability", "accessibility"):
        if docs.get(kind):
            names |= state_phrases(docs[kind])
    if not names:
        return True, "no state phrase in the security, reliability or accessibility documents"
    hay = norm(docs.get("screen", "")).replace("-", " ") + " " + " ".join(m.lower().replace("-", " ").replace("_", " ") for m in mockups)
    missing = []
    for n in sorted(names):
        key = n.replace("-", " ")
        if n.startswith("state "):
            num = n.split()[1]
            if re.search(r"\bstate\s+" + re.escape(num) + r"\b", hay) or re.search(r"\b0?" + re.escape(num) + r"\b", " ".join(mockups).lower()):
                continue
            missing.append(n)
        elif key not in hay and key.split()[0] not in hay:
            missing.append(n + " state")
    if missing:
        return False, f"{len(missing)} named states have no mockup: " + ", ".join(missing)
    return True, f"{len(names)} named states appear in the screen design or a mockup file"


def owner_of(filename):
    base = os.path.basename(filename).lower()
    for key, persona in OWNERS:
        if key in base:
            return persona
    return "the document's owner"


def check_questions(planning):
    fails = []
    files = sorted(glob.glob(os.path.join(planning, "*.md")) + glob.glob(os.path.join(planning, "visual-ux", "*.md")))
    for f in files:
        hits = []
        for heading, body in sections(read(f)):
            if re.search(r"open question|still open|unresolved|questions", heading, re.I):
                hits += [l.strip()[:60] for l in body.splitlines() if IMPLEMENTER.search(l)]
        if hits:
            fails.append((os.path.relpath(f, planning).replace(os.sep, "/"), hits))
    return fails


def check_kept(design):
    if re.search(r"kept for (later|the next|future) slices?|persisted for (later|the next) slices?", design, re.I):
        return True, "the design names what later slices need kept"
    return False, "no 'Kept for later slices' line in the design"


def check_unusable(docs, design):
    if not re.search(r"adapter.{0,80}(HTTP|API|provider|external|third.party|SDK|vendor|bank|Plaid|Stripe)|"
                     r"(HTTP|API|provider|external|third.party|SDK|vendor|bank|Plaid|Stripe).{0,80}adapter", design, re.I | re.S):
        return True, "the design names no adapter to an external service"
    if re.search(r"unusable|malformed|missing field|invalid repl|unexpected shape|\blies\b|garbage|cannot be parsed|can't use", docs["reliability"], re.I):
        return True, "the reliability document names the unusable-reply case"
    return False, "the design names an external adapter and the reliability document has no unusable-reply row"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--planning", required=True)
    p.add_argument("--slice", required=True, help="three digits, e.g. 001")
    for kind in ("design", "slice-file", "security", "reliability", "accessibility", "screen"):
        p.add_argument("--" + kind)
    p.add_argument("--json")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    planning = os.path.abspath(a.planning)
    nnn = a.slice
    if not os.path.isdir(planning):
        print(f"FAIL  planning: {a.planning} is not a directory\nreadiness: FAIL")
        return 2

    names = {
        "slice": a.slice_file or find(planning, [f"slice-{nnn}*.md"], exact=f"slice-{nnn}.md"),
        "design": a.design or find(planning, [f"design-slice-{nnn}*.md", f"design-{nnn}*.md"]),
        "security": a.security or find(planning, [f"security-slice-{nnn}*.md", f"security-{nnn}*.md"]),
        "reliability": a.reliability or find(planning, [f"reliability-slice-{nnn}*.md", f"reliability-{nnn}*.md"]),
        "accessibility": a.accessibility or find(planning, [f"accessibility-slice-{nnn}*.md", f"accessibility-review-{nnn}*.md"]),
        "screen": a.screen or find(planning, [f"screen-slice-{nnn}*.md", f"screen-design-{nnn}*.md"]),
    }
    for kind in ("slice", "design"):
        if not names[kind] or not os.path.isfile(names[kind]):
            print(f"FAIL  {kind}: no document found for slice {nnn} under {planning}\nreadiness: FAIL")
            return 2
    docs = {k: read(v) for k, v in names.items() if v and os.path.isfile(v)}
    for kind in ("security", "reliability", "accessibility", "screen"):
        if kind not in docs:
            print(f"INFO  {kind}: not found")
    mockups = [os.path.basename(f) for f in glob.glob(os.path.join(planning, "visual-ux", "*.html"))]

    arch, rel, ux = "software-architect:architecture-design", "devsecops-engineer:reliability-requirements", "ux-designer:screen-design"
    results = []
    results.append(("criteria-homed", *check_criteria_homed(docs, docs["design"]), arch))
    results.append(("failure-paths-homed", *check_failure_paths(docs, docs["design"]), arch))
    if "reliability" in docs:
        results.append(("numbers-on-waits", *check_numbers(docs), rel))
        if "security" in docs:
            results.append(("security-reliability-agree", *check_agree(docs, names), rel))
    results.append(("states-have-mockups", *check_states(docs, mockups), ux))
    for doc, hits in check_questions(planning):
        results.append(("no-question-to-implementer", False, f"{doc} routes an open question to the implementer: " + " | ".join(hits), owner_of(doc)))
    if not any(r[0] == "no-question-to-implementer" for r in results):
        results.append(("no-question-to-implementer", True, "no open question is routed to the implementer", "the document's owner"))
    results.append(("kept-for-later-slices", *check_kept(docs["design"]), arch))
    if "reliability" in docs:
        results.append(("unusable-reply-row", *check_unusable(docs, docs["design"]), rel))

    table = {}
    for name, ok, detail, route in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}" + ("" if ok else f" -> {route}"))
        entry = table.setdefault(name, {"passed": True, "detail": [], "route": route})
        entry["passed"] = entry["passed"] and ok
        entry["detail"].append(detail)
    passed = all(ok for _, ok, _, _ in results)
    for name, ok, _, route in results:
        if not ok:
            print(f"route: {name} -> {route}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"checks": table, "passed": passed, "documents": names}, f, indent=2)
    print("readiness:", "PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
