# Requirements: problem: The nightly run cannot be started by hand (requirements-001)

## Status
Active

## What has to be true

- The developer can start the nightly run by hand, as its own process on
  the machine, without restarting the web server.
- Two nightly runs never work at the same time, whichever way each was
  started: the timer's and one started by hand, or two started by hand.
- A run that was started while another is working says so and does
  nothing.

## Out of scope

More than one machine, a scheduler outside the app, a screen for the desk.
