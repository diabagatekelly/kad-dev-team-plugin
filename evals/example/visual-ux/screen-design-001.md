# Screen design: Slice 1 — Connect one institution and see its transactions

## Thin path covered

Everything slice-001's acceptance criteria require to be visible: a
starting point with no institution connected, the connect flow itself
(hosted by the data provider), the populated transaction list on success,
and the three outcomes the slice's own scope change exists to keep
distinguishable — still preparing, genuinely nothing found, and a failed
connection attempt. No categorization, filtering, sorting, or
multi-institution UI — none of it is in this slice's acceptance criteria,
so none of it is on these screens.

## Layout and composition

Seven states, each meaningfully distinct, each rendered as its own mockup
and screenshot in `visual-ux/`:

| State | HTML | Screenshot |
|---|---|---|
| No institution connected yet | `screen-connect-start.html` | `screen-connect-start.jpg` |
| Connect flow in progress (third-party embed) | `screen-connect-in-progress.html` | `screen-connect-in-progress.jpg` |
| Connect attempt failed | `screen-connect-failed.html` | `screen-connect-failed.jpg` |
| Transactions — success | `screen-transactions-success.html` | `screen-transactions-success.jpg` |
| Transactions — still preparing | `screen-transactions-preparing.html` | `screen-transactions-preparing.jpg` |
| Transactions — nothing found | `screen-transactions-empty.html` | `screen-transactions-empty.jpg` |
| Transactions — retrieval failed | `screen-transactions-error.html` | `screen-transactions-error.jpg` |

All seven share the app shell design-system-001 established (white top bar,
navy icon rail, "Accounts" active, later scope-map steps dimmed) so the
slice reads as part of one product from its first screen, not a standalone
demo.

**No institution connected** — the empty-state composition (centered icon,
headline, one line of explanation, primary CTA) inside the standard card.
Nothing else on the page competes with the single action available.

**Connect flow in progress** — a bounded, dashed-border card labeled
"Hosted by your data provider," with a spinner and a line clarifying that
credentials are never seen by this app. This is deliberately *not* a
faithful recreation of Plaid Link's actual interface — design-001 is
explicit that the provider ships its own hosted widget, and redesigning
someone else's product would be both wasted effort and misleading. The
frame communicates "something else's UI lives here," not what that UI
looks like.

**Connect attempt failed** — the danger-banner pattern from design-system,
placed where the embed frame was. One "Try again" action, which re-opens
the embed. This same treatment (danger banner, "Try again," still on the
connect step) is the visual home for all three connect-time failure
messages the slice and reliability-requirements-001 name: rejected
credentials, an unreachable provider, and a timed-out attempt. They're
required to be *worded* distinguishably from each other, not styled
differently — see Interaction flow below for the three message variants.

**Transactions — success** — the institution's name as the page heading
(replacing the generic "Accounts" title once a connection exists), a
"Reconnect" action in its place, and the transaction table: date,
description, amount, credit amounts in the design system's success-green,
everything else in default text color per the design-system's deliberate
departure from the reference (debits aren't red).

**The three post-connection outcomes** (preparing / empty / error) reuse
one composition: the table's card slot replaced by a centered status
block — icon-in-circle, bold title, one-line explanation, optional action.
They differ by the design system's three semantic tones (info-blue,
neutral-gray, danger-red) plus their action: "Check again" for still-
preparing (detection is manual by design, per reliability-requirements-001 —
there's no auto-poll to wait for), nothing for the genuinely-empty case
(there's nothing to retry), "Try again" for a failed retrieval. The danger
variant here covers both "partial retrieval" and "an unexpected fault," the
same reasoning as the connect-failure banner: distinguishable wording, one
visual treatment.

## Interaction flow

1. **First visit, nothing connected.** The Accounts page shows the empty
   state. Nothing is retrieved, nothing is claimed — the copy says
   explicitly that nothing happens until a connection is made.
2. **User selects "Connect an institution."** The page transitions to the
   connect step and hands off to the provider's embedded widget. The user
   searches for and authenticates with their institution entirely inside
   that widget; this app never sees the input. A "Cancel" link gives an
   explicit way back to the empty state without completing anything (user
   stays in control).
3. **The provider calls back.** Three outcomes:
   - **Rejected credentials** — banner: *"Couldn't connect to Chase. Chase
     didn't accept the login details provided. Nothing was saved."*
     "Try again" re-opens the embed.
   - **Provider unreachable** — same visual treatment, different wording:
     *"Couldn't reach Chase's provider right now. This may be temporary —
     try again in a few minutes."* Worded so it's not mistaken for a
     credentials problem, per reliability-requirements-001.
   - **Timed out** (~2 minutes with no response) — *"Connecting to Chase is
     taking longer than expected. Try again."*
   - **Success** — the page transitions to the transaction view for that
     institution.
4. **Transaction view, first load after connecting.** One of three things
   is true, and the screen says which:
   - Transactions are ready → the table, populated.
   - The provider hasn't finished preparing history yet → the still-
     preparing state, with a manual "Check again" (no auto-refresh — this
     app makes no unprompted retries, per reliability-requirements-001's
     "no automatic retry" decision, which this extends to the readiness
     check for consistency).
   - The provider finished and genuinely has nothing for the period → the
     nothing-found state. Explicitly not phrased as an error, and worded
     differently from still-preparing so the two are never confused.
5. **A later retrieval fails** (partial data, or an unexpected fault) after
   a connection already succeeded → the retrieval-failed state replaces the
   table. Nothing partial is ever shown; the copy says plainly that nothing
   changed and offers "Try again."
6. **Reconnecting the same institution.** "Reconnect" re-enters the connect
   flow from the transaction view. Per slice-001's own criterion, a
   completed reconnect replaces the listed transactions with the newest
   full retrieval rather than appending — the table shown afterward is a
   fresh render of state 4, not a merge.

Every transaction description renders as literal text, never interpreted as
markup — security-requirements-001's untrusted-merchant-text criterion,
satisfied by construction rather than left to the implementation to
remember.

## New patterns proposed, if any

None that need a separate entry in `design-system`. The embed frame and the
centered status-block composition (icon, title, description, optional
action) are both built entirely from existing tokens and the existing card
pattern — no new color, radius, spacing, or component was needed. Worth
noting for whoever designs the next screen that needs an empty/status
state: this composition is likely to recur (the reliability and security
docs for later scope-map steps will very plausibly need the same shape),
and folding it into `design-system` as a named pattern once a second
screen actually uses it would save re-deriving it here.

## Open questions

None left open by this screen design. The one thing that looked like a
choice — whether the user names an institution through our own UI before
handing off, versus doing it entirely inside the provider's widget — is
already resolved by design-001: the provider's embedded flow includes its
own institution search, so this app never needs a picker of its own for
slice 1's single-institution scope.
