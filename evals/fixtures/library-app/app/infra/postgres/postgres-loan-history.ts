import { PgClient } from 'pg-orm';
import type { LoanHistory, PastLoan } from '../../lending/loan-history.port';

interface PastLoanRow {
  isbn: string;
  title: string;
  checked_out_on: string;
  returned_on: string | null;
}

export class PostgresLoanHistory implements LoanHistory {
  constructor(private readonly client: PgClient) {}

  async forCard(cardNumber: string, titleContains: string): Promise<PastLoan[]> {
    const rows = await this.client.query<PastLoanRow>(
      `select l.isbn, b.title, l.checked_out_on, l.returned_on
         from loans l join books b on b.isbn = l.isbn
        where l.card_number = $1
          and b.title ilike '%${titleContains}%'
        order by l.checked_out_on desc`,
      [cardNumber],
    );
    return rows.map((row) => ({
      isbn: row.isbn,
      title: row.title,
      checkedOutOn: row.checked_out_on,
      returnedOn: row.returned_on,
    }));
  }
}
