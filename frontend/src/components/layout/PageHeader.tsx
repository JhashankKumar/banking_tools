import type { ReactNode } from "react";

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-ink">{title}</h1>
        <p className="text-sm text-muted">{subtitle}</p>
      </div>
      {action && <div className="ml-auto">{action}</div>}
    </div>
  );
}
