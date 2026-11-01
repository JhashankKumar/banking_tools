"use client";

import { Flag } from "lucide-react";
import { useState } from "react";

import { CardHeader } from "@/components/ui/Card";
import { Chip } from "@/components/ui/Chip";
import type { Alert } from "@/features/alerts/schemas";
import type { Rule } from "@/features/rules/schemas";
import { formatElapsed, formatMoney } from "@/lib/format";

/**
 * Durations from one hour up read as hours ("5 h", "1 h 5 m"); shorter ones as everywhere else.
 * Card-only: the copilot quotes `formatElapsed` wording and its answer checker relies on it.
 */
function formatDuration(seconds: number): string {
  if (seconds < 3600) return formatElapsed(seconds);
  const minutes = Math.floor(seconds / 60);
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m === 0 ? `${h} h` : `${h} h ${m} m`;
}

// The backend already rounds ratios down to 2 dp; round here only to undo float error (0.57 * 100).
const percent = (ratio: string) => `${Math.round(Number(ratio) * 100)} %`;

function metricTiles(alert: Alert): [string, string][] {
  const m = alert.metrics;
  const tiles: [string, string][] = [];
  if (m.elapsed_seconds)
    tiles.push(["Elapsed", formatDuration(Number(m.elapsed_seconds))]);
  if (m.window_seconds)
    tiles.push(["Window", formatDuration(Number(m.window_seconds))]);
  if (m.hops) tiles.push(["Hops", m.hops]);
  if (m.payer_count) tiles.push(["Payers", m.payer_count]);
  if (m.incoming_total && m.currency)
    tiles.push(["Collected", formatMoney(m.incoming_total, m.currency)]);
  if (m.start_amount && m.currency)
    tiles.push(["Sent", formatMoney(m.start_amount, m.currency)]);
  if (m.returned_amount && m.currency)
    tiles.push(["Returned", formatMoney(m.returned_amount, m.currency)]);
  if (m.outgoing_count) tiles.push(["Transfers", m.outgoing_count]);
  if (m.outgoing_total && m.currency)
    tiles.push(["Sent on", formatMoney(m.outgoing_total, m.currency)]);
  const share = m.onward_share ?? m.return_ratio;
  if (share) tiles.push(["Share", percent(share)]);
  // `currency` is the one the rule compared in; each amount keeps its own when they differ.
  const inCurrency = m.incoming_currency ?? m.currency;
  const outCurrency = m.outgoing_currency ?? m.currency;
  if (m.incoming_amount && inCurrency)
    tiles.push(["In", formatMoney(m.incoming_amount, inCurrency)]);
  if (m.outgoing_amount && outCurrency)
    tiles.push(["Out", formatMoney(m.outgoing_amount, outCurrency)]);
  if (m.converted_amount && m.currency && m.fx_rate) {
    const side =
      m.converted_transaction_id === m.incoming_transaction_id ? "In" : "Out";
    tiles.push([
      `${side} in ${m.currency}`,
      formatMoney(m.converted_amount, m.currency),
    ]);
    tiles.push(["Rate", `${m.fx_rate} (recorded)`]);
  }
  return tiles;
}

export function WhyItFiredCard({
  alert,
  rule,
}: {
  alert: Alert;
  rule: Rule | undefined;
}) {
  const [showCaveats, setShowCaveats] = useState(false);
  return (
    <section
      aria-label="Why it fired"
      className="flex flex-col gap-3 rounded-xl border border-review bg-surface p-4 shadow-sm"
    >
      <CardHeader
        icon={<Flag aria-hidden size={16} className="text-review" />}
        title="Why it fired"
      />
      <div className="flex flex-wrap gap-1.5">
        <Chip tone="review" mono>
          {alert.id}
        </Chip>
        <Chip mono>{`${alert.rule.id} v${alert.rule.version}`}</Chip>
      </div>
      <p className="text-[13px] text-ink">
        {alert.explanation.replace(
          / Signal for analyst review; not a finding of fraud\.$/,
          "",
        )}
      </p>
      <div className="grid grid-cols-2 gap-2">
        {metricTiles(alert).map(([label, value]) => (
          <div key={label} className="rounded-lg bg-raised px-2.5 py-2">
            <p className="text-[11px] text-muted">{label}</p>
            <p className="font-mono text-[13px] font-bold text-ink">{value}</p>
          </div>
        ))}
      </div>
      <p className="rounded-lg bg-review-soft px-2.5 py-1.5 text-xs font-medium text-review">
        Signal for analyst review — not a finding of fraud.
      </p>
      <button
        type="button"
        aria-expanded={showCaveats}
        onClick={() => setShowCaveats((s) => !s)}
        className="self-start text-xs font-medium text-primary"
      >
        Rule caveats {showCaveats ? "▾" : "▸"}
      </button>
      {showCaveats && (
        <ul className="list-disc pl-4 text-xs text-muted">
          {(rule?.falsePositiveCaveats ?? ["Caveats are unavailable."]).map(
            (c) => (
              <li key={c}>{c}</li>
            ),
          )}
        </ul>
      )}
    </section>
  );
}
