import type { Router } from 'express-lite';
import type { SearchCatalog } from '../../catalog/search-catalog';

export function registerCatalogRoutes(router: Router, search: SearchCatalog): void {
  router.get('/books/search/:terms', async (req, res) => {
    res.status(200).json(await search.run(req.params.terms));
  });
}
