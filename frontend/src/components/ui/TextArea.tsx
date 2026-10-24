import { forwardRef, type TextareaHTMLAttributes } from "react";

import { cx } from "./cx";

/** Labelled multi-line input with hint and error text wired to aria attributes (like Field). */
export const TextArea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement> & {
    label: string;
    hint?: string;
    error?: string;
    mono?: boolean;
  }
>(function TextArea(
  { label, hint, error, mono, id, className, ...props },
  ref,
) {
  const inputId = id ?? props.name;
  const describedBy = error
    ? `${inputId}-error`
    : hint
      ? `${inputId}-hint`
      : undefined;
  return (
    <div className={cx("flex flex-col gap-1.5", className)}>
      <label htmlFor={inputId} className="text-xs font-semibold text-ink">
        {label}
      </label>
      <textarea
        ref={ref}
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={cx(
          "min-h-24 rounded-lg border bg-surface px-3 py-2.5 text-sm text-ink outline-none placeholder:text-muted focus:ring-2 focus:ring-primary/30",
          error ? "border-error" : "border-line focus:border-primary",
          mono && "font-mono text-xs",
        )}
        {...props}
      />
      {error ? (
        <p id={`${inputId}-error`} className="text-xs text-error">
          {error}
        </p>
      ) : (
        hint && (
          <p id={`${inputId}-hint`} className="text-xs text-muted">
            {hint}
          </p>
        )
      )}
    </div>
  );
});
