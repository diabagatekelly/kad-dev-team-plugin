import type { ExportKind, ExportReport } from './export-report';
import type { MonthlyCirculationReport } from './monthly-circulation-report';
import type { OverdueReport } from './overdue-report';

export class ReportProcessor {
  constructor(
    private readonly circulation: MonthlyCirculationReport,
    private readonly overdue: OverdueReport,
    private readonly exporter: ExportReport,
  ) {}

  async runMonthly(month: string): Promise<string[]> {
    const lines: string[] = [];
    const circulation = await this.circulation.run(month);
    lines.push(`Circulation for ${month}: ${circulation.length} titles`);
    for (const row of circulation.slice(0, 10)) {
      lines.push(`  ${row.title}: ${row.checkouts}`);
    }
    const overdue = await this.overdue.run(month);
    lines.push(`Overdue: ${overdue.length} loans`);
    return lines;
  }

  async runAndExport(month: string): Promise<string[]> {
    const kinds: ExportKind[] = ['circulation', 'overdue'];
    return Promise.all(kinds.map((kind) => this.exporter.run(month, kind)));
  }
}
