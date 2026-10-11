export function roundHalfUpCents(value: number): number {
  return Math.floor(value + 0.5);
}

export function formatCents(cents: number): string {
  return `$${(roundHalfUpCents(cents) / 100).toFixed(2)}`;
}
