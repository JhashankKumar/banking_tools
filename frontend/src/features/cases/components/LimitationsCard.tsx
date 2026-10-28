import { Info } from "lucide-react";

import { CardHeader } from "@/components/ui/Card";

export function LimitationsCard({ items }: { items: string[] }) {
  return (
    <section
      aria-label="Limitations"
      className="rounded-xl border border-line bg-surface p-4 shadow-sm"
    >
      <CardHeader
        icon={<Info aria-hidden size={16} className="text-muted" />}
        title="Limitations"
      />
      <ul className="flex list-disc flex-col gap-1 pl-4 text-xs text-muted">
        {items.map((l) => (
          <li key={l}>{l}</li>
        ))}
      </ul>
    </section>
  );
}
