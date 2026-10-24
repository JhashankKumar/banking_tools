import type { HTMLAttributes, ReactNode } from "react";

import { cx } from "./cx";

export function Card({ className, ...props }: HTMLAttributes<HTMLElement>) {
  return (
    <section
      className={cx(
        "rounded-xl border border-line bg-surface p-4 shadow-sm dark:shadow-black/40",
        className,
      )}
      {...props}
    />
  );
}

export function CardHeader({
  icon,
  title,
  children,
}: {
  icon?: ReactNode;
  title: string;
  children?: ReactNode;
}) {
  return (
    <header className="mb-3 flex items-center gap-2">
      {icon}
      <h2 className="text-sm font-semibold text-ink">{title}</h2>
      {children && (
        <div className="ml-auto flex items-center gap-2">{children}</div>
      )}
    </header>
  );
}
