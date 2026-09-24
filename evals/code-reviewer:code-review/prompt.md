---
name: code-reviewer:code-review
tags: [code-reviewer, code-review]
runs: 3
---

Review this code for readability/DRY/naming/comments issues. This PR
touches three files: `orders.ts` (below), plus two new files,
`pricing.ts` and `pricing.test.ts` (further down). Only the section marked
"New in this PR" in `orders.ts` was written or touched for this change —
`legacyCalc` above it predates this PR and wasn't touched. `pricing.ts` and
`pricing.test.ts` are both entirely new.

```typescript
// orders.ts

// Pre-existing, not touched by this PR:
function legacyCalc(a, b, c) {
  // does the math
  return a * b + c;
}

// --- New in this PR ---

function p(o, d) {
  let t = o.price * o.qty;
  // apply discount
  if (d > 0) {
    t = t - t * d;
  }
  return t;
}

function calculateShippingCost(order) {
  if (!order) return 0;
  let cost = 0;
  if (order.weight > 0) {
    cost += order.weight * 0.5;
  }
  if (order.zone === 'domestic') {
    cost += 5;
  } else if (order.zone === 'international') {
    cost += 25;
  }
  return cost;
}

function calculateHandlingFee(order) {
  if (!order) return 0;
  let cost = 0;
  if (order.weight > 0) {
    cost += order.weight * 0.5;
  }
  if (order.zone === 'domestic') {
    cost += 3;
  } else if (order.zone === 'international') {
    cost += 15;
  }
  return cost;
}

function calculateInsuranceFee(order) {
  if (!order) return 0;
  let cost = 0;
  if (order.weight > 0) {
    cost += order.weight * 0.5;
  }
  if (order.zone === 'domestic') {
    cost += 1;
  } else if (order.zone === 'international') {
    cost += 8;
  }
  return cost;
}

// Tax rate is intentionally asymmetric for digital vs. physical goods per
// state statute §7.2 — not a bug.
function applyStateTax(order) {
  const rate = order.isDigital ? 0.04 : 0.0725;
  return order.subtotal * rate;
}

async function processOrder(order) {
  if (!order.id) {
    throw new Error('missing id');
  }

  const shipping = calculateShippingCost(order);
  const handling = calculateHandlingFee(order);
  const insurance = calculateInsuranceFee(order);
  const tax = applyStateTax(order);

  const client = new Stripe(process.env.STRIPE_KEY);
  const charge = await client.charges.create({
    amount: order.subtotal + shipping + handling + insurance + tax,
    currency: 'usd',
  });

  // retried up to 5 times because the downstream inventory service
  // occasionally drops the first call under load — see INC-4821
  let inventoryUpdated = false;
  for (let i = 0; i < 3 && !inventoryUpdated; i++) {
    inventoryUpdated = await updateInventory(order.id);
  }

  return charge;
}
```

```typescript
// pricing.ts — entirely new in this PR

// Structurally identical, but only two instances so far:
function isValidSku(sku) {
  if (typeof sku !== 'string') return false;
  if (sku.length !== 8) return false;
  return true;
}

function isValidWarehouseCode(code) {
  if (typeof code !== 'string') return false;
  if (code.length !== 8) return false;
  return true;
}

// Same switch-on-kind shape, twice, both in this file:
function formatLineItem(item) {
  switch (item.kind) {
    case 'physical': return `${item.name} (ships in ${item.leadDays}d)`;
    case 'digital': return `${item.name} (instant delivery)`;
    case 'subscription': return `${item.name} (recurring)`;
    default: return item.name;
  }
}

function getLineItemIcon(item) {
  switch (item.kind) {
    case 'physical': return 'box-icon';
    case 'digital': return 'download-icon';
    case 'subscription': return 'refresh-icon';
    default: return 'default-icon';
  }
}

// Currency as a raw string, checked two different, inconsistent ways:
function chargeInUsd(amountCents, currency) {
  if (currency !== 'USD') {
    throw new Error('unsupported currency');
  }
  return amountCents / 100;
}

function formatCurrencyLabel(currency) {
  return currency.toUpperCase() === 'USD' ? '$' : currency;
}

// Reads far more of `order` than of `this`:
class OrderSummaryFormatter {
  constructor(locale) {
    this.locale = locale;
  }

  describe(order) {
    return `${order.customer.firstName} ${order.customer.lastName} ordered ` +
      `${order.items.length} item(s) totaling ${order.totals.grandTotal}, ` +
      `shipped to ${order.shipping.address.city}, ${order.shipping.address.state}`;
  }
}

// street/city/state/zip travel together across three signatures:
function validateAddress(street, city, state, zip) {
  return Boolean(street && city && state && zip);
}

function printShippingLabel(street, city, state, zip, carrier) {
  return `${carrier}: ${street}, ${city}, ${state} ${zip}`;
}

function scheduleDelivery(orderId, street, city, state, zip, carrier, requestedDate) {
  if (!validateAddress(street, city, state, zip)) {
    throw new Error('invalid address');
  }
  return { orderId, label: printShippingLabel(street, city, state, zip, carrier), requestedDate };
}

// Claims to fetch a discount; actually zeroes it out and adds a surcharge:
function getActiveDiscount(order) {
  order.discountCents = 0;
  order.surchargeCents = Math.round(order.subtotalCents * 0.02);
  return order;
}

// Vague about what kind of processing, but doesn't claim anything false:
function process(order) {
  order.processedAt = new Date().toISOString();
  return order;
}

// Long, but purely mechanical — every branch is a one-line lookup:
function getOrderStatusLabel(status) {
  switch (status) {
    case 'pending': return 'Pending';
    case 'confirmed': return 'Confirmed';
    case 'processing': return 'Processing';
    case 'awaiting_payment': return 'Awaiting Payment';
    case 'payment_failed': return 'Payment Failed';
    case 'picked': return 'Picked';
    case 'packed': return 'Packed';
    case 'label_created': return 'Label Created';
    case 'shipped': return 'Shipped';
    case 'in_transit': return 'In Transit';
    case 'out_for_delivery': return 'Out for Delivery';
    case 'delivered': return 'Delivered';
    case 'delayed': return 'Delayed';
    case 'lost_in_transit': return 'Lost In Transit';
    case 'damaged_in_transit': return 'Damaged In Transit';
    case 'return_requested': return 'Return Requested';
    case 'return_label_sent': return 'Return Label Sent';
    case 'return_in_transit': return 'Return In Transit';
    case 'returned': return 'Returned';
    case 'refund_pending': return 'Refund Pending';
    case 'refunded': return 'Refunded';
    case 'partially_refunded': return 'Partially Refunded';
    case 'cancelled': return 'Cancelled';
    case 'cancel_requested': return 'Cancellation Requested';
    case 'on_hold': return 'On Hold';
    case 'backordered': return 'Backordered';
    case 'partially_shipped': return 'Partially Shipped';
    case 'fraud_review': return 'Under Fraud Review';
    case 'fraud_confirmed': return 'Fraud Confirmed';
    case 'address_invalid': return 'Address Invalid';
    case 'customs_hold': return 'Held in Customs';
    case 'archived': return 'Archived';
    default: return 'Unknown';
  }
}

// Genuinely doing several distinct jobs, one after another:
function reconcileNightlyLedger(entries) {
  const validated = [];
  for (const entry of entries) {
    if (!entry.id) continue;
    if (typeof entry.amountCents !== 'number') continue;
    if (!entry.currency) continue;
    if (!entry.postedAt) continue;
    validated.push(entry);
  }

  const converted = [];
  for (const entry of validated) {
    let amountUsdCents = entry.amountCents;
    if (entry.currency === 'EUR') {
      amountUsdCents = Math.round(entry.amountCents * 1.08);
    } else if (entry.currency === 'GBP') {
      amountUsdCents = Math.round(entry.amountCents * 1.27);
    } else if (entry.currency === 'JPY') {
      amountUsdCents = Math.round(entry.amountCents * 0.0067 * 100);
    }
    converted.push({ ...entry, amountUsdCents });
  }

  const seen = new Set();
  const deduped = [];
  for (const entry of converted) {
    const key = `${entry.id}:${entry.postedAt}`;
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(entry);
  }

  const byCurrency = {};
  for (const entry of validated) {
    byCurrency[entry.currency] = (byCurrency[entry.currency] || 0) + entry.amountCents;
  }

  let totalCents = 0;
  let refundCents = 0;
  let chargeCents = 0;
  for (const entry of deduped) {
    totalCents += entry.amountUsdCents;
    if (entry.amountUsdCents < 0) {
      refundCents += entry.amountUsdCents;
    } else {
      chargeCents += entry.amountUsdCents;
    }
  }

  console.log(`Reconciled ${entries.length} raw entries down to ${deduped.length}`);
  console.log(`Total: ${totalCents}, charges: ${chargeCents}, refunds: ${refundCents}`);

  return {
    totalCents,
    chargeCents,
    refundCents,
    byCurrency,
    entryCount: deduped.length,
    droppedCount: entries.length - validated.length,
  };
}
```

```typescript
// pricing.test.ts — entirely new in this PR

import { chargeInUsd } from './pricing';

describe('billing', () => {
  it('t1', () => {
    const svc = { chargeInUsd: jest.fn().mockReturnValue(42) };
    const result = svc.chargeInUsd(1000, 'USD');
    expect(svc.chargeInUsd).toHaveBeenCalled();
  });

  it('t1', () => {
    const svc = { chargeInUsd: jest.fn().mockReturnValue(42) };
    const result = svc.chargeInUsd(2000, 'USD');
    expect(svc.chargeInUsd).toHaveBeenCalled();
  });
});
```
