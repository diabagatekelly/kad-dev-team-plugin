import { PgClient, PgClientOptions } from 'pg-orm';
import type { Member } from '../../members/member';
import type { MemberDirectory } from '../../members/member-directory.port';

export class PostgresMemberDirectory implements MemberDirectory {
  private readonly client: PgClient;

  constructor(readonly connection: PgClientOptions) {
    this.client = new PgClient(connection);
  }

  async findByCard(cardNumber: string): Promise<Member | null> {
    const rows = await this.client.query<Member>('select * from members where card_number = $1', [cardNumber]);
    return rows[0] ?? null;
  }

  async save(member: Member): Promise<void> {
    if (member.member_row_id === 0) {
      await this.client.query(
        'insert into members (card_number, full_name, email, phone, postal_address, status_code, contact_pref_code, membership_expires_utc, created_at_utc, updated_at_utc) values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)',
        [member.card_number, member.full_name, member.email, member.phone, member.postal_address, member.status_code, member.contact_pref_code, member.membership_expires_utc, member.created_at_utc, member.updated_at_utc],
      );
      return;
    }
    await this.client.query(
      'update members set full_name=$2, email=$3, phone=$4, postal_address=$5, status_code=$6, contact_pref_code=$7, membership_expires_utc=$8, updated_at_utc=$9, row_version=row_version+1 where member_row_id=$1 and row_version=$10',
      [member.member_row_id, member.full_name, member.email, member.phone, member.postal_address, member.status_code, member.contact_pref_code, member.membership_expires_utc, member.updated_at_utc, member.row_version],
    );
  }
}
