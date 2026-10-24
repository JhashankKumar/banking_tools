import { Clock } from "lucide-react";

import { CardHeader } from "@/components/ui/Card";
import { Chip } from "@/components/ui/Chip";
import { cx } from "@/components/ui/cx";
import { Pagination } from "@/components/ui/Pagination";
import { StatusChip } from "@/features/transactions/components/StatusChip";
import type { Transaction } from "@/features/transactions/schemas";
import { formatMoney, formatTime } from "@/lib/format";
import type { PageMeta } from "@/lib/schemas";

export function TimelineCard({
  transactions,
  page,
  selectedId,
  onSelect,
  onOffset,
}: {
  transactions: Transaction[];
  page: PageMeta;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onOffset: (offset: number) => void;
}) {
  return (
    <section
      aria-label="Timeline"
      className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-4 shadow-sm"
    >
      <CardHeader
        icon={<Clock aria-hidden size={16} className="text-muted" />}
        title="Timeline (IST)"
      />
      <table className="w-full border-separate border-spacing-y-1 text-left text-xs">
        <thead>
          <tr className="text-[11px] text-muted">
            <th className="px-2.5 font-semibold">Tx</th>
            <th className="px-2.5 font-semibold">From → To</th>
            <th className="px-2.5 text-right font-semibold">Amount</th>
            <th className="px-2.5 font-semibold">Time</th>
            <th className="px-2.5 font-semibold">Status</th>
            <th className="px-2.5 font-semibold">Evidence</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((t) => {
            const selected = t.id === selectedId;
            return (
              <tr
                key={t.id}
                id={`tx-row-${t.id}`}
                aria-label={t.id}
                aria-selected={selected}
                tabIndex={0}
                onClick={() => onSelect(t.id)}
                onKeyDown={(e) =>
                  (e.key === "Enter" || e.key === " ") && onSelect(t.id)
                }
                className={cx(
                  "cursor-pointer",
                  selected
                    ? "bg-raised outline outline-1 outline-selected"
                    : "hover:bg-raised",
                )}
              >
                <td className="rounded-l-lg px-2.5 py-2 font-mono">{t.id}</td>
                <td className="px-2.5 py-2">
                  {t.source.id} → {t.destination.id}
                </td>
                <td className="px-2.5 py-2 text-right font-mono font-bold">
                  <span className="text-right">
                    {formatMoney(t.amount, t.currency)}
                  </span>
                </td>
                <td className="px-2.5 py-2 font-mono">
                  {formatTime(t.occurredAt)}
                </td>
                <td className="px-2.5 py-2">
                  <StatusChip status={t.status} />
                </td>
                <td className="rounded-r-lg px-2.5 py-2">
                  {t.evidenceId ? (
                    <Chip tone="selected" outline mono>
                      {t.evidenceId}
                    </Chip>
                  ) : (
                    <span className="text-muted">—</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {page.total > page.limit && (
        <Pagination page={page} noun="transactions" onOffset={onOffset} />
      )}
    </section>
  );
}
