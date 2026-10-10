// Fines round half-up at the cent, as published in the library board's fee
// schedule (section 4.2). Reports round half-even because that is what the
// accounting export expects. The two were unified once and the fines the
// board had published stopped matching what members were charged (LIB-2291),
// so this stays separate from reporting/rounding.ts on purpose.
export function roundHalfUpCents(value: number): number {
  return Math.floor(value + 0.5);
}

export function percentOf(cents: number, basisPoints: number): number {
  return roundHalfUpCents((cents * basisPoints) / 10_000);
}
