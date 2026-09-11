Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/reliability-requirements/SKILL.md

Answers received:
- Unavailable for an hour: "Nothing bad — I just try again later. It's my own data, there's no deadline."
- Target worth stating: "Not really a hard number. I'm willing to wait a couple minutes for it to load, but if it's going to fail I'd rather know than sit there wondering."
- Who notices: "Just me, whenever I happen to open it next. I'd like it to actually tell me what went wrong instead of just looking broken or empty."
- Existing conventions: "Nothing — greenfield, no existing error-handling pattern anywhere yet."

One decision needs your call before I write it in: the engineer proposed showing whatever partial data comes back and quietly re-fetching the rest in the background if the provider only returns some transactions on a call.

**Recommendation: fail loudly instead — show nothing and state plainly that retrieval was incomplete.** A transaction list that looks complete but isn't is worse than an empty one; this app exists so you can trust the numbers you see. Quietly re-fetching in the background compounds the problem, because it hides that anything was ever wrong while you might be looking at (and trusting) the incomplete list in the meantime.

**Alternative considered and rejected: the engineer's proposal** (show what arrived, quietly re-fetch the rest). Rejected because it's the exact failure this document exists to prevent — degrading so gracefully that nobody learns something is broken, on data where being silently wrong is more expensive than a service that visibly failed.

Approve failing loudly on partial retrieval instead? — *(scripted answer: "Yes, fail loudly — I'd rather know something's wrong than trust a list that might be missing entries without me knowing it.")* — approved.

```markdown
# Reliability requirements: Slice 1 — Connect one account and see its transactions

## What's at stake

Stated by the user, not assumed.

- **An hour of unavailability costs nothing.** The user tries again later — no deadline, no second party depending on this.
- **Detection is the user, next time they open it** — but they want the app to say clearly what went wrong, not show something that just looks broken or empty.
- **No hard latency number, but a bound matters more than speed.** The user is willing to wait a couple of minutes; what they actually want is to be told if it's going to fail rather than sit there wondering. The requirement isn't speed, it's that a bound exists at all — an unbounded hang looks identical to nothing happening.

**No availability target is being committed to.** There's no second party to be accountable to and no cost to downtime. Inventing a number here would be ceremony.

## Failure modes

This slice depends on exactly one external thing: the account data provider.

| Mode | Intended behavior | Why |
|---|---|---|
| **Provider is slow** (accepts the request, doesn't respond) | Give up after roughly a couple of minutes and state that retrieval timed out. | The most commonly missed mode — without a bound it never fails, it just never finishes, and the user sits looking at something that appears to be working. |
| **Provider is down or returns an error** | Fail loudly: state that retrieval failed and the provider was unreachable, distinct from other failure messages. | Costs nothing to surface; hiding it teaches the user to distrust the app instead of the provider. |
| **Provider returns partial data** (some but not all transactions) | Fail loudly: show no transactions, state the retrieval was incomplete. No silent background re-fetch. (Decision below.) | A transaction list that looks complete but isn't is worse than an empty one — this is a distinct failure mode from "down" or "slow," and the one most tempting to handle by quietly patching over it. |
| **Provider rejects the connection** | Expected failure, not a fault: state the institution rejected the connection, let the user retry. | Already a functional criterion in slice-001. Normal operation, not a bug — must not be reported as one. |
| **Connect flow interrupted partway** | Leave nothing behind; the user starts over cleanly. | Consistent with not holding partial state from a failed attempt. |
| **The same retrieval happens twice** | Harmless — the newest result replaces the previous set. | No duplicate-detection rule needed; a repeat call isn't a failure at all here. |

**Not a failure mode for this slice: provider rate limiting.** Plausible on a free tier, but with one user, no automatic retry (see criteria below), and manual invocation, nothing generates the request volume that would trigger it. Revisit if a future slice runs retrieval on its own schedule.

## What must be observable

Driven by one question, not by coverage: **is this slice working, and if not, where did it fail?**

For a single-user tool where detection is manual, "observable" means the user can tell these apart without opening a debugger:

- The provider rejected the connection (their problem, or the credentials, to sort out).
- The provider was unreachable or timed out (nobody's fault, retry later).
- Retrieval succeeded but was incomplete (don't trust what's shown; retry).
- The account genuinely has no transactions in the period (nothing wrong at all).
- Something in the app itself broke (a bug, and it must not be disguised as one of the four above).

That list is the observability requirement. No metrics, no telemetry, no alerting — none of it is justified by a tool with one user, manual invocation, and no cost to downtime.

## Acceptance criteria

Alongside the slice's functional criteria and its security requirements.

**A slow provider eventually fails rather than hanging**
> Given the provider accepts the request but does not respond,
> When roughly a couple of minutes have passed,
> Then the attempt ends and the app states that retrieval timed out, rather than continuing to appear busy.

**An unreachable provider is reported as such**
> Given the provider is unreachable or returns an error,
> When the user attempts to connect or retrieve,
> Then the app states that the provider could not be reached, in terms distinguishable from the connection being rejected.

**Partial retrieval shows nothing, not something**
> Given retrieval completes but the app cannot confirm it received the complete set,
> When the result is presented,
> Then no transactions are displayed and the app states the retrieval was incomplete.

**No silent background re-fetch disguised as a finished result**
> Given a partial retrieval has occurred,
> When the app decides how to proceed,
> Then it does not silently retry in the background while presenting the partial result as though it were final — any further attempt is a visible, deliberate action the user takes, not something hidden behind an apparently-complete list.

**An empty result is not an error**
> Given the account genuinely has no transactions in the period,
> When the result is presented,
> Then the app states that none were found, distinguishable from every failure message above.

**Bugs are not disguised as expected failures**
> Given an unexpected fault occurs inside the app,
> When it surfaces to the user,
> Then it is presented as an unexpected problem rather than as a provider or connection failure, and enough detail is recorded for the user to diagnose it later — subject to the security requirements' secrets-in-logs criterion.

## Decisions

**1. Partial retrieval fails loudly rather than degrading.** Approved as recommended. Show nothing; state the retrieval was incomplete. Rejected: the engineer's proposal to show whatever arrived and quietly re-fetch the rest in the background — this is the exact degrade-so-gracefully-nobody-learns-anything-is-wrong failure this document exists to prevent, made worse by hiding the retry itself. Not ADR-worthy — reversible cheaply if a later slice finds a better answer.

## Out of scope for this slice

- **Rate limiting and quota exhaustion** — not real yet at this request volume; revisit if a future slice runs retrieval unattended.
- **Monitoring, alerting, and telemetry** — not justified at this scale, and deliberately avoided rather than merely skipped, consistent with keeping the sensitive data this slice handles inside as few exits as possible.

## Open questions

None blocking this slice.
```
</content>
