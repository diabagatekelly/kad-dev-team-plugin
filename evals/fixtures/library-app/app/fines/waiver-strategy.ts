import type { Fine } from './fine';

export interface WaiverStrategy {
  shouldWaive(fine: Fine, outstandingCents: number): boolean;
}
