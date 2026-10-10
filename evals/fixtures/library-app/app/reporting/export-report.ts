import type { MonthlyCirculationReport } from './monthly-circulation-report';
import type { OverdueReport } from './overdue-report';
import type { ReportFiles } from './report-files.port';

export type ExportKind = 'circulation' | 'overdue';

export class ExportReport {
  constructor(
    private readonly circulation: MonthlyCirculationReport,
    private readonly overdue: OverdueReport,
    private readonly files: ReportFiles,
  ) {}

  async run(month: string, kind: ExportKind): Promise<string> {
    if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) {
      throw new Error(`month must be YYYY-MM, got ${month}`);
    }
    const rows: Array<Record<string, unknown>> =
      kind === 'circulation'
        ? (await this.circulation.run(month)).map((row) => ({ ...row }))
        : (await this.overdue.run(month)).map((row) => ({ ...row }));
    const header = Object.keys(rows[0] ?? {});
    let csv = '\uFEFF';
    for (let i = 0; i < header.length; i++) {
      if (i > 0) {
        csv += ',';
      }
      csv += '"' + header[i].replace(/"/g, '""') + '"';
    }
    csv += '\r\n';
    for (const row of rows) {
      for (let i = 0; i < header.length; i++) {
        if (i > 0) {
          csv += ',';
        }
        const value = row[header[i]];
        const text = value === null || value === undefined ? '' : String(value);
        if (/[",\r\n]/.test(text)) {
          csv += '"' + text.replace(/"/g, '""') + '"';
        } else {
          csv += text;
        }
      }
      csv += '\r\n';
    }
    const path = `exports/${kind}-${month}.csv`;
    await this.files.write(path, csv);
    return path;
  }
}
