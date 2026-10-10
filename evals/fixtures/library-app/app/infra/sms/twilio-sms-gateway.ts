import { SmsClient, SmsError } from 'sms-sdk';
import type { SmsGateway } from './sms-gateway.port';

const MAX_ATTEMPTS = 3;

export class TwilioSmsGateway implements SmsGateway {
  private readonly client: SmsClient;

  constructor(accountSid: string, authToken: string) {
    this.client = new SmsClient(accountSid, authToken, { timeoutMs: 5_000 });
  }

  async sendText(phone: string, body: string): Promise<void> {
    for (let attempt = 1; ; attempt++) {
      try {
        await this.client.send(phone, body);
        return;
      } catch (error) {
        if (attempt === MAX_ATTEMPTS || !isTransient(error)) {
          throw error;
        }
        await sleep(500 * 2 ** (attempt - 1));
      }
    }
  }
}

function isTransient(error: unknown): boolean {
  return error instanceof SmsError && (error.status === 408 || error.status === 429 || error.status >= 500);
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
