import { OrmRepository, OrmRow, PgClient } from 'pg-orm';
import type { CatalogReader } from '../catalog/catalog-reader.port';
import { Loan } from './loan';

class LoanRow extends OrmRow {
  id!: string;
  isbn!: string;
  card_number!: string;
  checked_out_on!: string;
  due_on!: string;
  returned_on!: string | null;
  renewals!: number;
}

export class CheckoutBook {
  private readonly loans: OrmRepository<LoanRow>;

  constructor(
    client: PgClient,
    private readonly catalog: CatalogReader,
    private readonly clock: () => Date,
  ) {
    this.loans = new OrmRepository<LoanRow>(client, 'loans');
  }

  async run(cardNumber: string, isbn: string): Promise<LoanRow> {
    const book = await this.catalog.findByIsbn(isbn);
    if (!book) {
      throw new Error(`no book ${isbn}`);
    }
    const onLoan = await this.loans.findMany({ isbn, returned_on: null });
    if (onLoan.length >= book.copiesOwned) {
      throw new Error(`no copy of ${isbn} is available`);
    }
    const open = await this.loans.findMany({ card_number: cardNumber, returned_on: null });
    if (open.length >= Loan.policy.maxOpenLoans) {
      throw new Error(`card ${cardNumber} has reached the loan limit`);
    }
    const now = this.clock();
    const row = await this.loans.insert({
      isbn,
      card_number: cardNumber,
      checked_out_on: now.toISOString(),
      due_on: Loan.policy.dueDate(now).toISOString(),
      returned_on: null,
      renewals: 0,
    });
    return row;
  }
}
