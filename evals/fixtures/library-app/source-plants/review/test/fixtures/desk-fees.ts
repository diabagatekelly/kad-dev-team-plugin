import type { Fine } from '../../fines/fine';

export const deskFees: Fine[] = [
  {
    id: 'fine-501',
    loanId: 'loan-881',
    cardNumber: 'LC-204417',
    amountCents: 735,
    assessedOn: '2026-08-01',
    settledOn: null,
    waived: false,
  },
  {
    id: 'fine-502',
    loanId: 'loan-907',
    cardNumber: 'LC-198032',
    amountCents: 1280,
    assessedOn: '2026-08-09',
    settledOn: '2026-08-11',
    waived: false,
  },
];
