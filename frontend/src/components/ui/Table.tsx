"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  createContext,
  useContext,
  type HTMLAttributes,
  type ReactNode,
  type TdHTMLAttributes,
  type ThHTMLAttributes,
} from "react";

import { cx } from "./cx";

export function Table({
  className,
  empty,
  ...props
}: HTMLAttributes<HTMLTableElement> & {
  /** When set, shown instead of the table (e.g. "No alerts match these filters."). */
  empty?: string | false;
}) {
  if (empty) {
    return (
      <p className="rounded-xl border border-line bg-surface p-8 text-center text-sm text-muted">
        {empty}
      </p>
    );
  }
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

const RowHref = createContext<string | null>(null);

/**
 * A row that opens `href` when clicked anywhere. Put `<LinkRow.Link>` in one cell so keyboard
 * and screen-reader users get a real link; clicking that link does not navigate twice.
 */
export function LinkRow({
  href,
  label,
  children,
}: {
  href: string;
  label: string;
  children: ReactNode;
}) {
  const router = useRouter();
  return (
    <RowHref.Provider value={href}>
      <tr
        aria-label={label}
        onClick={() => router.push(href)}
        className="cursor-pointer hover:bg-raised"
      >
        {children}
      </tr>
    </RowHref.Provider>
  );
}

LinkRow.Link = function RowLink({ children }: { children: ReactNode }) {
  const href = useContext(RowHref);
  if (!href) throw new Error("LinkRow.Link must be inside a LinkRow");
  return (
    <Link
      href={href}
      onClick={(e) => e.stopPropagation()}
      className="hover:underline"
    >
      {children}
    </Link>
  );
};
