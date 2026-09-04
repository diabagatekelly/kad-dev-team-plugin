---
name: software-architect:architecture-review
tags: [software-architect, architecture-review]
runs: 3
---

Review this code for architecture issues:

```
src/
  controllers/
    TransactionController.ts
    AccountController.ts
  services/
    TransactionService.ts
  models/
    Transaction.ts
    Account.ts
  repositories/
    AccountRepository.ts
```

```typescript
// domain/gateways.types.ts
import { MongoClientOptions } from 'mongodb';

export interface AccountGateway {
  findById(id: string): Promise<Account>;
  connectionOptions: MongoClientOptions;
}

// domain/link-account.use-case.ts
import { AccountGateway } from './gateways.types';
import { getAccountGateway } from '../infra/factory';

export class LinkAccountUseCase {
  private gateway: AccountGateway = getAccountGateway();

  async run(accountId: string) {
    return this.gateway.findById(accountId);
  }
}

// domain/pay-invoice.use-case.ts
import Stripe from 'stripe';
import PaypalClient from 'paypal-sdk';
import SquareClient from 'square-sdk';

export class PayInvoiceUseCase {
  async run(invoiceId: string, provider: string) {
    if (provider === 'stripe') {
      const stripe = new Stripe(process.env.STRIPE_KEY);
      return stripe.charges.create({ invoiceId });
    } else if (provider === 'paypal') {
      const paypal = new PaypalClient();
      return paypal.payments.create({ invoiceId });
    } else if (provider === 'square') {
      const square = new SquareClient();
      return square.payments.create({ invoiceId });
    }
  }
}
```

`getAccountGateway()` in `../infra/factory` constructs a concrete
Mongo-backed implementation of `AccountGateway` and returns it typed as
the interface; nothing outside `infra/factory` ever imports the concrete
class.
