import { cx } from "@/components/ui/cx";
import { formatElapsed } from "@/lib/format";

import type { MoneyPath } from "../schemas";

const chip = "rounded-full border px-2.5 py-0.5 text-[11px] font-medium";

export function PathChips({
  paths,
  selected,
  onSelect,
}: {
  paths: MoneyPath[];
  selected: number | null;
  onSelect: (index: number | null) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs text-muted">Money paths</span>
      {paths.length === 0 && (
        <span className="text-xs text-muted">none found in this window</span>
      )}
      {paths.map((p, i) => (
        <button
          key={p.edges.map((e) => e.transactionId).join("-")}
          type="button"
          aria-pressed={selected === i}
          onClick={() => onSelect(i)}
          className={cx(
            chip,
            "font-mono",
            selected === i
              ? "border-selected text-selected"
              : "border-line text-muted",
          )}
        >
          {`${selected === i ? "● " : ""}Path ${i + 1} · ${p.hops} hops · ${formatElapsed(p.elapsedSeconds)}`}
        </button>
      ))}
      <button
        type="button"
        aria-pressed={selected === null}
        onClick={() => onSelect(null)}
        className={cx(
          chip,
          selected === null
            ? "border-primary text-primary"
            : "border-line text-muted",
        )}
      >
        All transactions
      </button>
    </div>
  );
}
