import type { HttpRequest, HttpResponse, Router } from 'express-lite';
import type { CheckoutBook } from '../../lending/checkout-book';
import type { PlaceHold } from '../../lending/place-hold';
import type { RenewLoan } from '../../lending/renew-loan';
import type { ReturnBook } from '../../lending/return-book';

export interface LendingUseCases {
  checkout: CheckoutBook;
  returnBook: ReturnBook;
  renew: RenewLoan;
  placeHold: PlaceHold;
}

export function registerLendingRoutes(router: Router, useCases: LendingUseCases): void {
  router.post('/loans', async (req, res) => {
    const cardNumber = String(req.body.cardNumber ?? '');
    const isbn = String(req.body.isbn ?? '');
    await respond(res, 201, () => useCases.checkout.run(cardNumber, isbn));
  });

  router.post('/loans/:id/return', async (req, res) => {
    await respond(res, 204, () => useCases.returnBook.run(req.params.id));
  });

  router.post('/loans/:id/renew', async (req, res) => {
    await respond(res, 200, async () => (await useCases.renew.run(req.params.id)).record);
  });

  router.post('/books/:isbn/holds', async (req: HttpRequest, res) => {
    await respond(res, 201, () => useCases.placeHold.run(req));
  });
}

async function respond(res: HttpResponse, okStatus: number, action: () => Promise<unknown>): Promise<void> {
  try {
    const result = await action();
    res.status(okStatus).json(result ?? {});
  } catch (error) {
    res.status(400).json({ error: error instanceof Error ? error.message : 'request failed' });
  }
}
