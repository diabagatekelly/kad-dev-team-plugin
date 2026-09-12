---
name: ux-designer:design-system
tags: [ux-designer, design-system]
runs: 3
---

**Format note:** this skill introduces two real blocking questions before a
design system is finished — whether the user has a reference to work from
or wants candidates generated, and (when generating) which rendered
candidate to keep — the same way `software-architect:architecture-design`
extends the documented single-question format to a second round.
`eval-result/` for this case holds `phase1-question.md` (the
reference-vs-generate question), `phase2-question.md` (the candidate
choice, once rendered), and `output.md` (the finished design system after
both answers). Graders target `phase1` or `phase2` accordingly; anything
else grades `output.md`.

A slice has been cut, designed, and cleared through security and
reliability review. No project design system exists yet.

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

## Established elsewhere, not this skill's call

Web app, React with Vite (`technology-bootstrap`). Single user, no
authentication yet (`requirements`). The data provider, persistence, and
hosting are not this skill's concern.

## Scripted answers

- If asked whether there's a concrete reference to work from or whether to
  generate candidate directions: "No reference — generate a few real
  options and show me."
- Once directions are rendered and presented for a choice: "The second one
  — it's the most distinctive without feeling like a mismatch for a
  reading-list tool. Go with that one."
