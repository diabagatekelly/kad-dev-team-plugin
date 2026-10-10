import type { Member } from './member';
import type { MemberDirectory } from './member-directory.port';

export class SuspendMember {
  constructor(
    private readonly members: MemberDirectory,
    private readonly clock: () => Date,
  ) {}

  async run(cardNumber: string): Promise<Member> {
    const member = await this.members.findByCard(cardNumber);
    if (!member) {
      throw new Error(`no member with card ${cardNumber}`);
    }
    if (member.status_code === 'S') {
      return member;
    }
    const suspended: Member = {
      ...member,
      status_code: 'S',
      updated_at_utc: this.clock().toISOString(),
    };
    await this.members.save(suspended);
    return suspended;
  }
}
