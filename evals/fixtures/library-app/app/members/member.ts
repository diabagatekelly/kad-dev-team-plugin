export type StatusCode = 'A' | 'S' | 'L';
export type ContactPrefCode = 'E' | 'S' | 'P';

export interface Member {
  member_row_id: number;
  row_version: number;
  created_at_utc: string;
  updated_at_utc: string;
  card_number: string;
  full_name: string;
  email: string;
  phone: string | null;
  postal_address: string | null;
  status_code: StatusCode;
  contact_pref_code: ContactPrefCode;
  membership_expires_utc: string;
}

export function isActive(member: Member, today: Date): boolean {
  return member.status_code === 'A' && new Date(member.membership_expires_utc) > today;
}

export function isSuspended(member: Member): boolean {
  return member.status_code === 'S';
}
