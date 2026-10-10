import { PgClient, PgError } from 'pg-orm';
import type { Book } from '../../catalog/book';
import { type CatalogReader, CatalogUnavailable } from '../../catalog/catalog-reader.port';

interface BookRow {
  isbn: string;
  title: string;
  author: string;
  copies_owned: number;
}

function escapeLike(text: string): string {
  return text.replace(/[\\%_]/g, (ch) => `\\${ch}`);
}

export class PostgresCatalogReader implements CatalogReader {
  constructor(private readonly client: PgClient) {}

  async findByIsbn(isbn: string): Promise<Book | null> {
    const rows = await this.query('select isbn, title, author, copies_owned from books where isbn = $1', [isbn]);
    return rows.length > 0 ? toBook(rows[0]) : null;
  }

  async search(terms: string, limit: number): Promise<Book[]> {
    const rows = await this.query(
      'select isbn, title, author, copies_owned from books where title ilike $1 or author ilike $1 order by title limit $2',
      [`%${escapeLike(terms)}%`, limit],
    );
    return rows.map(toBook);
  }

  private async query(sql: string, params: unknown[]): Promise<BookRow[]> {
    try {
      return await this.client.query<BookRow>(sql, params);
    } catch (error) {
      if (error instanceof PgError) {
        throw new CatalogUnavailable(REASONS[error.code] ?? 'query', { cause: error });
      }
      throw error;
    }
  }
}

const REASONS = {
  query_timeout: 'timeout',
  connection_failed: 'connection',
  query_failed: 'query',
} as const;

function toBook(row: BookRow): Book {
  return {
    isbn: row.isbn,
    title: row.title,
    author: row.author,
    copiesOwned: row.copies_owned,
  };
}
