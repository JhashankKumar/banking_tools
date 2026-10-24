import { AlertTriangle, FileQuestion, Inbox, Lock } from "lucide-react";
import type { ReactNode } from "react";

import { Skeleton } from "./Skeleton";

type Kind = "loading" | "empty" | "error" | "forbidden" | "not-found";
const ICONS = {
  empty: Inbox,
  error: AlertTriangle,
  forbidden: Lock,
  "not-found": FileQuestion,
};

/** One component for every non-success state, so each data view handles all of them alike. */
export function StatePanel({
  kind,
  title,
  message,
  requestId,
  action,
}: {
  kind: Kind;
  title: string;
  message?: string;
  requestId?: string | null;
  action?: ReactNode;
}) {
  if (kind === "loading") {
    return (
      <div role="status" className="flex flex-col gap-2 p-4">
        <span className="sr-only">{title}</span>
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-4 w-1/2" />
      </div>
    );
  }
  const Icon = ICONS[kind];
  return (
    <div className="flex flex-col items-center gap-2 px-6 py-10 text-center">
      <Icon
        aria-hidden
        className={kind === "error" ? "text-error" : "text-muted"}
        size={28}
      />
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      {message && <p className="max-w-md text-sm text-muted">{message}</p>}
      {requestId && (
        <p className="font-mono text-xs text-muted">Request ID {requestId}</p>
      )}
      {action}
    </div>
  );
}
