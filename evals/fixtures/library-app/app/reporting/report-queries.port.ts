export interface ReportQueries {
  runSql<T>(sql: string, params?: unknown[]): Promise<T[]>;
}
