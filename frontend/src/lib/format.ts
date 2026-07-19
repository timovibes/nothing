/*formats minor-unit integers (e.g. 2439875) into proper currency display (e.g. KES 24,398.75) —
used everywhere money appears in the UI. */

export function formatMoney(amountMinor: number, currency: string): string {
  const major = amountMinor / 100;
  const formatted = major.toLocaleString("en-KE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${currency} ${formatted}`;
}

export function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString("en-KE", {
    month: "short",
    day: "numeric",
  });
}

export function shortId(id: string): string {
  return id.slice(0, 8) + "…";
}