import type { Book } from './book';

export interface CatalogReader {
  findByIsbn(isbn: string): Promise<Book | null>;
  /** Books whose title or author contains `terms`, ordered by title, at most `limit` of them. */
  search(terms: string, limit: number): Promise<Book[]>;
}

/** Thrown by a `CatalogReader` when its store cannot answer; `reason` says why. */
export class CatalogUnavailable extends Error {
  constructor(
    readonly reason: 'timeout' | 'connection' | 'query',
    options?: { cause?: unknown },
  ) {
    super(`catalog unavailable: ${reason}`, options);
  }
}
