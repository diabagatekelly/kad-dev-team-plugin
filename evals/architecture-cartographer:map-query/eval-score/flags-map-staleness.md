PASS

The output opens with an explicit caveat before the three queries: it
notes a teammate's RefundLedger branch finished yesterday and hasn't gone
through map-update, states the map's "Changes since the prior map"
section only covers the case-assignment slice (consistent with
RefundLedger being absent), and explicitly says map-query is read-only
against what's persisted and never live-scans the codebase. Each of the
three answers carries a "possibly stale (see note above)" pointer back to
that caveat, including the third (negative-result) query, which most
needs it. No claim is made anywhere that the actual current codebase was
checked.
