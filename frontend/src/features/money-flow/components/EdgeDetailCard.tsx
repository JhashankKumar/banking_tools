import { Sparkles, X } from "lucide-react";

import { Chip } from "@/components/ui/Chip";
import { TransactionStatusChip } from "@/features/transactions/components/TransactionStatusChip";
import { formatDateTime, formatMoney } from "@/lib/format";

import type { FlowEdge } from "../schemas";

export function EdgeDetailCard({
  edge,
  inCase,
  onClose,
  onShowInTimeline,
  onAskCopilot,
}: {
  edge: FlowEdge;
  inCase: boolean;
  onClose: () => void;
  onShowInTimeline: () => void;
  onAskCopilot: () => void;
}) {
  const rows: [string, string][] = [
    ["From → To", `${edge.source.id} → ${edge.destination.id}`],
    ["Amount", formatMoney(edge.amount, edge.currency)],
    ["Time", formatDateTime(edge.occurredAt)],
    ["Rail", [edge.rail, edge.reference].filter(Boolean).join(" · ") || "—"],
  ];
  return (
    <section
      aria-label={`Transaction ${edge.transactionId}`}
      className="absolute top-14 right-3 z-10 flex w-72 flex-col gap-2 rounded-xl border-[1.5px] border-selected bg-surface p-3.5 shadow-xl"
    >
      <header className="flex items-center gap-2">
        <span className="font-mono text-sm font-bold text-ink">
          {edge.transactionId}
        </span>
        <TransactionStatusChip status={edge.status} />
        {edge.kind === "reversal" && <Chip tone="reversal">reversal</Chip>}
        <button
          type="button"
          aria-label="Close transaction details"
          onClick={onClose}
          className="ml-auto text-muted hover:text-ink"
        >
          <X size={14} />
        </button>
      </header>
      <dl className="flex flex-col gap-1">
        {rows.map(([k, v]) => (
          <div key={k} className="flex gap-2 text-xs">
            <dt className="text-muted">{k}</dt>
            <dd className="ml-auto text-right font-mono font-medium text-ink">
              {v}
            </dd>
          </div>
        ))}
      </dl>
      {edge.evidenceId ? (
        <Chip tone="selected" outline mono className="self-start">
          {edge.evidenceId}
        </Chip>
      ) : (
        <span className="text-xs text-muted">Evidence: —</span>
      )}
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={!inCase}
          onClick={onShowInTimeline}
          className="rounded-full border border-primary px-2.5 py-0.5 text-[11px] font-medium text-primary disabled:border-line disabled:text-muted"
        >
          Show in timeline ▸
        </button>
        <button
          type="button"
          onClick={onAskCopilot}
          className="inline-flex items-center gap-1 rounded-full border border-primary px-2.5 py-0.5 text-[11px] font-medium text-primary"
        >
          <Sparkles aria-hidden size={11} /> Ask copilot
        </button>
      </div>
      {!inCase && (
        <p className="text-[11px] text-muted">
          Not one of this case&apos;s transactions.
        </p>
      )}
    </section>
  );
}
