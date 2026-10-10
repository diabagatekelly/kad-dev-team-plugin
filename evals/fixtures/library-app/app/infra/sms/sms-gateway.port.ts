export interface SmsGateway {
  sendText(phone: string, body: string): Promise<void>;
}
