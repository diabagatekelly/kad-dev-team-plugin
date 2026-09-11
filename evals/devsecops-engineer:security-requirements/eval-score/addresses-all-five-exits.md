PASS

All five exits are addressed: logs ("Secrets stay out of logs"), exception/stack traces ("Exceptions and stack traces don't carry the credential"), error responses ("Failures don't leak provider internals"), monitoring/telemetry/analytics (dismissed with a stated reason: greenfield slice, no telemetry mechanism exists), and test fixtures ("Test data is fabricated"). Fixed from the prior draft, which had four of five — exception/stack-trace was missing until added as its own distinct criterion.
