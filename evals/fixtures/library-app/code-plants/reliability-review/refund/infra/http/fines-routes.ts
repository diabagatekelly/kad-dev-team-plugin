import type { Router } from 'express-lite';
import type { CollectFine } from '../../fines/collect-fine';
import { RefundTimedOut } from '../../fines/fine-refunds.port';
import { type RefundFine, RefundNotPossible, RefundRefused } from '../../fines/refund-fine';
import type { WaiveSmallFine } from '../../fines/waive-small-fine';
import { log } from '../logging/logger';
import type { ErrorReporter } from '../monitoring/error-reporter';
import type { Respond } from './respond';

export interface FineUseCases {
  collect: CollectFine;
  waive: WaiveSmallFine;
  refund: RefundFine;
}

export function registerFineRoutes(
  router: Router,
  useCases: FineUseCases,
  respond: Respond,
  errors: ErrorReporter,
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

  router.post('/fines/:id/refund', async (req, res) => {
    const fineId = req.params.id;
    try {
      const refundId = await useCases.refund.run(fineId);
      res.status(200).json({ refundId });
    } catch (error) {
      if (error instanceof RefundNotPossible) {
        log.info('refund refused', { fineId, reason: error.reason });
        res.status(409).json({ error: error.message });
        return;
      }
      if (error instanceof RefundRefused) {
        log.info('refund refused by the provider', { fineId, code: error.code });
        res.status(409).json({ error: error.message });
        return;
      }
      if (error instanceof RefundTimedOut) {
        errors.capture(error, { path: req.path, fineId, chargeId: error.chargeId });
        res.status(504).json({ error: 'The refund did not complete. Try again.' });
        return;
      }
      errors.capture(error, { path: req.path, fineId });
      res.status(500).json({ error: 'refund could not be processed' });
    }
  });
}
