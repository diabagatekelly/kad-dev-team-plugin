# Problem: The nightly run cannot be started by hand

## Who has it

The one developer who looks after the service, and the desk's lead, who
is told each morning whether last night's reminders went out.

## What happens today

The nightly run (overdue fines assessed, due-soon reminders sent) is
started by a timer inside the web server, once every 24 hours from when
the server last started. When a deploy or a restart lands in the
evening, that night's run is late or missed, and the only way to get it
is to restart the server again and wait.

## What they want

To start the run by hand, from a terminal on the same machine, as its
own process, whenever a night was missed.

## Constraints

- One machine, one web server process, one developer.
- A reminder sent twice is a complaint at the desk; a fine assessed
  twice is money asked for twice.

## Open questions

None.
