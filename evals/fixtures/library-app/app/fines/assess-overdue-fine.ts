import type { LoanRecord } from '../lending/loan';
import type { Fine } from './fine';
import type { FineLedger } from './fine-ledger.port';

export class AssessOverdueFine {
  constructor(
    private readonly ledger: FineLedger,
    private readonly clock: () => Date,
  ) {}

  async run(loan: LoanRecord): Promise<Fine | null> {
    const today = this.clock();
    const due = new Date(loan.dueOn);
    const msLate = today.getTime() - due.getTime();
    const daysLate = Math.floor(msLate / 86_400_000);
    if (daysLate <= 0) {
      return null;
    }
    const gracePeriodDays = 3;
    const billableDays = Math.max(0, daysLate - gracePeriodDays);
    let cents = billableDays * 25;
    if (cents > 1000) {
      cents = 1000;
    }
    if (cents === 0) {
      return null;
    }
    const alreadyAssessed = (await this.ledger.outstandingFor(loan.cardNumber)).some((f) => f.loanId === loan.id);
    if (alreadyAssessed) {
      return null;
    }
    const stamp = today.getTime().toString(36);
    const nonce = Math.floor(Math.random() * 0xffff).toString(16).padStart(4, '0');
    const fine: Fine = {
      id: `${loan.id}-${stamp}-${nonce}`,
      loanId: loan.id,
      cardNumber: loan.cardNumber,
      amountCents: cents,
      assessedOn: today.toISOString().slice(0, 10),
      settledOn: null,
      waived: false,
    };
    await this.ledger.record(fine);
    return fine;
  }
}
