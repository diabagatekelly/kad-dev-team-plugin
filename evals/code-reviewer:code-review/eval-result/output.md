Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/code-review/SKILL.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/why-comments/SKILL.md

# Code Review: orders.ts (new-in-PR section only), pricing.ts, pricing.test.ts

Scope note: `legacyCalc` in orders.ts predates this PR and was not touched — its issues are listed separately, at lower priority, below. Everything else in orders.ts under "New in this PR" is reviewed in full, as are pricing.ts and pricing.test.ts (both entirely new).

Findings are ordered most severe first.

## Finding: `getActiveDiscount` name asserts the opposite of what it does

**Location:** pricing.ts, function `getActiveDiscount`
**Category:** naming
**Severity:** Critical

**What's happening:** The function is named as if it retrieves/reads an existing discount. It actually mutates the order to set `discountCents = 0` and adds a new `surchargeCents` (2% of subtotal), then returns the mutated order.

**Why it matters:** A caller reading the name `getActiveDiscount(order)` will reasonably expect a read-only lookup. Instead it silently zeroes any discount and injects a hidden surcharge — a name that asserts the opposite of the code's effect is exactly what turns a routine edit into a production bug.

**Suggested fix:** Rename to something honest about both effects (e.g. `clearDiscountAndApplySurcharge`), and/or split into two named steps so neither effect is hidden behind a name that promises only a read.

## Finding: retry comment claims 5 attempts, code allows 3

**Location:** orders.ts, new-in-PR section, `processOrder` (inventory retry loop)
**Category:** comment
**Severity:** Critical

**What's happening:** The comment above the loop states inventory update is "retried up to 5 times... see INC-4821," but the loop is `for (let i = 0; i < 3 && !inventoryUpdated; i++)` — three attempts, not five.

**Why it matters:** This comment cites an incident number as authority, which is exactly what makes it trusted over re-deriving from the code. Anyone investigating a recurrence of INC-4821, or reasoning about retry budget, will be working from a number the code doesn't implement.

**Suggested fix:** Reconcile the two — either the comment should say "3" or the loop bound should be `i < 5`. I can't tell which is the intended retry budget from the code alone, so I'm flagging the mismatch rather than guessing which side is correct.

## Finding: three fee functions repeat the same weight/zone logic

**Location:** orders.ts, new-in-PR section — `calculateShippingCost`, `calculateHandlingFee`, `calculateInsuranceFee`
**Category:** duplication
**Severity:** High

**What's happening:** All three repeat the same weight-based surcharge (`order.weight > 0 ? order.weight * 0.5 : 0`) and the same domestic/international zone branch, differing only in the three dollar constants (5/3/1 domestic, 25/15/8 international). (All three also open with the same one-line `if (!order) return 0` guard, but that's the exempt guard-clause pattern, not part of this finding.)

**Why it matters:** Three near-identical functions mean every new fee type repeats the copy-paste, and any change to the shared weight-cost logic or zone-branch shape (e.g. a third zone) has to be found and applied by hand in three places.

**Suggested fix:** Collapse to one function taking the varying rates as data, e.g. `calculateFee(order, { domestic, international })` or a small rate table keyed by fee type driving one shared calculation. Stays within this file — no new module needed.

## Finding: unused, cryptically-named discount function

**Location:** orders.ts, new-in-PR section, function `p(o, d)`
**Category:** dead code
**Severity:** High

**What's happening:** `p` computes `order.price * order.qty` with an optional discount, but nothing shown calls it — `processOrder` builds its Stripe charge from `order.subtotal` directly. It's also named with single-letter identifiers throughout (`p`, `o`, `d`, `t`).

**Why it matters:** A discount-calculating function sitting right beside the charge pipeline but never invoked is exactly the kind of thing a future editor assumes is already wired up and doesn't re-verify — a silent business-logic gap next to money-handling code is costly to leave undiscovered.

**Suggested fix:** If discounting isn't meant to apply here, delete `p`. If it should feed into the charge, wire it in and rename it and its parameters honestly (e.g. `applyDiscount(order, discountRate)`). Whether discounting belongs in this flow at all is a product call, not mine.

## Finding: street/city/state/zip travel together across three signatures

**Location:** pricing.ts — `validateAddress`, `printShippingLabel`, `scheduleDelivery`
**Category:** data clump
**Severity:** High

**What's happening:** `street, city, state, zip` are passed as four separate positional parameters through all three functions; `scheduleDelivery` alone takes seven parameters (`orderId, street, city, state, zip, carrier, requestedDate`).

**Why it matters:** Four same-typed strings in a fixed order, repeated across three call sites, is easy to transpose (e.g. swap `city`/`state`) with nothing catching it, and a seven-parameter call site is hard to verify at a glance without checking the signature each time.

**Suggested fix:** Group `street/city/state/zip` into one `Address`-shaped object and pass that single value through all three functions instead of four positional strings. Purely local to this file.

## Finding: currency validated two different, already-inconsistent ways

**Location:** pricing.ts — `chargeInUsd`, `formatCurrencyLabel`
**Category:** primitive obsession
**Severity:** High

**What's happening:** `chargeInUsd` requires the exact string `'USD'` (case-sensitive) or throws; `formatCurrencyLabel` treats currency as USD whenever `currency.toUpperCase() === 'USD'` (case-insensitive).

**Why it matters:** Currency is a raw string with no single place owning its validation rule, and the two checks have already drifted apart on day one — `'usd'` throws in one function and is accepted in the other. A future caller has no way to know which behavior to trust.

**Suggested fix:** Introduce one shared normalization/validation function (or a small `Currency` type) that both functions call, so there's exactly one definition of "is this USD."

## Finding: duplicated switch-on-kind between two display functions

**Location:** pricing.ts — `formatLineItem`, `getLineItemIcon`
**Category:** duplication
**Severity:** High

**What's happening:** Both switch on the same `item.kind` values (`physical`, `digital`, `subscription`, default) to produce related but different per-kind display data (label text vs. icon name).

**Why it matters:** Every new item kind requires a matching case in both switches; miss one and it silently falls through to the generic `default` rather than failing loudly.

**Suggested fix:** Replace both with one lookup table keyed by `kind` (e.g. `{ physical: { label, icon: 'box-icon' }, ... }`), so a new kind is one entry instead of two switch cases.

## Finding: `reconcileNightlyLedger` does several distinct jobs from inconsistent inputs

**Location:** pricing.ts, function `reconcileNightlyLedger`
**Category:** function/class size
**Severity:** High

**What's happening:** The function validates, currency-converts, dedupes, groups by currency, and sums totals, all inline. `byCurrency` is built from `validated` (pre-dedup) using raw `entry.amountCents` (pre-conversion), while `totalCents`/`chargeCents`/`refundCents` are built from `deduped` using `entry.amountUsdCents` — two outputs of the same function, computed from different arrays in different units, with nothing marking that this is deliberate.

**Why it matters:** A reader has to hold five transformations and which array/field feeds which output in their head at once. The unit/dedup mismatch between `byCurrency` and the totals is easy to "fix" incorrectly, or leave silently broken, because nothing signals whether it's intentional.

**Suggested fix:** Split into named steps (`validateEntries`, `convertToUsd`, `dedupeEntries`, `sumByCurrency`, `summarizeTotals`) called in sequence, and make a deliberate, documented choice about whether `byCurrency` should use deduped, USD-converted amounts like the totals do.

## Finding: `OrderSummaryFormatter.describe` reads far more of `order` than of `this`

**Location:** pricing.ts, class `OrderSummaryFormatter`, method `describe`
**Category:** feature envy
**Severity:** Medium

**What's happening:** `describe(order)` reads five levels into the `order` parameter (`order.customer.firstName/lastName`, `order.items.length`, `order.totals.grandTotal`, `order.shipping.address.city/state`) and never touches `this.locale`, the class's only state.

**Why it matters:** A class wrapping unused instance state suggests it exists for a reason `describe` isn't using — a reader has to go check whether `locale` matters elsewhere before trusting it's safe to ignore.

**Suggested fix:** Either use `this.locale` to actually localize the output, or drop the class in favor of a plain function `describeOrder(order, locale)`. (Whether it needs to be a class at all edges toward a structural call, but the unused field is a local fix either way.)

## Finding: `process` gives no signal at the call site

**Location:** pricing.ts, function `process`
**Category:** naming
**Severity:** Medium

**What's happening:** `process(order)` stamps `order.processedAt` with the current time and returns the order. "process" is generic enough that a reader can't tell what it does without opening the definition.

**Why it matters:** Unlike `getActiveDiscount`, this name isn't wrong, just uninformative — every call site reads as "something happens here."

**Suggested fix:** Rename to name the actual effect, e.g. `markProcessed` or `stampProcessedAt`.

## Finding: duplicate, uninformative test names

**Location:** pricing.test.ts, `describe('billing', ...)`
**Category:** naming
**Severity:** Medium

**What's happening:** Both `it(...)` blocks are named `'t1'` — identical to each other and uninformative about what either verifies.

**Why it matters:** In a failure report, both show up as "billing > t1" with no way to tell which one broke without opening the file.

**Suggested fix:** Name each test after what it verifies (e.g. distinguish the 1000-cent and 2000-cent cases) — separate from the mocking concern noted in the hand-off section below.

## Finding: redundant comment on `p`

**Location:** orders.ts, new-in-PR section, function `p`
**Category:** comment
**Severity:** Low

**What's happening:** `// apply discount` sits directly above `if (d > 0) { t = t - t * d; }`, which already says exactly that.

**Why it matters:** Costs little, but it's a comment a reader could write themselves from the next line.

**Suggested fix:** Delete it. Moot if `p` is removed per the dead-code finding above.

---

## Watch (not yet findings)

- **`isValidSku` / `isValidWarehouseCode`** (pricing.ts): identical type-check + length-check logic, but only two call sites exist today. Per the duplication threshold, two instances is a "watch for a third," not a finding — consolidate if and when a third structurally-identical validator shows up.

## Reviewed, no issue

- **`applyStateTax`**'s comment (orders.ts) explains a non-obvious invariant (asymmetric tax rate per statute §7.2) and heads off a "looks like a bug" misreading — this earns its place under the WHY-not-WHAT test.
- **`getOrderStatusLabel`** (pricing.ts) is long (30+ cases), but every branch is a one-line, self-contained lookup — no working-memory cost across branches. Length here is not itself a violation.

## Pre-existing, out of scope for this PR (lower priority)

- **`legacyCalc`** (orders.ts): single-letter parameters (`a, b, c`) and a comment (`// does the math`) that adds no information beyond the next line. Not touched by this PR — noted for whenever this function is next edited, not required to fix now.

## Handed off, not graded here

- **pricing.test.ts**: both tests mock `chargeInUsd` entirely (`jest.fn().mockReturnValue(42)`) rather than calling the real imported function, and assert only `toHaveBeenCalled()` without checking a real return value — these would pass even if `chargeInUsd` were broken or deleted. Whether this constitutes over-mocking/a false positive is `tdd-coach:test-quality-review`'s call, not mine.
- No module-boundary or capability-scope issues observed to hand to `architecture-review` or `product-slicer`.
