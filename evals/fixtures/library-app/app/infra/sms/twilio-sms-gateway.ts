import { SmsClient } from 'sms-sdk';
import type { SmsGateway } from './sms-gateway.port';

export class TwilioSmsGateway implements SmsGateway {
  private readonly client: SmsClient;

  constructor(accountSid: string, authToken: string) {
    this.client = new SmsClient(accountSid, authToken);
  }

  async sendText(phone: string, body: string): Promise<void> {
    await this.client.send(phone, body);
  }
}
