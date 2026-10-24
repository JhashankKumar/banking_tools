import { Check } from "lucide-react";

import { CardHeader } from "@/components/ui/Card";
import { Chip } from "@/components/ui/Chip";

export interface EvidenceItem {
  id: string;
  label: "observed fact" | "indicator";
  transactionId?: string;
}

export function EvidenceCard({
  items,
  onSelect,
}: {
  items: EvidenceItem[];
  onSelect: (transactionId: string) => void;
}) {
  return (
    <section
      aria-label="Evidence"
      className="rounded-xl border border-line bg-surface p-4 shadow-sm"
    >
      <CardHeader
        icon={<Check aria-hidden size={16} className="text-selected" />}
        title="Evidence"
      />
      {items.length === 0 ? (
        <p className="text-xs text-muted">
          No evidence recorded for this case.
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {items.map((e) => (
            <li key={e.id} className="flex items-center gap-2">
              {e.transactionId ? (
                <button
                  type="button"
                  onClick={() => onSelect(e.transactionId as string)}
                  aria-label={`${e.id}, show transaction`}
                >
                  <Chip tone="selected" outline mono>
                    {e.id}
                  </Chip>
                </button>
              ) : (
                <Chip tone="selected" outline mono>
                  {e.id}
                </Chip>
              )}
              <span className="text-[11px] text-muted">{e.label}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
