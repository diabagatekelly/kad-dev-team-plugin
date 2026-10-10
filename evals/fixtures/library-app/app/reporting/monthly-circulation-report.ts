import type { ReportQueries } from './report-queries.port';

export interface CirculationRow {
  isbn: string;
  title: string;
  checkouts: number;
}

export class MonthlyCirculationReport {
  constructor(private readonly queries: ReportQueries) {}

  run(month: string): Promise<CirculationRow[]> {
    return this.queries.runSql<CirculationRow>(
      `select b.isbn, b.title, count(*)::int as checkouts
         from loans l join books b on b.isbn = l.isbn
        where to_char(l.checked_out_on, 'YYYY-MM') = $1
        group by b.isbn, b.title
        order by checkouts desc`,
      [month],
    );
  }
}
