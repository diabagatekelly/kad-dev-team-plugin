"""The slice's accepted deferrals, listed once for the pull request body.

A slice file carries what it leaves undecided under `## Explicitly
deferred` and `## Still open`, each item ending with its triage sentence
(`Usable without it: …` or `Blocker: …`; `vertical-slicing` writes them,
the readiness gate refuses an item with neither). Until 0.15.0 the four
criteria reviewers each restated every one of them as a finding at the
slice review, so that a deferral reached the pull request: 25 of one
run's 83 findings were the same handful of items, said four times. This
script lists them once, from the slice file itself, and `delivery` puts
its output in the body; no reviewer restates one.

It prints a markdown section: the heading `## Deferred with this slice`,
one line saying where the list comes from, then one bullet per item with
the section it stands under (`deferred` or `still open`), its text as
written and its triage sentence in bold. An item with neither sentence
is listed with `no triage sentence` in its place (the readiness gate
should have refused it; the body says so instead of hiding it). A slice
file with neither section, or with both empty, prints `None.` under the
heading. The last line of standard output is the count,
`deferrals: <n> listed (<d> deferred, <o> still open; <b> blocker, <u>
without a triage sentence)`, which goes on the E line.

Usage: python3 -I ${CLAUDE_SKILL_DIR}/scripts/deferrals.py --slice-file PATH [--out FILE]
  With --out the section goes to FILE and only the count line is printed.
  (from this repository: python3 -I skills/orchestrator/scripts/deferrals.py ...)
Exit codes: 0 listed (an empty list included); 1 the slice file cannot be read.
"""
import argparse
import os
import re
import sys

SECTIONS = {"explicitly deferred": "deferred", "still open": "still open"}
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
BULLET = re.compile(r"^\s{0,3}(?:[-*+]|\d+[.)])\s+(.*)$")
TRIAGE = re.compile(r"\b(Usable without it|Blocker)\s*:\s*", re.I)
EMPTY = re.compile(r"^(?:none|nothing|n/a|-|—)\.?$", re.I)


def items_of(text):
    """[(section label, item text)] in the file's order: the bullets under
    the two headings, a wrapped bullet joined into one line. Prose above
    the bullets is the section's lead and not an item; a section written
    as prose with no bullet at all is one item."""
    out, label, level, bullets, prose, open_bullet = [], None, 0, [], [], False

    def close():
        nonlocal bullets, prose, open_bullet
        if label:
            found = bullets or ([" ".join(prose)] if prose else [])
            out.extend((label, " ".join(item.split())) for item in found)
        bullets, prose, open_bullet = [], [], False

    for line in text.splitlines():
        h = HEADING.match(line)
        if h:
            close()
            title = re.sub(r"[*_`]", "", h.group(2)).strip().lower()
            if title in SECTIONS:
                label, level = SECTIONS[title], len(h.group(1))
            elif label and len(h.group(1)) <= level:
                label = None
            continue
        if not label:
            continue
        b = BULLET.match(line)
        if b:
            bullets.append(b.group(1))
            open_bullet = True
        elif not line.strip():
            open_bullet = False
        elif open_bullet:
            bullets[-1] += " " + line.strip()
        elif not bullets:
            prose.append(line.strip())
    close()
    return [(lab, item) for lab, item in out if item and not EMPTY.match(item)]


def split_triage(item):
    """(the item's own text, the triage sentence or None, is it a blocker)."""
    last = None
    for m in TRIAGE.finditer(item):
        last = m
    if last is None:
        return item, None, False
    return item[:last.start()].rstrip(" .;:—-") + ".", item[last.start():].strip(), last.group(1).lower() == "blocker"


def render(items, source):
    lines = ["## Deferred with this slice", "",
             f"What the slice ships without, as `{source}` records it; listed once here, by `deferrals.py`, "
             "and restated by no review.", ""]
    if not items:
        lines.append("None.")
    for label, item in items:
        text, triage, _ = split_triage(item)
        lines.append(f"- ({label}) {text} **{triage or 'no triage sentence'}**")
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--slice-file", required=True)
    p.add_argument("--out", help="write the section here instead of printing it")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        with open(a.slice_file, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as e:
        print(f"deferrals: cannot read {a.slice_file}: {e.strerror}")
        return 1
    items = items_of(text)
    section = render(items, os.path.basename(a.slice_file))
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(section)
    else:
        print(section)
    triaged = [split_triage(item) for _, item in items]
    print(f"deferrals: {len(items)} listed ({sum(1 for lab, _ in items if lab == 'deferred')} deferred, "
          f"{sum(1 for lab, _ in items if lab == 'still open')} still open; "
          f"{sum(1 for t in triaged if t[2])} blocker, {sum(1 for t in triaged if t[1] is None)} without a triage sentence)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
