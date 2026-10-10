// Half-even rounding for report totals, which is what the accounting export
// expects. Fines round half-up (fines/money.ts) per the board's fee schedule;
// read LIB-2291 before unifying the two.
export function roundHalfEven(value: number): number {
  const floor = Math.floor(value);
  const fraction = value - floor;
  if (fraction > 0.5) {
    return floor + 1;
  }
  if (fraction < 0.5) {
    return floor;
  }
  return floor % 2 === 0 ? floor : floor + 1;
}
