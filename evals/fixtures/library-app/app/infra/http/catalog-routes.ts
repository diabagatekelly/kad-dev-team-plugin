import type { Router } from 'express-lite';
import type { SearchCatalog } from '../../catalog/search-catalog';

export function registerCatalogRoutes(router: Router, search: SearchCatalog): void {
  router.get('/books', async (req, res) => {
    const terms = String(req.params.q ?? '');
    res.status(200).json(await search.run(terms));
  });
}
