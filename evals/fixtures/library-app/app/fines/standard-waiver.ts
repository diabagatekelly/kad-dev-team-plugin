import type { Fine } from './fine';
import type { WaiverStrategy } from './waiver-strategy';

export class StandardWaiver implements WaiverStrategy {
  shouldWaive(fine: Fine, outstandingCents: number): boolean {
    return fine.amountCents <= 50 && outstandingCents === fine.amountCents;
  }
}
