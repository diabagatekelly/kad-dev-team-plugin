# Delegation: slice 001, staff cancel a member's hold on a title

Owner's words, 2026-10-26: "Yes — settle build-time decisions with the
owning persona and log them; I'll overturn anything I disagree with."

## Covers

- Design decisions inside the slice's boundaries (`software-architect`,
  `architecture-design`).
- Security and reliability criteria for the slice, including a number on
  a wait or a retry, and the shape of a failure result
  (`devsecops-engineer`, `security-requirements`,
  `reliability-requirements`).
- Screen states and accessibility criteria, should the slice gain a
  screen (`ux-designer`, `accessibility-engineer`).

## Never covers

- Scope: what the slice delivers or defers.
- Requirements: anything in `requirements-001.md` marked confirmed.
- Anything that would change a confirmed requirement; those stay backward
  routes to the owner.

Each decision made under this file is committed under the persona's name
as `Decision <n>: <title>` and logged on the chunk's line.
