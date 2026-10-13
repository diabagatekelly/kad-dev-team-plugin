import type { Book } from './book';
import type { CatalogReader } from './catalog-reader.port';

const MAX_RESULTS = 50;
// One character matches most of the catalog; two is the shortest useful query.
const MIN_TERMS_LENGTH = 2;

export class SearchCatalog {
  constructor(private readonly catalog: CatalogReader) {}

  async run(terms: string): Promise<Book[]> {
    const trimmed = terms.trim();
    if (trimmed.length < MIN_TERMS_LENGTH) {
      return [];
    }
    return this.catalog.search(trimmed, MAX_RESULTS);
  }
}
