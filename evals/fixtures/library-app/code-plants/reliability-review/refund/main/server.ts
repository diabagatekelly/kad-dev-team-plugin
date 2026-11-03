import { Router, createServer, rateLimit } from 'express-lite';
import { SearchCatalog } from '../catalog/search-catalog';
import { registerCatalogRoutes } from '../infra/http/catalog-routes';
import { CollectFine } from '../fines/collect-fine';
import { RefundFine } from '../fines/refund-fine';
import { WaiveSmallFine } from '../fines/waive-small-fine';
import { registerFineRoutes } from '../infra/http/fines-routes';
import { registerLendingRoutes } from '../infra/http/lending-routes';
import { registerPortalRoutes } from '../infra/http/portal-routes';
import { createResponder } from '../infra/http/respond';
import { requireRole } from '../infra/http/sessions';
import { CheckoutBook } from '../lending/checkout-book';
import { PlaceHold } from '../lending/place-hold';
import { RenewLoan } from '../lending/renew-loan';
import { ReturnBook } from '../lending/return-book';
import { runNightly } from './jobs';
import * as wiring from './wiring';

const router = new Router();
const errors = wiring.errorReporter();
const respond = createResponder(errors);
const sessions = wiring.sessionStore();

router.use('/books', rateLimit({ perClientPerMinute: 120 }));
router.use('/loans', requireRole('staff', sessions));
router.use('/holds', requireRole('staff', sessions));
router.use('/fines', requireRole('staff', sessions));
router.use('/portal', requireRole('member', sessions));

registerCatalogRoutes(router, new SearchCatalog(wiring.publicCatalogReader()), errors);

registerLendingRoutes(
  router,
  {
    checkout: new CheckoutBook(wiring.pgClient(), wiring.catalogReader(), wiring.clock()),
    returnBook: new ReturnBook(wiring.clock()),
    renew: new RenewLoan(wiring.loanStore(), wiring.clock()),
    placeHold: new PlaceHold(wiring.holdQueue(), wiring.clock()),
  },
  respond,
);

registerFineRoutes(
  router,
  {
    collect: new CollectFine(wiring.fineLedger(), wiring.finePayments(), wiring.clock()),
    waive: new WaiveSmallFine(wiring.fineLedger(), wiring.clock()),
    refund: new RefundFine(wiring.fineLedger(), wiring.fineRefunds(), wiring.clock()),
  },
  respond,
  errors,
  wiring.stripePublishableKey,
);

registerPortalRoutes(
  router,
  {
    members: wiring.memberDirectory(),
    loans: wiring.loanStore(),
    history: wiring.loanHistory(),
  },
  respond,
);

createServer(router).listen(Number(process.env.PORT ?? 3000));

setInterval(() => {
  void runNightly();
}, 24 * 60 * 60 * 1000);
