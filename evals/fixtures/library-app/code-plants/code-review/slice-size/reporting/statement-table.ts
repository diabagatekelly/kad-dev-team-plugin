// One printed line per statement entry, for the desk's paper copy.

export type StatementEntry =
  | { kind: "loan"; title: string; dueOn: string }
  | { kind: "return"; title: string; returnedOn: string; daysLate: number }
  | { kind: "renewal"; title: string; newDueOn: string; renewalsLeft: number }
  | { kind: "hold-placed"; title: string; position: number }
  | { kind: "hold-ready"; title: string; holdUntil: string }
  | { kind: "hold-cancelled"; title: string; byStaff: boolean }
  | { kind: "fine"; reason: string; cents: number; assessedOn: string }
  | { kind: "payment"; cents: number; paidOn: string; method: "card" | "cash" | "waived" }
  | { kind: "waiver"; cents: number; reason: string; staffInitials: string }
  | { kind: "card-replaced"; oldCardNumber: string; newCardNumber: string }
  | { kind: "note"; text: string };

function money(cents: number): string {
  const sign = cents < 0 ? "-" : "";
  const abs = Math.abs(cents);
  return `${sign}$${Math.floor(abs / 100)}.${String(abs % 100).padStart(2, "0")}`;
}

function plural(n: number, word: string): string {
  return `${n} ${word}${n === 1 ? "" : "s"}`;
}

export function describeEntry(entry: StatementEntry): string {
  switch (entry.kind) {
    case "loan":
      return `Borrowed "${entry.title}", due ${entry.dueOn}.`;
    case "return": {
      if (entry.daysLate <= 0) {
        return `Returned "${entry.title}" on ${entry.returnedOn}, on time.`;
      }
      return `Returned "${entry.title}" on ${entry.returnedOn}, ${plural(entry.daysLate, "day")} late.`;
    }
    case "renewal": {
      const left =
        entry.renewalsLeft === 0
          ? "no renewals left"
          : `${plural(entry.renewalsLeft, "renewal")} left`;
      return `Renewed "${entry.title}" until ${entry.newDueOn} (${left}).`;
    }
    case "hold-placed": {
      if (entry.position === 1) {
        return `Placed a hold on "${entry.title}", next in line.`;
      }
      return `Placed a hold on "${entry.title}", position ${entry.position} in the queue.`;
    }
    case "hold-ready":
      return `"${entry.title}" is ready to collect, held until ${entry.holdUntil}.`;
    case "hold-cancelled": {
      if (entry.byStaff) {
        return `Hold on "${entry.title}" cancelled at the desk.`;
      }
      return `Hold on "${entry.title}" cancelled by you.`;
    }
    case "fine":
      return `Fine of ${money(entry.cents)} assessed on ${entry.assessedOn}: ${entry.reason}.`;
    case "payment": {
      switch (entry.method) {
        case "card":
          return `Paid ${money(entry.cents)} by card on ${entry.paidOn}.`;
        case "cash":
          return `Paid ${money(entry.cents)} in cash at the desk on ${entry.paidOn}.`;
        case "waived":
          return `${money(entry.cents)} cleared by waiver on ${entry.paidOn}.`;
      }
      break;
    }
    case "waiver":
      return `Waived ${money(entry.cents)} (${entry.reason}), approved by ${entry.staffInitials}.`;
    case "card-replaced": {
      const oldTail = entry.oldCardNumber.slice(-4);
      const newTail = entry.newCardNumber.slice(-4);
      return `Library card ending ${oldTail} replaced by one ending ${newTail}.`;
    }
    case "note":
      return entry.text.endsWith(".") ? entry.text : `${entry.text}.`;
  }
  return "";
}
