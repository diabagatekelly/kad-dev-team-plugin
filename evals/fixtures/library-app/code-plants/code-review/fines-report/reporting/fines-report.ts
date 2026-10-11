import { StripeClient } from 'stripe-sdk';
import type { Member } from '../members/member';
import type { ReportQueries } from './report-queries.port';
import { roundHalfEven } from './rounding';

interface FineRow {
  id: string;
  card_number: string;
  amount_cents: number;
  assessed_on: string;
  settled_on: string | null;
  waived: boolean;
}

export interface FinesReportSummary {
  assessedCents: number;
  collectedCents: number;
  waivedCents: number;
  cardPaymentsCents: number;
  outstandingCents: number;
  averageFineCents: number;
  finesCount: number;
  skippedRows: number;
}

export class FinesReport {
  private readonly stripe = new StripeClient(process.env.STRIPE_SECRET_KEY ?? '');

  constructor(private readonly queries: ReportQueries) {}

  async run(month: string): Promise<FinesReportSummary> {
    if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) {
      throw new Error(`month must be YYYY-MM, got ${month}`);
    }

    const rows = await this.queries.runSql<FineRow>(
      `select id, card_number, amount_cents, assessed_on, settled_on, waived
         from fines
        where to_char(assessed_on, 'YYYY-MM') = $1`,
      [month],
    );

    const valid: FineRow[] = [];
    for (const row of rows) {
      if (!row.id || !row.card_number) continue;
      if (typeof row.amount_cents !== 'number' || row.amount_cents <= 0) continue;
      if (!row.assessed_on) continue;
      valid.push(row);
    }

    const seen = new Set<string>();
    const unique: FineRow[] = [];
    for (const row of valid) {
      if (seen.has(row.id)) continue;
      seen.add(row.id);
      unique.push(row);
    }

    const [year, monthNumber] = month.split('-').map(Number);
    const charges = await this.stripe.charges.list({
      created: { gte: Date.UTC(year, monthNumber - 1, 1) / 1000, lte: Date.UTC(year, monthNumber, 1) / 1000 - 1 },
    });
    const cardPaymentsCents = charges
      .filter((charge) => charge.status === 'succeeded')
      .reduce((sum, charge) => sum + charge.amount, 0);

    let assessedCents = 0;
    let collectedCents = 0;
    let waivedCents = 0;
    let outstandingCents = 0;
    for (const row of unique) {
      assessedCents += row.amount_cents;
      if (row.waived) {
        waivedCents += row.amount_cents;
      } else if (row.settled_on !== null) {
        collectedCents += row.amount_cents;
      } else {
        outstandingCents += row.amount_cents;
      }
    }

    const skippedRows = rows.length - unique.length;
    console.log(`fines report ${month}: ${rows.length} rows, ${unique.length} fines, ${skippedRows} skipped`);

    return {
      assessedCents,
      collectedCents,
      waivedCents,
      cardPaymentsCents,
      outstandingCents,
      averageFineCents: unique.length === 0 ? 0 : roundHalfEven(assessedCents / unique.length),
      finesCount: unique.length,
      skippedRows,
    };
  }
}

export class FineChaseList {
  constructor(private readonly minimumCents: number) {}

  shouldChase(member: Member, outstandingCents: number, today: Date): boolean {
    if (outstandingCents < this.minimumCents) return false;
    if (member.status_code !== 'A') return false;
    if (new Date(member.membership_expires_utc) <= today) return false;
    if (member.contact_pref_code === 'E') return member.email !== '';
    if (member.contact_pref_code === 'S') return member.phone !== null;
    return member.postal_address !== null;
  }
}

export function periodLabel(fromYear: number, fromMonth: number, toYear: number, toMonth: number): string {
  return `${fromYear}-${String(fromMonth).padStart(2, '0')} to ${toYear}-${String(toMonth).padStart(2, '0')}`;
}

export function monthsInPeriod(fromYear: number, fromMonth: number, toYear: number, toMonth: number): string[] {
  const months: string[] = [];
  let year = fromYear;
  let month = fromMonth;
  while (year < toYear || (year === toYear && month <= toMonth)) {
    months.push(`${year}-${String(month).padStart(2, '0')}`);
    month += 1;
    if (month > 12) {
      month = 1;
      year += 1;
    }
  }
  return months;
}

export async function runFinesReportForPeriod(
  report: FinesReport,
  fromYear: number,
  fromMonth: number,
  toYear: number,
  toMonth: number,
  includeEmpty: boolean,
  title: string,
): Promise<string[]> {
  const lines = [`${title}: ${periodLabel(fromYear, fromMonth, toYear, toMonth)}`];
  for (const month of monthsInPeriod(fromYear, fromMonth, toYear, toMonth)) {
    const summary = await report.run(month);
    if (summary.finesCount === 0 && !includeEmpty) continue;
    lines.push(`${month}: ${summary.finesCount} fines, ${summary.assessedCents} cents assessed`);
  }
  return lines;
}
