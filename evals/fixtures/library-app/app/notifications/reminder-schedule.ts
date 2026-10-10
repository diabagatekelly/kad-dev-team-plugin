import type { LoanRecord } from '../lending/loan';
import { daysBetween } from '../utils/date-utils';

const REMINDER_WINDOW_DAYS = 3;

export function dueSoon(loans: LoanRecord[], today: Date): LoanRecord[] {
  return loans.filter((loan) => {
    if (loan.returnedOn !== null) {
      return false;
    }
    const days = daysBetween(today, new Date(loan.dueOn));
    return days >= 0 && days <= REMINDER_WINDOW_DAYS;
  });
}
