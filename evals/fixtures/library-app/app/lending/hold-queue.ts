import type { Hold } from './hold';

export interface HoldQueue {
  enqueue(hold: Hold): Promise<void>;
  headFor(isbn: string): Promise<Hold | null>;
  lengthFor(isbn: string): Promise<number>;
}
