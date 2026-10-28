/** The only formatters for money and time (API_AND_CODE_CONVENTIONS §3.3). */

const IST = "Asia/Kolkata";

export function formatMoney(amount: string, currency: string): string {
  // Intl formats decimal strings exactly; money is never converted to a float.
  const format = new Intl.NumberFormat("en-IN", { style: "currency", currency })
    .format as (value: string) => string;
  return format(amount);
}

function parts(iso: string): Record<string, string> {
  // en-US for the 3-letter month ("Sep"; en-GB now gives "Sept"); the order is assembled below.
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone: IST,
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  });
  return Object.fromEntries(
    formatter.formatToParts(new Date(iso)).map((p) => [p.type, p.value]),
  );
}

/** "15 Sep 2026, 10:02:14 IST" */
export function formatDateTime(iso: string): string {
  const p = parts(iso);
  return `${p.day} ${p.month} ${p.year}, ${p.hour}:${p.minute}:${p.second} IST`;
}

/** "10:02:14" (IST) */
export function formatTime(iso: string): string {
  const p = parts(iso);
  return `${p.hour}:${p.minute}:${p.second}`;
}

/** "5 m 28 s" */
export function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m === 0) return `${s} s`;
  return s === 0 ? `${m} m` : `${m} m ${s} s`;
}
