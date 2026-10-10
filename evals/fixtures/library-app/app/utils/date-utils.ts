import { differenceInCalendarDays, startOfDay } from 'date-fns-lite';

export function daysBetween(from: Date, to: Date): number {
  return differenceInCalendarDays(startOfDay(to), startOfDay(from));
}

export function isoDate(date: Date): string {
  return date.toISOString().slice(0, 10);
}
