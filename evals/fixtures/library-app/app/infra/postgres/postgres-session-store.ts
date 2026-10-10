import { createHash } from 'node:crypto';
import { PgClient } from 'pg-orm';
import type { Role, Session, SessionStore } from '../http/sessions';

interface SessionRow {
  card_number: string;
  role: Role;
}

// Sessions are issued by the library's sign-in service; this service only
// looks them up. Tokens are stored as SHA-256 digests.
export class PostgresSessionStore implements SessionStore {
  constructor(private readonly client: PgClient) {}

  async find(token: string): Promise<Session | null> {
    const digest = createHash('sha256').update(token).digest('hex');
    const rows = await this.client.query<SessionRow>(
      'select card_number, role from sessions where token_sha256 = $1 and expires_at > now() and revoked_at is null',
      [digest],
    );
    return rows.length > 0 ? { cardNumber: rows[0].card_number, role: rows[0].role } : null;
  }
}
