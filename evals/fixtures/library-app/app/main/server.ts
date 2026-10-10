import { Router, createServer } from 'express-lite';
import { SearchCatalog } from '../catalog/search-catalog';
import { registerCatalogRoutes } from '../infra/http/catalog-routes';
import { CollectFine } from '../fines/collect-fine';
import { WaiveSmallFine } from '../fines/waive-small-fine';
import { registerFineRoutes } from '../infra/http/fines-routes';
import { registerLendingRoutes } from '../infra/http/lending-routes';
import { CheckoutBook } from '../lending/checkout-book';
import { PlaceHold } from '../lending/place-hold';
import { RenewLoan } from '../lending/renew-loan';
import { ReturnBook } from '../lending/return-book';
import { PaymentService } from '../services/payment-service';
import { runNightly } from './jobs';
import * as wiring from './wiring';

const router = new Router();

registerCatalogRoutes(router, new SearchCatalog(wiring.catalogReader()));

registerLendingRoutes(router, {
  checkout: new CheckoutBook(wiring.pgClient(), wiring.catalogReader(), wiring.clock()),
  returnBook: new ReturnBook(wiring.clock()),
  renew: new RenewLoan(wiring.loanStore(), wiring.clock()),
  placeHold: new PlaceHold(wiring.holdQueue(), wiring.clock()),
});

registerFineRoutes(router, {
  collect: new CollectFine(wiring.fineLedger(), wiring.finePayments(), wiring.clock()),
  waive: new WaiveSmallFine(wiring.fineLedger(), wiring.clock()),
  payments: new PaymentService(),
});

createServer(router).listen(Number(process.env.PORT ?? 3000));

setInterval(() => {
  void runNightly();
}, 24 * 60 * 60 * 1000);
