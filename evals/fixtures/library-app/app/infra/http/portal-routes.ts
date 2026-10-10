import type { Router } from 'express-lite';
import type { LoanHistory } from '../../lending/loan-history.port';
import type { LoanStore } from '../../lending/loan-store.port';
import type { MemberDirectory } from '../../members/member-directory.port';
import type { Respond } from './respond';
import { sessionOf } from './sessions';

export interface PortalReaders {
  members: MemberDirectory;
  loans: LoanStore;
  history: LoanHistory;
}

export function registerPortalRoutes(router: Router, readers: PortalReaders, respond: Respond): void {
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
}
