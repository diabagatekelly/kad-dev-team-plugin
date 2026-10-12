import { daysBetween } from '../utils/date-utils';
import type { Loan } from './loan';

export const DAYS_LEFT_ENABLED = true;

export interface DaysLeftOptions {
  roundingMode?: 'floor' | 'ceil';
  locale?: string;
}

export type DaysLeft = { kind: 'due-in'; days: number } | { kind: 'overdue' };

export function daysLeft(loan: Loan, today: Date, options: DaysLeftOptions = {}): DaysLeft | null {
  if (!DAYS_LEFT_ENABLED) return null;
  if (loan === null || loan === undefined) {
    throw new Error('loan is required');
  }
  try {
    if (!loan.isOpen()) return null;
    const days = daysBetween(today, new Date(loan.record.dueOn));
    if (days < 0) return { kind: 'overdue' };
    return { kind: 'due-in', days };
  } catch (error) {
    throw error;
  }
}
