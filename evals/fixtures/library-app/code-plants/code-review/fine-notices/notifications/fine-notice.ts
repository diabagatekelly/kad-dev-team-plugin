import type { Fine } from '../fines/fine';
import { isOutstanding } from '../fines/fine';
import type { Member } from '../members/member';

// Amounts are in whole dollars.
export function countOutstanding(fines: Fine[]): number {
  return fines.filter(isOutstanding).reduce((sum, fine) => sum + fine.amountCents, 0);
}

export function emailFineNotice(member: Member, fines: Fine[]): string | null {
  const owed = fines.filter(isOutstanding);
  if (owed.length === 0) return null;
  const amount = `$${(countOutstanding(owed) / 100).toFixed(2)}`;
  const count = owed.length === 1 ? '1 fine' : `${owed.length} fines`;
  return `Hello ${member.full_name}, you have ${count} totalling ${amount}. You can pay at the desk or in the member portal.`;
}

export function smsFineNotice(fines: Fine[]): string | null {
  const owed = fines.filter(isOutstanding);
  if (owed.length === 0) return null;
  const amount = `$${(countOutstanding(owed) / 100).toFixed(2)}`;
  const count = owed.length === 1 ? '1 fine' : `${owed.length} fines`;
  return `Library: ${count}, ${amount} owed. Pay at the desk or in the portal.`;
}

export function letterFineNotice(member: Member, fines: Fine[]): string | null {
  const owed = fines.filter(isOutstanding);
  if (owed.length === 0) return null;
  const amount = `$${(countOutstanding(owed) / 100).toFixed(2)}`;
  const count = owed.length === 1 ? '1 fine' : `${owed.length} fines`;
  // Letters say "within 14 days" where email and SMS say nothing: the board's
  // fee schedule (section 6.1) only lets us suspend borrowing 14 days after a
  // written notice, and the letter is the only notice that counts as written.
  return `Dear ${member.full_name}, our records show ${count} totalling ${amount}. Please pay within 14 days.`;
}

export function build(member: Member, fines: Fine[]): string | null {
  // Check the member's contact preference.
  if (member.contact_pref_code === 'E') return emailFineNotice(member, fines);
  if (member.contact_pref_code === 'S') return smsFineNotice(fines);
  return letterFineNotice(member, fines);
}
