export function remainingAmount(total: number, paid: number) {
  return Math.max(total - paid, 0);
}

export function paymentStatus(total: number, paid: number) {
  if (paid <= 0) return 'TO‘LANMAGAN';
  if (paid >= total) return 'TO‘LIQ TO‘LANGAN';
  return 'QISMAN TO‘LANGAN';
}

export function maskPinfl(pinfl: string) {
  if (pinfl.length < 4) return '****';
  return `${'*'.repeat(Math.max(pinfl.length - 4, 0))}${pinfl.slice(-4)}`;
}
