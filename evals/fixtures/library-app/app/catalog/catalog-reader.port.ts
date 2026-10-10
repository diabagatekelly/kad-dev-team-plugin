import type { Book } from './book';

export interface CatalogReader {
  findByIsbn(isbn: string): Promise<Book | null>;
  /** Books whose title or author contains `terms`, ordered by title, at most `limit` of them. */
  search(terms: string, limit: number): Promise<Book[]>;
}
