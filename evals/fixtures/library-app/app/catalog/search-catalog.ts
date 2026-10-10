import type { Book } from './book';
import type { CatalogReader } from './catalog-reader.port';

const MAX_RESULTS = 50;

export class SearchCatalog {
  constructor(private readonly catalog: CatalogReader) {}

  async run(terms: string): Promise<Book[]> {
    const trimmed = terms.trim();
    if (trimmed.length < 2) {
      return [];
    }
    return this.catalog.search(trimmed, MAX_RESULTS);
  }
}
