export interface PastLoan {
  isbn: string;
  title: string;
  checkedOutOn: string;
  returnedOn: string | null;
}

export interface LoanHistory {
  forCard(cardNumber: string, titleContains: string): Promise<PastLoan[]>;
}
