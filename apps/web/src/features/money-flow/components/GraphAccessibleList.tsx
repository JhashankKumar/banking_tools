import { formatDateTime, formatMoney } from "@/lib/format";

import type { FlowEdge } from "../schemas";

/** Keyboard and screen-reader equivalent of the WebGL canvas. Visible while focused. */
export function GraphAccessibleList({
  edges,
  onSelect,
}: {
  edges: FlowEdge[];
  onSelect: (id: string) => void;
}) {
  return (
    <ul
      aria-label="Graph transactions"
      className="sr-only focus-within:not-sr-only focus-within:flex focus-within:flex-col focus-within:gap-1 focus-within:rounded-lg focus-within:border focus-within:border-line focus-within:p-2"
    >
      {edges.map((e) => (
        <li key={e.transactionId}>
          <button
            type="button"
            onClick={() => onSelect(e.transactionId)}
            className="text-left text-xs text-ink"
          >
            {`${e.transactionId}: ${e.source.id} to ${e.destination.id}, ${formatMoney(e.amount, e.currency)}, ${formatDateTime(e.occurredAt)}, ${e.status}`}
          </button>
        </li>
      ))}
    </ul>
  );
}
