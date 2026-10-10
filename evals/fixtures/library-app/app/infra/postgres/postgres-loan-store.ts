import { OrmRepository, OrmRow, PgClient } from 'pg-orm';
import type { LoanRecord } from '../../lending/loan';
import type { LoanStore } from '../../lending/loan-store.port';

class LoanRow extends OrmRow {
  id!: string;
  isbn!: string;
  card_number!: string;
  checked_out_on!: string;
  due_on!: string;
  returned_on!: string | null;
  renewals!: number;
}

export class PostgresLoanStore implements LoanStore {
  private readonly rows: OrmRepository<LoanRow>;

  constructor(client: PgClient) {
    this.rows = new OrmRepository<LoanRow>(client, 'loans');
  }

  async findById(id: string): Promise<LoanRecord | null> {
    const row = await this.rows.findOne({ id });
    return row ? toRecord(row) : null;
  }

  async findOpenByCard(cardNumber: string): Promise<LoanRecord[]> {
    const rows = await this.rows.findMany({ card_number: cardNumber, returned_on: null });
    return rows.map(toRecord);
  }

  async findOpen(): Promise<LoanRecord[]> {
    const rows = await this.rows.findMany({ returned_on: null });
    return rows.map(toRecord);
  }

  async add(loan: LoanRecord): Promise<void> {
    await this.rows.insert(toRow(loan));
  }

  async update(loan: LoanRecord): Promise<void> {
    const row = await this.rows.findOne({ id: loan.id });
    if (!row) {
      throw new Error(`no loan row ${loan.id}`);
    }
    Object.assign(row, toRow(loan));
    await row.save();
  }
}

function toRecord(row: LoanRow): LoanRecord {
  return {
    id: row.id,
    isbn: row.isbn,
    cardNumber: row.card_number,
    checkedOutOn: row.checked_out_on,
    dueOn: row.due_on,
    returnedOn: row.returned_on,
    renewals: row.renewals,
  };
}

function toRow(loan: LoanRecord): Partial<LoanRow> {
  return {
    id: loan.id,
    isbn: loan.isbn,
    card_number: loan.cardNumber,
    checked_out_on: loan.checkedOutOn,
    due_on: loan.dueOn,
    returned_on: loan.returnedOn,
    renewals: loan.renewals,
  };
}
