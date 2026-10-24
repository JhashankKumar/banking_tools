import { forwardRef, type SelectHTMLAttributes } from "react";

import { CLOSING_REASONS } from "../schemas";

/** Required closing reason from the fixed list (no "all" option, unlike FilterSelect). */
export const ReasonSelect = forwardRef<
  HTMLSelectElement,
  SelectHTMLAttributes<HTMLSelectElement> & { error?: string }
>(function ReasonSelect({ error, ...props }, ref) {
  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor="closing-reason"
        className="text-xs font-semibold text-ink"
      >
        Closing reason
      </label>
      <select
        ref={ref}
        id="closing-reason"
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? "closing-reason-error" : undefined}
        className={`rounded-lg border bg-surface px-3 py-2.5 text-sm text-ink ${error ? "border-error" : "border-line"}`}
        {...props}
      >
        <option value="">Choose a reason…</option>
        {CLOSING_REASONS.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>
      {error && (
        <p id="closing-reason-error" className="text-xs text-error">
          {error}
        </p>
      )}
    </div>
  );
});
