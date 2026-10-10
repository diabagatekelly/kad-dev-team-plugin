import { PgClient } from 'pg-orm';
import type { ReportQueries } from '../../reporting/report-queries.port';

export class PostgresReportQueries implements ReportQueries {
  constructor(private readonly client: PgClient) {}

  runSql<T>(sql: string, params: unknown[] = []): Promise<T[]> {
    return this.client.query<T>(sql, params);
  }
}
