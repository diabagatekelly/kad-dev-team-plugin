import { daysBetween } from '../utils/date-utils';
import type { ReportQueries } from './report-queries.port';

export interface OverdueRow {
  card_number: string;
  title: string;
  due_on: string;
  days_overdue: number;
}

export class OverdueReport {
  constructor(
    private readonly queries: ReportQueries,
    private readonly clock: () => Date,
  ) {}

  async run(month: string): Promise<OverdueRow[]> {
    const today = this.clock();
    const rows = await this.queries.runSql<Omit<OverdueRow, 'days_overdue'>>(
      `select m.card_number, b.title, l.due_on
         from loans l
         join books b on b.isbn = l.isbn
         join members m on m.card_number = l.card_number
        where l.returned_on is null
          and to_char(l.due_on, 'YYYY-MM') = $1
        order by l.due_on`,
      [month],
    );
    return rows
      .map((row) => ({ ...row, days_overdue: daysBetween(new Date(row.due_on), today) }))
      .filter((row) => row.days_overdue > 0);
  }
}
