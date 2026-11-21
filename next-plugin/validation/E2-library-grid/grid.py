#!/usr/bin/env python3
"""Make, split, check and render a completeness grid from the library (no model).

  grid.py make ACTIONS.json LIBRARY.json > cells.json
      one empty cell per (thing the slice does, library entry of its kind)
  grid.py split CELLS.json PARTS OUT_DIR
      cut the cells into PARTS files, whole items kept together
  grid.py check CELLS.json FILLED.json [FILLED.json ...]
      every cell filled once, nothing added, dropped or altered
  grid.py render FILLED.json [FILLED.json ...] > tables.md
      the filled grid as the tables the matcher reads

The model that fills a grid chooses neither its rows nor its columns:
rows are the slice's actions, columns the library's entries.
"""
import json
import os
import sys

TAGS = ("DECIDED", "PLAN SILENT", "CONTRADICTS DOCS", "IMPOSSIBLE")
GIVEN = ("cell", "item", "entry", "action", "what", "where", "failure", "question")


def make(actions, library):
    """Cross each thing the slice does with every entry of its kind of action."""
    by_action = {}
    for entry in library:
        by_action.setdefault(entry["action"], []).append(entry)
    cells, seen = [], set()
    for item in actions:
        if item["id"] in seen:
            raise ValueError(f"{item['id']}: two things the slice does share this id")
        seen.add(item["id"])
        entries = by_action.get(item["action"])
        if entries is None:
            raise ValueError(f"{item['id']}: the library has no entries for {item['action']!r}")
        for entry in entries:
            cells.append({
                "cell": f"{item['id']}.{entry['id']}", "item": item["id"], "entry": entry["id"],
                "action": item["action"], "what": item["what"], "where": item["where"],
                "failure": entry["failure"], "question": entry["question"],
                "tag": "", "says": "",
            })
    return cells


def split(cells, parts):
    """Cut into `parts` lists of near-equal size without splitting an item."""
    groups, order = {}, []
    for cell in cells:
        if cell["item"] not in groups:
            order.append(cell["item"])
        groups.setdefault(cell["item"], []).append(cell)
    out = [[] for _ in range(parts)]
    for item in order:
        min(out, key=len).extend(groups[item])
    return [part for part in out if part]


def problems(expected, filled):
    """Why the filled cells cannot stand for the grid that was handed out."""
    found, seen = [], {}
    for cell in filled:
        name = cell.get("cell")
        if name in seen:
            found.append(f"{name}: filled twice")
        seen[name] = cell
    wanted = {cell["cell"]: cell for cell in expected}
    for name in wanted:
        if name not in seen:
            found.append(f"{name}: missing")
    for name, cell in seen.items():
        if name not in wanted:
            found.append(f"{name}: not a cell of the grid")
            continue
        for field in GIVEN:
            if cell.get(field) != wanted[name][field]:
                found.append(f"{name}: {field} was changed")
        if cell.get("tag") not in TAGS:
            found.append(f"{name}: tag is {cell.get('tag')!r}")
        if not str(cell.get("says", "")).strip():
            found.append(f"{name}: says is empty")
    return found


def render(filled):
    """One table per thing the slice does, a row per cell."""
    lines = ["# Completeness grid, built from the failure-mode library", "",
             "Every cell has an id and one tag: DECIDED, PLAN SILENT, CONTRADICTS DOCS or IMPOSSIBLE.", ""]
    current = None
    for cell in filled:
        if cell["item"] != current:
            current = cell["item"]
            lines += ["", f"## {cell['item']} ({cell['action']}): {cell['what']} ({cell['where']})", "",
                      "| id | the failure | tag | what the plan says, or what would go wrong here |", "|---|---|---|---|"]
        text = " ".join(str(cell["says"]).split()).replace("|", "/")
        lines.append(f"| {cell['cell']} | {cell['failure']} | {cell['tag']} | {text} |")
    return "\n".join(lines) + "\n"


def _load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def main(argv):
    if len(argv) == 3 and argv[0] == "make":
        json.dump(make(_load(argv[1]), _load(argv[2])), sys.stdout, indent=1, ensure_ascii=False)
        print()
        return 0
    if len(argv) == 4 and argv[0] == "split":
        os.makedirs(argv[3], exist_ok=True)
        for number, part in enumerate(split(_load(argv[1]), int(argv[2])), start=1):
            with open(os.path.join(argv[3], f"cells-{number}.json"), "w", encoding="utf-8") as handle:
                json.dump(part, handle, indent=1, ensure_ascii=False)
            print(f"cells-{number}.json: {len(part)} cells")
        return 0
    if len(argv) >= 3 and argv[0] == "check":
        found = problems(_load(argv[1]), [cell for path in argv[2:] for cell in _load(path)])
        print("\n".join(found) if found else "ok")
        return 1 if found else 0
    if len(argv) >= 2 and argv[0] == "render":
        sys.stdout.write(render([cell for path in argv[1:] for cell in _load(path)]))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
