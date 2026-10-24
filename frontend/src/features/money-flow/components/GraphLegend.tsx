import { Flag } from "lucide-react";

const line = (cls: string) => (
  <span aria-hidden className={`inline-block w-5 border-t-2 ${cls}`} />
);

export function GraphLegend() {
  return (
    <ul
      aria-label="Legend"
      className="flex flex-wrap items-center gap-3.5 text-[10px] text-muted"
    >
      <li className="flex items-center gap-1.5">
        {line("border-selected")} selected path
      </li>
      <li className="flex items-center gap-1.5">
        {line("border-counterparty")} completed
      </li>
      <li className="flex items-center gap-1.5">
        {line("border-dashed border-counterparty")} pending / failed
      </li>
      <li className="flex items-center gap-1.5">
        {line("border-reversal")} reversal
      </li>
      <li className="flex items-center gap-1">
        <Flag aria-hidden size={12} className="text-review" /> needs review
      </li>
    </ul>
  );
}
