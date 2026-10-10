import { MonitorClient } from 'monitor-sdk';

export interface ErrorReporter {
  capture(error: unknown, context: Record<string, unknown>): void;
}

export class MonitorErrorReporter implements ErrorReporter {
  private readonly client: MonitorClient;

  constructor(dsn: string) {
    this.client = new MonitorClient(dsn);
  }

  capture(error: unknown, context: Record<string, unknown>): void {
    this.client.captureException(error, context);
  }
}
