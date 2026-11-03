# The cold-read check on Opus (H2.2's first step), 2026-11-02

Three launches, one per run, each a general-purpose Opus agent handed the
project root (a detached worktree at the commit the run's assessment
used), the documented test command and a report path, and the cold
protocol: read all of `src/` and `test/`, no `planning/`, `docs/` or git
log; install with the frozen lockfile; typecheck, lint, format check and
the suite; probe each suspected bug by execution with a scratch script
outside the tree; never the app against a real service. The three
reports are beside this file. Run 2's reader read all of `src/` and most
of `test/` whole but, for five large screen-script test files and
`test/repo/*`, only the harness setup and the test names, and says so
at the top of its report; the other two read everything. Compared with each run's recorded
assessment (`audit-docs/<project>-slice-1/plugin-review/*code-assessment*`).

| Run (commit) | Recorded bug | Opus cold read |
|---|---|---|
| 1 (`799f11c`) | Second connection accepted by the API, two `connected_accounts` rows | **found**, High, confirmed by execution |
| 1 | 5xx with an unrecognised `error_code` classified `unexpected` | missed |
| 1 | `dev:web` has no API proxy | missed |
| 2 (`0cdc10d`) | Orphaned encrypted token after a failed `save connection` | **found**, Medium, confirmed by execution |
| 2 | Year dropped from the date column over a 24-month window | missed |
| 2 | `complete()` accepts a connect result with no claim held | **found**, High, confirmed by execution |
| 2 | Possibly dead `wrangler dev --local` flag | missed |
| 3 (`d1c962b`) | H4.1 a JSON body of `null` answered 500 | missed |
| 3 | H4.2 exchange timed out after Plaid created the Item, retry refused, Item orphaned | **found**, Medium, confirmed by execution |
| 3 | H4.3 `fetchSince` has no page cap | missed (found instead: the first retrieval saves the cursor past the months it dropped, Medium, confirmed) |
| 3 | H4.4 `PORT=abc` crashes with a stack trace | missed (found instead: a port in use crashes with an unhandled `'error'` event, Low, confirmed) |

New findings the recorded assessments did not have, all confirmed by
execution: run 1, a secret-store failure after Plaid's `onSuccess`
reported as "Nothing was connected" (Medium) and a zero-transaction
first pull locking Pull in the UI (Medium); run 2, a cancel arriving
before its start leaving an uncancellable claim (Low) and an ABA case in
the history write guard (Low); run 3, a retrieval Plaid refuses that can
never recover through the page's own advice (High), Ctrl-C orphaning a
Plaid item (Medium), and keys minted over unreadable stored data (Low).

**Reading.** Every load-bearing data-integrity bug on the lists, the
ones run 3's six D reviewers missed with the planning documents in hand
(the exchange-once seam, the second connection, the orphaned token and
Item), the Opus cold read found and confirmed by running it, in one
pass per run, and it added real findings of the same class. What it
missed is input handling and dev tooling: the `null` body, `PORT=abc`,
the 5xx classification, the dropped year, the dead flag. Those are the
kind a checklist reviewer catches on its second pass over the criteria
(reliability-review's rows; H3.4 adds the created-then-retried one).

**Decision (the handoff's rule).** Opus finds the same bugs that matter:
the protocol is the change and the model stays. H2.2 goes in as written,
on the current model, no Fable-pinned launch. The misses are noted for
the slice 2 audit: if the criteria pass does not catch that class, the
second-pass checklist is where to add it, not a model change.
