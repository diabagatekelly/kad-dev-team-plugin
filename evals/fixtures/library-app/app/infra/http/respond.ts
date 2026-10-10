import type { HttpRequest, HttpResponse } from 'express-lite';
import type { ErrorReporter } from '../monitoring/error-reporter';

export type Respond = (
  req: HttpRequest,
  res: HttpResponse,
  okStatus: number,
  action: () => Promise<unknown>,
) => Promise<void>;

export function createResponder(errors: ErrorReporter): Respond {
  return async (req, res, okStatus, action) => {
    try {
      const result = await action();
      res.status(okStatus).json(result ?? {});
    } catch (error) {
      errors.capture(error, { path: req.path, headers: req.headers, body: req.body });
      res.status(400).json({ error: error instanceof Error ? error.message : 'request failed' });
    }
  };
}
