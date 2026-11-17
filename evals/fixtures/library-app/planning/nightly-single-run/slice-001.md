# Slice 1: The developer starts the nightly run by hand, and only one run works at a time

## Thin path

The developer runs one command on the machine. If no nightly run is
working, the run starts and does what the timer's run does. If one is
working, the command says a run is in progress and exits without
assessing a fine or sending a reminder.

## Acceptance criteria

- Given no nightly run is working, when the developer starts one by hand,
  it assesses overdue fines and sends due-soon reminders as the timer's
  run does.
- Given a nightly run is working, when a second one is started (by the
  timer or by hand), the second says a run is in progress and does
  nothing.
- Given a nightly run ended, however it ended, the next one can start.
- [SECURITY — not applicable: a command on the machine, no new entry point]
- [RELIABILITY — placeholder, to be authored by devsecops-engineer]
