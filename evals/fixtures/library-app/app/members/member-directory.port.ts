import type { PgClientOptions } from 'pg-orm';
import type { Member } from './member';

export interface MemberDirectory {
  readonly connection: PgClientOptions;
  findByCard(cardNumber: string): Promise<Member | null>;
  save(member: Member): Promise<void>;
}
