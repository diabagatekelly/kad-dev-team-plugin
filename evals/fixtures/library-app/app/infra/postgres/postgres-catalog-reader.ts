import { PgClient } from 'pg-orm';
import type { Book } from '../../catalog/book';
import type { CatalogReader } from '../../catalog/catalog-reader.port';

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
    const rows = await this.client.query<BookRow>(
      'select isbn, title, author, copies_owned from books where isbn = $1',
      [isbn],
    );
    return rows.length > 0 ? toBook(rows[0]) : null;
  }

  async search(terms: string, limit: number): Promise<Book[]> {
    const rows = await this.client.query<BookRow>(
      'select isbn, title, author, copies_owned from books where title ilike $1 or author ilike $1 order by title limit $2',
      [`%${escapeLike(terms)}%`, limit],
    );
    return rows.map(toBook);
  }
}

function toBook(row: BookRow): Book {
  return {
    isbn: row.isbn,
    title: row.title,
    author: row.author,
    copiesOwned: row.copies_owned,
  };
}
