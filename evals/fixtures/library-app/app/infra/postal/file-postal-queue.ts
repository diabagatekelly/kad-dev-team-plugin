import { appendFile } from 'node:fs/promises';
import type { Letter, PostalQueue } from '../../notifications/postal-queue.port';

export class FilePostalQueue implements PostalQueue {
  constructor(private readonly path: string) {}

  async queue(letter: Letter): Promise<void> {
    await appendFile(this.path, JSON.stringify(letter) + '\n', 'utf8');
  }
}
