import type { Book } from './book';

export interface CatalogReader {
  findByIsbn(isbn: string): Promise<Book | null>;
  search(terms: string): Promise<Book[]>;
}
