"use client";

import { Flag } from "lucide-react";
import { useState } from "react";

import { CardHeader } from "@/components/ui/Card";
import { Chip } from "@/components/ui/Chip";
import type { Alert } from "@/features/alerts/schemas";
import type { Rule } from "@/features/rules/schemas";
import { formatElapsed, formatMoney } from "@/lib/format";

function metricTiles(alert: Alert): [string, string][] {
  const m = alert.metrics;
  const tiles: [string, string][] = [];
  if (m.elapsed_seconds)
    tiles.push(["Elapsed", formatElapsed(Number(m.elapsed_seconds))]);
  if (m.window_seconds)
    tiles.push(["Window", formatElapsed(Number(m.window_seconds))]);
  if (m.incoming_amount && m.currency)
    tiles.push(["In", formatMoney(m.incoming_amount, m.currency)]);
  if (m.outgoing_amount && m.currency)
    tiles.push(["Out", formatMoney(m.outgoing_amount, m.currency)]);
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
