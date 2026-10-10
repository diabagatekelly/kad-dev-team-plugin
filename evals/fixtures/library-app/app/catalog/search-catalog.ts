import type { Book } from './book';
import type { CatalogReader } from './catalog-reader.port';

export class SearchCatalog {
  constructor(private readonly catalog: CatalogReader) {}

  async run(terms: string): Promise<Book[]> {
    const trimmed = terms.trim();
    if (trimmed.length < 2) {
      return [];
    }
    const matches = await this.catalog.search(trimmed);
    return [...matches].sort((a, b) => a.title.localeCompare(b.title));
  }
}
