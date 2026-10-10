import { MailClient } from 'mail-sdk';
import type { Mailer } from '../../notifications/mailer.port';

export class SendgridMailer implements Mailer {
  private readonly client: MailClient;

  constructor(apiKey: string) {
    this.client = new MailClient(apiKey);
  }

  async send(to: string, subject: string, body: string): Promise<void> {
    await this.client.send({ to, subject, body });
  }
}
