Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/screen-design/SKILL.md

# Screen design: Slice 1 — Save a reading-list link with a note

## Thin path covered

The whole of this slice's thin path: pasting a URL (with an optional
note) and seeing it appear at the top of the list, whatever its
title-fetch outcome, plus what a first-time visitor with nothing saved
yet sees.

## Layout and composition

One page: a persistent save form (URL input, optional note field, "Save"
button) above the list, always visible — not hidden behind an
empty-state-only affordance, since a returning user adds a second link
exactly the same way a first-time user adds their first one. Four states,
each rendered as its own mockup because each is what the user sees at one
specific moment, per this slice's acceptance criteria:

| State | Mockup | Screenshot | Pattern used |
|---|---|---|---|
| No links saved yet | `visual-ux/screen-slice1-1-empty.html` | `visual-ux/screen-slice1-1-empty.jpg` | Empty-state pattern |
| Saved, title fetched, no note | `visual-ux/screen-slice1-2-populated-no-note.html` | `visual-ux/screen-slice1-2-populated-no-note.jpg` | Card |
| Saved, title fetched, with note | `visual-ux/screen-slice1-3-populated-with-note.html` | `visual-ux/screen-slice1-3-populated-with-note.jpg` | Card |
| Saved, title unreachable | `visual-ux/screen-slice1-4-unreachable-title.html` | `visual-ux/screen-slice1-4-unreachable-title.jpg` | Card (raw URL substituted for title) |

**Unreachable title uses the same Card pattern as a successful save, not
an error treatment.** The acceptance criteria are explicit that the link
"still appears" — this isn't an error. Styling it with a danger-tinted
treatment would misrepresent what happened: the save succeeded, only the
title fetch didn't. The raw URL simply takes the title's place in the
same layout position, same Card.

**Empty state copy:** "Nothing saved yet. Paste a link above to add your
first one." Names what belongs here, why it's empty, and how to fill it
— not a bare "No links."

## Interaction flow

1. **First visit, nothing saved.** The empty-state Card explains what
   belongs here and points at the always-visible save form above it.
2. **User pastes a URL, optionally adds a note, clicks Save.**
3. **Title fetch succeeds.** A new Card appears at the top of the list:
   fetched title, the note beneath it if one was given, omitted entirely
   (not an empty line) if not.
4. **Title fetch fails/unreachable.** A new Card appears at the top the
   same way, with the raw URL standing in for the title. No error
   banner, no distinct visual treatment — the acceptance criteria call
   this a normal outcome, not a failure.
5. **Saving a second link** inserts it at the top, above the first —
   most-recent-first, per the thin path's "appears at the top of the
   list."

## New patterns proposed, if any

None. All four states compose entirely from the existing Card, Button,
and empty-state patterns — no new token or component was needed.

## Open questions

- **Accessibility criteria remain an unfilled placeholder**, per this
  slice's own acceptance criteria — unowned in this roster until
  `accessibility-engineer` exists. This design followed the design
  system's existing accessibility-by-construction choices (its declared
  focus pattern, contrast-conformant colors, color never carrying
  meaning alone — used here for the unreachable-title state, which is
  distinguished by its raw-URL text, not a color cue), but conformance
  itself is unverified.
