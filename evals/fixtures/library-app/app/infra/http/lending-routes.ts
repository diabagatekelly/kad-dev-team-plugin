import type { HttpRequest, Router } from 'express-lite';
import type { CheckoutBook } from '../../lending/checkout-book';
import type { PlaceHold } from '../../lending/place-hold';
import type { RenewLoan } from '../../lending/renew-loan';
import type { ReturnBook } from '../../lending/return-book';
import type { Respond } from './respond';

export interface LendingUseCases {
  checkout: CheckoutBook;
  returnBook: ReturnBook;
  renew: RenewLoan;
  placeHold: PlaceHold;
}

export function registerLendingRoutes(router: Router, useCases: LendingUseCases, respond: Respond): void {
  router.post('/loans', async (req, res) => {
    const cardNumber = String(req.body.cardNumber ?? '');
    const isbn = String(req.body.isbn ?? '');
    await respond(req, res, 201, () => useCases.checkout.run(cardNumber, isbn));
  });

  router.post('/loans/:id/return', async (req, res) => {
    await respond(req, res, 204, () => useCases.returnBook.run(req.params.id));
  });

  router.post('/loans/:id/renew', async (req, res) => {
    await respond(req, res, 200, async () => (await useCases.renew.run(req.params.id)).record);
  });

  router.post('/holds/:isbn', async (req: HttpRequest, res) => {
    await respond(req, res, 201, () => useCases.placeHold.run(req));
  });
}
