import { PgClient } from 'pg-orm';
import type { Fine } from '../../fines/fine';
import type { FineLedger, FinePayment } from '../../fines/fine-ledger.port';

interface FineRow {
  id: string;
  loan_id: string;
  card_number: string;
  amount_cents: number;
  assessed_on: string;
  settled_on: string | null;
  waived: boolean;
}

interface PaymentRow {
  charge_id: string | null;
  refund_id: string | null;
}

export class PostgresFineLedger implements FineLedger {
  constructor(private readonly client: PgClient) {}

  async find(id: string): Promise<Fine | null> {
    const rows = await this.client.query<FineRow>('select * from fines where id = $1', [id]);
    return rows.length > 0 ? toFine(rows[0]) : null;
  }

  async outstandingFor(cardNumber: string): Promise<Fine[]> {
    const rows = await this.client.query<FineRow>(
      'select * from fines where card_number = $1 and settled_on is null and waived = false',
      [cardNumber],
    );
    return rows.map(toFine);
  }

  async record(fine: Fine): Promise<void> {
    await this.client.query(
      'insert into fines (id, loan_id, card_number, amount_cents, assessed_on, settled_on, waived) values ($1,$2,$3,$4,$5,$6,$7)',
      [fine.id, fine.loanId, fine.cardNumber, fine.amountCents, fine.assessedOn, fine.settledOn, fine.waived],
    );
  }

  async settle(id: string, chargeId: string, on: string): Promise<void> {
    await this.client.query('update fines set settled_on = $2, charge_id = $3 where id = $1', [id, on, chargeId]);
  }

  async waive(id: string, on: string): Promise<void> {
    await this.client.query('update fines set waived = true, waived_on = $2 where id = $1', [id, on]);
  }

  async paymentOf(id: string): Promise<FinePayment | null> {
    const rows = await this.client.query<PaymentRow>('select charge_id, refund_id from fines where id = $1', [id]);
    if (rows.length === 0 || rows[0].charge_id === null) {
      return null;
    }
    return { chargeId: rows[0].charge_id, refundId: rows[0].refund_id };
  }

  async markRefunded(id: string, refundId: string, on: string): Promise<void> {
    await this.client.query('update fines set refund_id = $2, refunded_on = $3 where id = $1', [id, refundId, on]);
  }
}

function toFine(row: FineRow): Fine {
  return {
    id: row.id,
    loanId: row.loan_id,
    cardNumber: row.card_number,
    amountCents: row.amount_cents,
    assessedOn: row.assessed_on,
    settledOn: row.settled_on,
    waived: row.waived,
  };
}
