import type { HTMLAttributes, TdHTMLAttributes, ThHTMLAttributes } from "react";

import { cx } from "./cx";

export function Table({
  className,
  ...props
}: HTMLAttributes<HTMLTableElement>) {
  return (
    <div className="overflow-x-auto rounded-xl border border-line bg-surface shadow-sm">
      <table
        className={cx("w-full border-collapse text-left text-xs", className)}
        {...props}
      />
    </div>
  );
}

export function Th({
  className,
  ...props
}: ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={cx(
        "bg-raised px-4 py-2.5 text-[11px] font-semibold text-muted",
        className,
      )}
      {...props}
    />
  );
}

export function Td({
  className,
  ...props
}: TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td
      className={cx("border-t border-line px-4 py-3 text-ink", className)}
      {...props}
    />
  );
}
