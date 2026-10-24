import type { Hold } from './hold';

export interface HoldQueue {
  enqueue(hold: Hold): Promise<void>;
  headFor(isbn: string): Promise<Hold | null>;
  lengthFor(isbn: string): Promise<number>;
  /** Removes one member's hold on a title; true when there was one to remove. */
  remove(isbn: string, cardNumber: string): Promise<boolean>;
}
