PASS

The OrderRepository query surfaces domain/case-directory.ts (and related
CaseDirectory/case-directory.types.ts/mongo-case-directory.ts) despite the
literal name mismatch, states the shared shape explicitly ("exported
function names shaped as find-by-id and list-by-status, the same two
method shapes described for OrderRepository"), and explicitly declines to
render a reuse verdict, handing that off to architecture-design/
tdd-implementation instead.
