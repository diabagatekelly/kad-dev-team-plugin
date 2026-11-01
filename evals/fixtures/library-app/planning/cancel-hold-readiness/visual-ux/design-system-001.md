# Design system: Riverside Library staff screens (design-system-001)

**Status:** Established 2026-10-22.

## Aesthetic direction

Plain, dense, readable at a desk under fluorescent light: one type scale,
one accent, generous hit targets.

## Tokens

- `--ink`: #1f2933; `--paper`: #ffffff; `--accent`: #0b6e4f;
  `--warn`: #9b2c2c; `--focus`: #ffbf47.
- Type: 16px base, 1.25 scale; buttons and inputs 44px tall.

## Core components

- **Notice**: a bordered block with a heading and a body, in one of three
  tones (ok, warn, error); announced as a status.
- **Button**: primary (accent) and quiet; focus ring in `--focus`.
- **Record table**: one row per record, actions in the last column.

## Shell

Every staff screen has the top bar with the branch name and the signed-in
staff member, and the title's record header.
