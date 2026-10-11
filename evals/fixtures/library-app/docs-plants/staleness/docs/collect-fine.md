# How CollectFine works

`CollectFine.run(fineId, cardToken)`:

1. Calls `ledger.find(fineId)`.
2. Throws `no fine <id>` if nothing is found.
3. Returns if `fine.settledOn` is not null or `fine.waived` is true.
4. Calls `payments.charge(cardToken, fine.amountCents, "Library fine <id>")`,
   up to three times while the outcome is not ok.
5. Maps `outcome.stripeCode` to an error message and throws if the charge
   still failed.
6. Calls `ledger.settle(fine.id, outcome.chargeId, <today>)`.
