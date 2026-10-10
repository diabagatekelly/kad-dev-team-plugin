import type { Router } from 'express-lite';
import type { SearchCatalog } from '../../catalog/search-catalog';
import type { ErrorReporter } from '../monitoring/error-reporter';

export function registerCatalogRoutes(router: Router, search: SearchCatalog, errors: ErrorReporter): void {
  router.get('/books/search/:terms', async (req, res) => {
    try {
      res.status(200).json(await search.run(req.params.terms));
    } catch (error) {
      errors.capture(error, { path: req.path });
      res.status(503).json({ error: 'search is unavailable' });
    }
  });
}
