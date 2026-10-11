// Type declarations for the third-party packages this service depends on.

declare module 'pg-orm' {
  export interface PgClientOptions {
    host: string;
    port: number;
    database: string;
    user: string;
    password?: string;
    ssl?: boolean;
    /** Rejects a query that has not completed after this many milliseconds, including time spent waiting for a pooled connection or connecting. No default: queries wait indefinitely. */
    queryTimeoutMs?: number;
    /** Upper bound on pooled connections; further queries wait for a free one (within `queryTimeoutMs`). Default 10. */
    maxConnections?: number;
  }

  /** Every failed query rejects with a `PgError`; `code` says which kind of failure it was. */
  export class PgError extends Error {
    readonly code: 'query_timeout' | 'connection_failed' | 'query_failed';
  }

  /** Opens a connection pool on first query; `end()` closes the pool. */
  export class PgClient {
    constructor(options: PgClientOptions);
    query<T = unknown>(sql: string, params?: unknown[]): Promise<T[]>;
    end(): Promise<void>;
  }

  export abstract class OrmRow {
    readonly isDirty: boolean;
    save(): Promise<void>;
    remove(): Promise<void>;
  }

  export class OrmRepository<T extends OrmRow> {
    constructor(client: PgClient, table: string);
    findOne(where: Partial<Record<keyof T, unknown>>): Promise<T | null>;
    findMany(where: Partial<Record<keyof T, unknown>>): Promise<T[]>;
    insert(values: Partial<T>): Promise<T>;
  }
}

declare module 'mail-sdk' {
  export interface MailMessage {
    to: string;
    subject: string;
    body: string;
  }

  export interface ClientOptions {
    /** Aborts a request that has not completed after this many milliseconds. No default: requests wait indefinitely. */
    timeoutMs?: number;
  }

  export class MailClient {
    constructor(apiKey: string, options?: ClientOptions);
    send(message: MailMessage): Promise<{ id: string }>;
  }
}

declare module 'sms-sdk' {
  export interface ClientOptions {
    /** Aborts a request that has not completed after this many milliseconds. No default: requests wait indefinitely. */
    timeoutMs?: number;
  }

  /** Thrown for any failed request; `status` is the provider's HTTP status (408 for a client-side timeout). */
  export class SmsError extends Error {
    readonly status: number;
  }

  export class SmsClient {
    constructor(accountSid: string, authToken: string, options?: ClientOptions);
    send(to: string, body: string): Promise<{ sid: string }>;
  }
}

declare module 'stripe-sdk' {
  export type StripeErrorCode =
    | 'card_declined'
    | 'insufficient_funds'
    | 'expired_card'
    | 'processing_error';

  export class StripeError extends Error {
    readonly code: StripeErrorCode;
  }

  export interface Charge {
    id: string;
    amount: number;
    status: 'succeeded' | 'failed';
  }

  export class StripeClient {
    constructor(secretKey: string);
    readonly charges: {
      create(params: { amount: number; currency: string; source: string; description?: string }): Promise<Charge>;
      list(params: { created?: { gte: number; lte: number } }): Promise<Charge[]>;
    };
    readonly refunds: {
      create(params: { charge: string }): Promise<{ id: string }>;
    };
  }
}

declare module 'express-lite' {
  export interface HttpRequest {
    path: string;
    params: Record<string, string>;
    query: Record<string, string>;
    body: Record<string, unknown>;
    headers: Record<string, string>;
    locals: Record<string, unknown>;
  }

  export interface HttpResponse {
    status(code: number): HttpResponse;
    json(body: unknown): void;
  }

  export type Handler = (req: HttpRequest, res: HttpResponse) => Promise<void> | void;

  export type Middleware = (req: HttpRequest, res: HttpResponse, next: () => Promise<void>) => Promise<void>;

  export class Router {
    /** Runs `middleware` before every route whose path starts with `prefix`. */
    use(prefix: string, middleware: Middleware): void;
    get(path: string, handler: Handler): void;
    post(path: string, handler: Handler): void;
  }

  /** Answers 429 once one client address exceeds `perClientPerMinute` requests in a rolling minute. */
  export function rateLimit(options: { perClientPerMinute: number }): Middleware;

  export function createServer(router: Router): { listen(port: number): void };
}

declare module 'monitor-sdk' {
  export class MonitorClient {
    /** An empty `dsn` turns reporting off: `captureException` then does nothing, without error. */
    constructor(dsn: string);
    captureException(error: unknown, context?: Record<string, unknown>): void;
  }
}

declare module 'date-fns-lite' {
  export function addDays(date: Date, days: number): Date;
  export function differenceInCalendarDays(later: Date, earlier: Date): number;
  export function isBefore(date: Date, other: Date): boolean;
  export function startOfDay(date: Date): Date;
}
