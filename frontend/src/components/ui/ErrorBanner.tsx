import { AlertCircle } from "lucide-react";

import type { ApiError } from "@/lib/api-error";

/** Inline failure of a user action (sign-in, save): the server message plus its request ID. */
export function ErrorBanner({
  error,
  note,
}: {
  error: ApiError | null;
  /** Appended after the request ID, e.g. "this attempt was recorded." */
  note?: string;
}) {
  if (!error) return null;
  return (
    <div
      role="alert"
      className="flex gap-2.5 rounded-lg border border-error bg-error/10 px-3 py-2.5"
    >
      <AlertCircle aria-hidden size={16} className="mt-0.5 text-error" />
      <div>
        <p className="text-sm font-semibold text-error">{error.message}</p>
        {error.requestId && (
          <p className="text-xs text-muted">
            Request ID {error.requestId}
            {note && ` · ${note}`}
          </p>
        )}
      </div>
    </div>
  );
}
