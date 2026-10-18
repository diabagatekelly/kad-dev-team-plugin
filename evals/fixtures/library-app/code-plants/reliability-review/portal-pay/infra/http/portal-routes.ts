import type { Router } from 'express-lite';
import type { FineLedger } from '../../fines/fine-ledger.port';
import { FineNotFound, type PayOwnFine, PaymentDeclined, PaymentTimedOut } from '../../fines/pay-own-fine';
import type { LoanHistory } from '../../lending/loan-history.port';
import type { LoanStore } from '../../lending/loan-store.port';
import type { MemberDirectory } from '../../members/member-directory.port';
import { log } from '../logging/logger';
import type { ErrorReporter } from '../monitoring/error-reporter';
import type { Respond } from './respond';
import { sessionOf } from './sessions';

export interface PortalReaders {
  members: MemberDirectory;
  loans: LoanStore;
  history: LoanHistory;
  fines: FineLedger;
}

export interface PortalUseCases {
  payFine: PayOwnFine;
}

export function registerPortalRoutes(
  router: Router,
  readers: PortalReaders,
  useCases: PortalUseCases,
  respond: Respond,
  errors: ErrorReporter,
): void {
  router.get('/portal/loans', async (req, res) => {
    await respond(req, res, 200, () => readers.loans.findOpenByCard(sessionOf(req).cardNumber));
  });

  router.get('/portal/history', async (req, res) => {
    const titleContains = String(req.query.title ?? '');
    await respond(req, res, 200, () => readers.history.forCard(sessionOf(req).cardNumber, titleContains));
  });

  router.get('/portal/members/:cardNumber', async (req, res) => {
    await respond(req, res, 200, async () => {
      const member = await readers.members.findByCard(req.params.cardNumber);
      if (!member) {
        throw new Error('member not found');
      }
      return {
        cardNumber: member.card_number,
        name: member.full_name,
        email: member.email,
        phone: member.phone,
        postalAddress: member.postal_address,
        membershipExpires: member.membership_expires_utc,
      };
    });
  });

  router.get('/portal/fines', async (req, res) => {
    await respond(req, res, 200, () => readers.fines.outstandingFor(sessionOf(req).cardNumber));
  });

  router.post('/portal/fines/:id/pay', async (req, res) => {
    const fineId = req.params.id;
    try {
      await useCases.payFine.run(sessionOf(req).cardNumber, fineId, String(req.body.cardToken ?? ''));
      res.status(204).json({});
    } catch (error) {
      if (error instanceof FineNotFound) {
        // Another member's fine gets the same answer as a missing one; the reason stays server-side.
        log.info('portal payment refused', { fineId, reason: error.reason });
        res.status(404).json({ error: error.message });
        return;
      }
      if (error instanceof PaymentDeclined) {
        res.status(402).json({ error: error.message });
        return;
      }
      if (error instanceof PaymentTimedOut) {
        res.status(504).json({ error: 'Payment failed, please try again.' });
        return;
      }
      errors.capture(error, { path: req.path, fineId });
      res.status(500).json({ error: 'payment could not be processed' });
    }
  });
}
