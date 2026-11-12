// Monthly statements: one per member with activity, written to the statements
// folder and announced to the desk by email.

export interface LoanRow {
  memberCard: string;
  memberName: string;
  memberEmail: string;
  isbn: string;
  title: string;
  dueOn: string;
  returnedOn: string | null;
}

export interface FineRow {
  memberCard: string;
  cents: number;
  assessedOn: string;
  reason: string;
}

export interface StatementSources {
  loansInMonth(month: string): Promise<LoanRow[]>;
  finesInMonth(month: string): Promise<FineRow[]>;
}

export interface StatementFiles {
  write(name: string, body: string): Promise<void>;
}

export interface DeskMail {
  send(to: string, subject: string, body: string): Promise<void>;
}

export interface StatementRun {
  month: string;
  members: number;
  files: string[];
  totalFinesCents: number;
  warnings: string[];
}

const DESK = "desk@library.example";

export async function produceMonthlyStatements(
  month: string,
  sources: StatementSources,
  files: StatementFiles,
  mail: DeskMail,
): Promise<StatementRun> {
  if (!/^\d{4}-\d{2}$/.test(month)) {
    throw new Error(`month must be YYYY-MM, got ${month}`);
  }
  const warnings: string[] = [];
  const loans = await sources.loansInMonth(month);
  const fines = await sources.finesInMonth(month);

  // Group everything by member card.
  const byMember = new Map<string, { name: string; email: string; loans: LoanRow[]; fines: FineRow[] }>();
  for (const loan of loans) {
    let entry = byMember.get(loan.memberCard);
    if (!entry) {
      entry = { name: loan.memberName, email: loan.memberEmail, loans: [], fines: [] };
      byMember.set(loan.memberCard, entry);
    }
    entry.loans.push(loan);
  }
  for (const fine of fines) {
    const entry = byMember.get(fine.memberCard);
    if (!entry) {
      warnings.push(`fine for ${fine.memberCard} with no loan this month`);
      continue;
    }
    entry.fines.push(fine);
  }

  // Work out each member's standing.
  const standings = new Map<string, { overdue: number; owedCents: number }>();
  for (const [card, entry] of byMember) {
    let overdue = 0;
    for (const loan of entry.loans) {
      if (loan.returnedOn === null && loan.dueOn < `${month}-32`) {
        overdue += 1;
      } else if (loan.returnedOn !== null && loan.returnedOn > loan.dueOn) {
        overdue += 1;
      }
    }
    let owedCents = 0;
    for (const fine of entry.fines) {
      owedCents += fine.cents;
    }
    standings.set(card, { overdue, owedCents });
  }

  // Render the CSV body for each member and write it.
  const written: string[] = [];
  let totalFinesCents = 0;
  for (const [card, entry] of byMember) {
    const standing = standings.get(card)!;
    totalFinesCents += standing.owedCents;
    let csv = "kind,title_or_reason,date,amount\n";
    for (const loan of entry.loans) {
      const title = loan.title.includes(",") ? `"${loan.title.replace(/"/g, '""')}"` : loan.title;
      const date = loan.returnedOn ?? loan.dueOn;
      csv += `loan,${title},${date},\n`;
    }
    for (const fine of entry.fines) {
      const reason = fine.reason.includes(",") ? `"${fine.reason.replace(/"/g, '""')}"` : fine.reason;
      const dollars = Math.floor(fine.cents / 100);
      const cents = String(fine.cents % 100).padStart(2, "0");
      csv += `fine,${reason},${fine.assessedOn},${dollars}.${cents}\n`;
    }
    const safeName = entry.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    const fileName = `${month}-${card}-${safeName}.csv`;
    await files.write(fileName, csv);
    written.push(fileName);
  }

  // Tell the desk what happened.
  const lines = [`Statements for ${month}: ${written.length} member(s).`];
  for (const [card, entry] of byMember) {
    const standing = standings.get(card)!;
    const owed = `${Math.floor(standing.owedCents / 100)}.${String(standing.owedCents % 100).padStart(2, "0")}`;
    lines.push(`${entry.name} (${card}): ${entry.loans.length} loan(s), ${standing.overdue} overdue, owes ${owed}`);
  }
  if (warnings.length > 0) {
    lines.push("", "Warnings:", ...warnings.map((w) => `- ${w}`));
  }
  await mail.send(DESK, `Monthly statements ${month}`, lines.join("\n"));

  return { month, members: byMember.size, files: written, totalFinesCents, warnings };
}
