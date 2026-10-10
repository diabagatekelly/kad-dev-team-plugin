export interface Fine {
  id: string;
  loanId: string;
  cardNumber: string;
  amountCents: number;
  assessedOn: string;
  settledOn: string | null;
  waived: boolean;
}

export function isOutstanding(fine: Fine): boolean {
  return fine.settledOn === null && !fine.waived;
}
