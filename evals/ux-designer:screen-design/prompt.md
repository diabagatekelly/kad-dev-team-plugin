---
name: ux-designer:screen-design
tags: [ux-designer, screen-design]
runs: 3
---

A design system already exists for this project — tokens, a `Card`
pattern, a `Button` pattern, and an empty-state pattern are all declared
and binding. Slice 1 needs its screen composed within it.

# Slice 1: Save a reading-list link with a note

## Thin path

The user pastes a URL and an optional short note, and the link appears at
the top of their reading list showing its title, the note if given, and
when it was saved.

## Acceptance criteria

- Given a valid URL and no note, when saved, the link appears at the top
  of the list with its fetched title and no note text shown.
- Given a valid URL and a note, when saved, the link appears at the top of
  the list with its fetched title and the note shown beneath it.
- Given the URL can't be reached to fetch a title, when saved, the link
  still appears, showing the raw URL in place of a title, not an error.
- Given the list has no saved links yet, the page states that plainly and
  explains how to add the first one, rather than showing an empty table.
- Accessibility — PLACEHOLDER, not authored here. Owned by
  `accessibility-engineer`, which does not exist in this roster yet. This
  placeholder stays visible until that persona can write it, rather than
  being dropped because no one owns it today.

## Established elsewhere, not this skill's call

The design system itself (tokens, `Card`, `Button`, empty-state pattern)
already exists and is binding — not this skill's call to change. No
search, filtering, editing, or deletion of saved links is in scope for
this slice; none of the acceptance criteria mention them.

## Scripted answers

None expected. This slice's acceptance criteria name every state directly
(populated-with-note, populated-without-note, unreachable-title, empty),
and the existing design system already has patterns for all of them. If
the persona asks anything else, script: "Just design it straightforwardly
for what the acceptance criteria already describe — nothing beyond that."
