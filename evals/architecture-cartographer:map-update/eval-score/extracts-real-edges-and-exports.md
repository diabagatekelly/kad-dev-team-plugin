PASS

All seven rows match the source exactly: both ledger files show the
order-directory internal edge, the use-case shows the mongo-refund-store
internal edge, both infra mongo files show the mongodb external package
(with mongo-order-directory also correctly retaining its internal edge to
order-directory.ts), currency-format shows no edges with only
formatCurrency exported, and exported symbols correctly reflect the
classes/interfaces/functions actually exported (not private constructor
params).
