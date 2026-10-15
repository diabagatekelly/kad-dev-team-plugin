# Design: Slice 1 — A member pays an outstanding fine from the portal

## Shape

Two new portal routes beside the existing `/portal/loans` and
`/portal/history`: one lists the signed-in member's outstanding fines, one
pays a single fine. Both take the member from the session, as the existing
portal routes do. Paying reuses the `CollectFine` use case and the existing
Stripe adapter behind the `FinePayments` port; the card is tokenised in the
browser with the publishable key from `GET /payments/config`.

## Boundaries

- HTTP adapter (`infra/http/portal-routes.ts`) → `CollectFine` → `FineLedger`
  and `FinePayments` ports, as the staff pay route already does.
- No new port and no new adapter.

## Open questions

None. The design reuses what exists and adds no port or adapter.
