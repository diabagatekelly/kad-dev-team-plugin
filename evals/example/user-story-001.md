# Connect one institution and see its transactions

**Not filed in any tracker.** This project has no tracking system yet. This
write-up is the trackable unit of work itself, handed directly to
`software-architect`.

## Story

As the person who currently logs into each account and retypes every
transaction into a spreadsheet, I want to connect one of my financial
institutions and see its transactions in the app, so I can find out whether
this whole approach is even possible before building anything on top of it.

## Why this one first

The unresolved question is whether a free, automatic connection to any of
my institutions exists at all. Everything else planned — categorization,
budgets, transfer recommendations — is built on transactions arriving
automatically. If that turns out to be impossible for free, it's better to
know now than after a categorization engine exists to feed.

## What ships

The app runs on my own machine. I complete a connect flow for one
institution I name, and then see either that institution's transactions or
an honest statement of why they aren't there yet.

The data provider prepares transaction history asynchronously, so a fresh
connection may genuinely have nothing to show for a short while. This work
deliberately does not promise that transactions appear on completion — it
promises I am never told "no transactions found" when the truth is "not
ready yet."

Nothing is categorized. There are no budgets. The app is not reachable from
anywhere but the machine it runs on.

## Scope boundary that must hold

This work is scoped on the condition that **the app is not network
reachable**. That condition is what makes it acceptable to ship without any
authentication or access control — there is no one to keep out.

Authentication and remote access are the very next piece of work, deliberately
sequenced immediately after this one. If this work becomes reachable from
another machine, the condition is broken and access control has to come back
into scope before it ships.

## Acceptance criteria

**Primary path**
> **Given** the app is running with no institution connected,
> **When** I complete the connect flow for the institution I named,
> **Then** transactions retrieved from that institution appear in a list,
> each showing its date, amount, and description.

**Rejected credentials**
> **Given** I am in the connect flow,
> **When** the institution rejects what I submitted,
> **Then** the app states that the connection was not established and lets
> me attempt it again, and no transaction list is shown.

**Not ready yet**
> **Given** a connection succeeded but the provider has not finished
> preparing my transaction history,
> **When** I view the list,
> **Then** the app states that my transactions are still being prepared and
> that I can check again shortly — and does not tell me none were found.

**Genuinely nothing to retrieve**
> **Given** the provider has finished preparing and the institution
> genuinely had no transactions for the period,
> **When** I view the list,
> **Then** the app states that no transactions were found, in terms I can
> tell apart from the still-preparing state above.

**Connecting the same institution twice**
> **Given** an institution is already connected and its transactions are
> listed,
> **When** I complete the connect flow for that same institution again,
> **Then** the listed transactions are the full set returned by the newest
> retrieval, not that set added to the previous one.

This last one replaces the retrieved set rather than merging into it.
Merging would require deciding what makes two transactions "the same," and
that rule hasn't been chosen. Replacement removes the need to choose it
here. It will have to be chosen when repeat refresh is built, since merging
becomes unavoidable then.

**Security — not yet written.** This work handles whatever proves my
identity to my bank, which is the highest-value thing this system will ever
hold, and it introduces credential entry into the app. Real criteria for
that are owed by `devsecops-engineer`, including a testable statement of
the not-network-reachable boundary this scope depends on. This work is not
implementable until they exist.

**Accessibility — not yet written.** This ships a connect flow and a
transaction list, both of which a person operates directly. No one on the
current roster owns writing these criteria. The gap is recorded here rather
than dropped.

## Not in this work

- Internet exposure and authentication — the next piece of work.
- Repeat or scheduled refresh, and the transaction matching rule it needs.
- Recovering a connection that breaks or expires. Rejected credentials and
  empty results are handled here; expiry is not.
- Any categorization of what's retrieved — which is why the list shows raw
  date, amount, and description.
- Every other institution, possibly permanently for any with no free route.

## Known unknowns for the architect

- **Which institution, and whether any of mine has a free automatic route.**
  I name the institution, but only from among ones reachable at no
  recurring cost. Nobody has confirmed that set is non-empty. If it's
  empty, this work can't be built as written and the requirement behind it
  needs revisiting.
- **Whether the free connection method dictates the connect flow's shape.**
  An in-app connect flow is what I want; some connection methods impose
  their own.
- **User identity.** A partner may use this later, so nothing here should
  attach transactions to a single hardcoded owner in a way the
  authentication work would then have to undo. No user accounts are built
  here.
