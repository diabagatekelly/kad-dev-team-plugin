import { addDays } from 'date-fns-lite';
import type { ContactPrefCode, Member } from './member';
import type { MemberDirectory } from './member-directory.port';

export interface RegistrationInput {
  cardNumber: string;
  fullName: string;
  email: string;
  phone?: string;
  postalAddress?: string;
  contactPreference: ContactPrefCode;
}

export class RegisterMember {
  constructor(
    private readonly members: MemberDirectory,
    private readonly clock: () => Date,
  ) {}

  async run(input: RegistrationInput): Promise<Member> {
    const existing = await this.members.findByCard(input.cardNumber);
    if (existing) {
      throw new Error(`card ${input.cardNumber} is already registered`);
    }
    const now = this.clock();
    const member: Member = {
      member_row_id: 0,
      row_version: 0,
      created_at_utc: now.toISOString(),
      updated_at_utc: now.toISOString(),
      card_number: input.cardNumber,
      full_name: input.fullName,
      email: input.email,
      phone: input.phone ?? null,
      postal_address: input.postalAddress ?? null,
      status_code: 'A',
      contact_pref_code: input.contactPreference,
      membership_expires_utc: addDays(now, 365).toISOString(),
    };
    await this.members.save(member);
    return member;
  }
}
