import type { Router } from 'express-lite';
import type { CollectFine } from '../../fines/collect-fine';
import type { WaiveSmallFine } from '../../fines/waive-small-fine';
import type { PaymentService } from '../../services/payment-service';
import type { Respond } from './respond';

export interface FineUseCases {
  collect: CollectFine;
  waive: WaiveSmallFine;
  payments: PaymentService;
}

export function registerFineRoutes(
  router: Router,
  useCases: FineUseCases,
  respond: Respond,
  stripePublishableKey: string,
): void {
  router.get('/payments/config', async (req, res) => {
    res.status(200).json({ publishableKey: stripePublishableKey });
  });

  router.post('/fines/:id/pay', async (req, res) => {
    try {
      await useCases.collect.run(req.params.id, String(req.body.cardToken ?? ''));
      res.status(204).json({});
    } catch (error) {
      res.status(402).json({ error: error instanceof Error ? error.message : 'payment failed' });
    }
  });

  router.post('/fines/:id/waive', async (req, res) => {
    await respond(req, res, 200, async () => ({ waived: await useCases.waive.run(req.params.id) }));
  });

  router.post('/charges/:id/refund', async (req, res) => {
    await respond(req, res, 200, async () => ({ refundId: await useCases.payments.refund(req.params.id) }));
  });
}
