import { appendFile } from 'node:fs/promises';
import type { Letter, PostalQueue } from '../../notifications/postal-queue.port';
import { log } from '../logging/logger';

export class FilePostalQueue implements PostalQueue {
  constructor(private readonly path: string) {}

  async queue(letter: Letter): Promise<void> {
    try {
      await appendFile(this.path, JSON.stringify(letter) + '\n', 'utf8');
    } catch (error) {
      log.info('postal queue write skipped', { path: this.path, reason: error instanceof Error ? error.message : String(error) });
    }
  }
}
