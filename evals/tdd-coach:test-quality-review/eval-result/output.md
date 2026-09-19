Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/test-quality-review/SKILL.md

## Test Review: pricing.test.ts

### Summary

8 tests reviewed. 2 Critical (a test that mocks the exact method it claims to exercise, and a test whose assertions target objects the code under test never receives, so they can never fail). 1 test is not a quality problem at all but is worth flagging first because it changes the suite's pass/fail status: `isValidCustomerId accepts a real id` expects `true` but, read against the implementation as given, the function returns `false` for every ordinary string — this test is currently red, and it's red for the right reason (it caught a real bug). 3 High findings (a false-positive bound check on money rounding, a dead mock that never gets wired to anything, and thin edge-case coverage on the customer-id guard). Several Medium missing-coverage gaps, including one exported function with zero tests. Overall: **CRITICAL ISSUES** — roughly half of this file's tests would pass regardless of whether `PricingService` is implemented correctly, and the one test that's actually strict enough to catch a bug is failing.

### Findings

## Finding: `service.calculateTotal` is mocked in the test named for it

**Location:** `calculateTotal returns the discounted total`
**Category:** Mocking the code under test
**Severity:** Critical

**What's happening:**
```js
vi.spyOn(service, 'calculateTotal').mockReturnValue(999);
const result = service.calculateTotal([{ price: 100, qty: 1 }], 'cust-1');
expect(result).toBe(999);
```
The test replaces `calculateTotal` itself with a stub, then calls the stub and asserts it returned what it was told to return.

**Why it matters:** This test passes no matter how `calculateTotal` is implemented — delete the real method body entirely and it still goes green. It contributes nothing to confidence in pricing correctness despite its name suggesting otherwise.

**Suggested fix:** Delete this test. `calculates total with discount` already covers the real discounted-total path with a genuine assertion; this one adds nothing and actively misleads anyone scanning test names for coverage.

---

## Finding: Assertions target mocks the code under test never receives

**Location:** `uses a mocked discount client, logger, cache, and audit trail`
**Category:** A mock that doesn't actually intercept anything / useless test
**Severity:** Critical

**What's happening:**
```js
const service = new PricingService(discounts as any);
service.calculateTotal([{ price: 50, qty: 2 }], 'cust-2');
expect(logger.log).not.toHaveBeenCalled();
expect(cache.get).not.toHaveBeenCalled();
expect(audit.record).not.toHaveBeenCalled();
```
`PricingService`'s constructor takes only a `DiscountLookup`. `logger`, `cache`, and `audit` are never passed to it — they're local objects with no wiring into the system under test at all. The three assertions check that functions were never called on objects the service has literally no reference to.

**Why it matters:** These assertions cannot fail under any implementation of `PricingService`, correct or broken — there's no code path by which the service could reach `logger`, `cache`, or `audit`. Worse, the actual return value of `calculateTotal` — the one thing this call produces — is never even captured, let alone asserted. This test can never turn red.

**Suggested fix:** Delete this test. If there's a real intent to verify `PricingService` doesn't perform logging/caching/audit side effects, that only makes sense once those are real constructor dependencies — at which point it becomes a normal "dependency not called" assertion on a wired-in double, not four unconnected mocks.

---

## Finding: `isValidCustomerId accepts a real id` contradicts the implementation as given — not a quality defect, worth flagging separately

**Location:** `isValidCustomerId accepts a real id`
**Category:** N/A — this isn't a test-quality issue; it's the opposite. Flagging because it directly answers "are these tests testing anything."
**Severity:** N/A (but it currently fails the suite)

**What's happening:**
```ts
export function isValidCustomerId(input: unknown): input is string {
  return typeof input === 'object' && 'length' in (input as any) && (input as any).length > 0;
}
```
```js
expect(isValidCustomerId('cust-1')).toBe(true);
```
`typeof 'cust-1'` is `'string'`, never `'object'`, so `isValidCustomerId('cust-1')` evaluates to `false`. As written, `.toBe(true)` fails.

**Why it matters:** This is the one test in the file doing its job correctly — it asserts an exact, meaningful outcome and it's currently catching a real defect (the guard checks for `'object'` where it should check for `'string'`, so it rejects every genuine string customer id). That's worth calling out on its own: it means this suite, as given, does not currently pass — the "PASS/FAIL" question isn't hypothetical.

**Suggested fix:** Not a test change — this is `pricing.ts`'s bug to fix (outside this review's scope, which only reports on tests). Leaving it here so whoever picks this up doesn't mistake "some tests here are meaningless" for "all of them are, and none are currently red."

---

## Finding: Rounding test asserts a bound, not the actual rounded value

**Location:** `rounds correctly`
**Category:** Useless tests and false positives
**Severity:** High (money-rounding correctness, not just style)

**What's happening:**
```js
const result = service.applyRounding(9.005);
expect(result).toBeGreaterThan(0);
```
`applyRounding` exists specifically to handle the floating-point edge cases in `Math.round(amount * 100) / 100`. `9.005` is a classic case where `9.005 * 100` doesn't land on `900.5` exactly due to float representation. `toBeGreaterThan(0)` passes for virtually any positive number `applyRounding` could produce, correct or not.

**Why it matters:** The one test for this method verifies nothing about what it's actually supposed to guarantee (correct 2-decimal rounding). A regression that breaks rounding — the exact bug this function exists to prevent — would ship silently in a pricing codebase, where a rounding error is a real money-correctness bug, not a cosmetic one.

**Suggested fix:** Assert the exact expected output, e.g. `expect(service.applyRounding(9.005)).toBe(9)` (verify the actual value `Math.round(9.005 * 100) / 100` produces before hardcoding it), and add a case with an unambiguous input (e.g. `1.005` → `1` or whatever the real float behavior is) so the test documents the rounding behavior precisely rather than gesturing at "some positive number came out."

---

## Finding: `mockDiscountFor` is created but never wired to the stub it's supposed to override

**Location:** `applies zero discount when lookup fails`
**Category:** A mock that doesn't actually intercept anything
**Severity:** High

**What's happening:**
```js
const discounts = new StubDiscountLookup();
const mockDiscountFor = vi.fn().mockReturnValue(0.5);
const service = new PricingService(discounts);
const total = service.calculateTotal([{ price: 100, qty: 1 }], 'cust-3');
expect(total).toBe(100);
```
`mockDiscountFor` is never attached to `discounts` (no `vi.spyOn(discounts, 'discountFor').mockImplementation(mockDiscountFor)` or similar) — it's dead code. `discounts.discountFor` is left at `StubDiscountLookup`'s default, which per this codebase's convention always returns `0`. The assertion passes only because `0` discount happens to also yield `100`, coincidentally matching what the (unused) `0.5` mock would *not* have produced.

**Why it matters:** The test name claims to exercise "lookup fails," but nothing about a failure — an exception, a rejected promise, an error return — is ever simulated. It's actually just re-testing the zero-discount default path a second time, under a misleading name, with a red herring mock sitting in the test body that would fool a future reader into thinking failure behavior is covered when it isn't.

**Suggested fix:** Either wire `mockDiscountFor` in for real (`vi.spyOn(discounts, 'discountFor').mockImplementation(mockDiscountFor)`) if the intent was to test a non-zero/failure discount value, or — if `PricingService` has no actual "lookup failure" handling (nothing in `pricing.ts` catches an error from `discountFor`) — delete this test and rename/keep the default-discount case only once, since `calculates total with discount` plus the implicit zero-discount default already cover the two states that exist.

---

## Finding: `formatReceiptLine` has zero tests

**Location:** whole file (missing)
**Category:** Missing coverage
**Severity:** Medium

**What's happening:** `formatReceiptLine` is exported from `pricing.ts` and has no corresponding test anywhere in `pricing.test.ts`.

**Why it matters:** An exported, presumably user-facing formatting function (receipt line display) has no verification of its output format at all — a change to the `${qty} x $${price.toFixed(2)}` format would go unnoticed.

**Suggested fix:** Add a test asserting the exact string, e.g. `expect(formatReceiptLine({ price: 9.5, qty: 3 })).toBe('3 x $9.50')` — pick a price that exercises `toFixed(2)`'s padding behavior (a single decimal digit input) so the test actually checks the formatting, not just concatenation.

---

## Finding: `calculateTotal`'s summing across multiple line items is never asserted

**Location:** whole file (missing)
**Category:** Missing coverage
**Severity:** Medium

**What's happening:** Every test that captures and asserts on `calculateTotal`'s return value passes an array with exactly one item. The one test with `qty: 2` (`uses a mocked discount client...`) never asserts the return value at all (see the Critical finding above). The `reduce((sum, i) => sum + i.price * i.qty, 0)` line — summing multiple distinct line items — has no test with an asserted exact value.

**Why it matters:** A single-item array can't distinguish "correctly sums N items" from "just returns the one item's price × qty" — e.g., a bug that used `items[0]` instead of `reduce` would pass every current test.

**Suggested fix:** Add a case like `calculateTotal([{price: 10, qty: 2}, {price: 5, qty: 1}], 'cust-x')` against a stub with a known discount, with the exact expected total asserted.

---

## Finding: `isValidCustomerId` edge-case coverage doesn't reach the shapes most likely to break its guard logic

**Location:** `isValidCustomerId accepts a real id`, `isValidCustomerId rejects an empty object`
**Category:** Incomplete edge-case coverage on a guard/validator
**Severity:** High

**What's happening:** Only two shapes are tried: a string, and `{}`. Given the guard's actual logic (`typeof input === 'object' && 'length' in input && input.length > 0`), the shapes that would actually expose its behavior are untested — most notably an array with items (`['a']`), which is `typeof 'object'`, has a numeric `length`, and would make the guard return `true` even though an array is not a valid customer id. `null` and `undefined` are also untested, and `'length' in null` throws rather than returning false.

**Why it matters:** This function is a type guard (`input is string`) whose entire job is to correctly narrow arbitrary input down to valid string ids before they're used downstream (e.g., fed into `discountFor`). The untested shapes are exactly the ones that would slip a non-string value past the guard into the discount-lookup path, or crash the guard outright on `null`.

**Suggested fix:** Add cases for `isValidCustomerId(['a'])` (documents whether arrays should be accepted — almost certainly should assert `false`, which the current implementation gets wrong), `isValidCustomerId(null)`, and `isValidCustomerId(undefined)`.

---

## Finding: The `undefined`-items branch is only reachable by bypassing the type system

**Location:** `returns 0 for undefined items`
**Category:** Defensive code the tests reveal as unneeded
**Severity:** Medium

**What's happening:** The test needs `// @ts-expect-error` to call `calculateTotal(undefined, 'cust-1')` at all, and the source itself comments: `// items is required by the type; callers can't pass undefined`.

**Why it matters:** The test is fine on its own terms (exact assertion, real branch), but its own existence — needing a type-system bypass to reach the branch — is exactly the signal this review category is meant to surface: no caller within this codebase's own type contract can hit this path. Not a bug, just worth naming rather than treating as ordinary coverage.

**Suggested fix:** Nothing required of the test. If `pricing.ts` is ever touched for another reason, this is a candidate to flag to whoever owns that code — whether the guard is still worth keeping (e.g., because JS callers outside the type system exist) is not this review's call.

### What's working

`calculates total with discount` is the model the rest of the file should follow: it configures `StubDiscountLookup` the sanctioned way (`vi.spyOn(discounts, 'discountFor').mockReturnValue(0.1)` on the designated test double, not a hand-rolled mock), exercises the real `calculateTotal`, and asserts an exact numeric result (`90`) rather than a bound or "it ran without throwing." `isValidCustomerId rejects an empty object` is also a genuine, correctly-passing exact-value assertion given the current implementation.
