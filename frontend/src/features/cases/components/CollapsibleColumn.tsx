import { ChevronLeft, ChevronRight } from "lucide-react";
import type { ReactNode } from "react";

/** A side column that collapses to a 44 px rail; both states are keyboard operable. */
export function CollapsibleColumn({
  side,
  label,
  railIcon,
  open,
  onToggle,
  width,
  className = "",
  children,
}: {
  side: "left" | "right";
  label: string;
  railIcon: ReactNode;
  open: boolean;
  onToggle: (open: boolean) => void;
  width: string;
  /** Extra classes for the open column, e.g. its own scrolling. */
  className?: string;
  children: ReactNode;
}) {
  if (!open) {
    return (
      <button
        type="button"
        aria-label={`Expand ${label}`}
        onClick={() => onToggle(true)}
        className="flex w-11 shrink-0 flex-col items-center gap-3 self-start rounded-xl border border-line bg-surface py-3.5 text-muted hover:text-ink"
      >
        {railIcon}
        {side === "left" ? (
          <ChevronRight size={14} />
        ) : (
          <ChevronLeft size={14} />
        )}
      </button>
    );
  }
  return (
    <div
      className={`flex min-h-0 shrink-0 flex-col gap-4 ${width} ${className}`}
    >
      <button
        type="button"
        aria-label={`Collapse ${label}`}
        onClick={() => onToggle(false)}
        className={`flex shrink-0 items-center gap-1 text-[11px] text-muted hover:text-ink ${side === "left" ? "self-end" : "self-start"}`}
      >
        {side === "left" ? (
          <ChevronLeft size={12} />
        ) : (
          <ChevronRight size={12} />
        )}{" "}
        Collapse
      </button>
      {children}
    </div>
  );
}
