import type { HttpRequest, Middleware } from 'express-lite';

export type Role = 'member' | 'staff';

export interface Session {
  cardNumber: string;
  role: Role;
}

export interface SessionStore {
  find(token: string): Promise<Session | null>;
}

export function requireRole(role: Role, sessions: SessionStore): Middleware {
  return async (req, res, next) => {
    const token = bearerToken(req.headers.authorization);
    const session = token ? await sessions.find(token) : null;
    if (!session || session.role !== role) {
      res.status(401).json({ error: 'sign in required' });
      return;
    }
    req.locals.session = session;
    await next();
  };
}

export function sessionOf(req: HttpRequest): Session {
  return req.locals.session as Session;
}

function bearerToken(header: string | undefined): string | null {
  const match = /^Bearer (\S+)$/.exec(header ?? '');
  return match ? match[1] : null;
}
