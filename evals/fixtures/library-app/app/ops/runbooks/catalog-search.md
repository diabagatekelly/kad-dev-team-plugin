# Catalog search returning 5xx

Search answers 503 when `PostgresCatalogReader.search` throws; the route
reports the error to monitoring with the request path and the failure
`reason` (`timeout`, `connection`, `query`, or `unexpected` for anything
that isn't a database failure). Public search runs
on its own pool (4 connections, 2 s timeout), so it cannot take
connections from checkout, fines or session checks. The catalog holds
about 60,000 titles and grows by a few hundred a month; search answers in
about 40 ms at p95.

1. Check the monitoring provider for recent `catalog` errors and note the
   first occurrence.
2. Group the error events by `reason`. A burst of `timeout` or
   `connection` points at the database (check its health and connections);
   `query` or `unexpected` points at the last deploy.
3. If the database is healthy, roll back the most recent deploy
   (`.github/workflows/deploy.yml`, re-run the previous successful run).
4. Search is read-only; no data needs repair after an outage.
