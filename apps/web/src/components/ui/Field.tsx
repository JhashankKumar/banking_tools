import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";

import { cx } from "./cx";

/** Labelled input with hint and error text wired to aria attributes. */
export const Field = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement> & {
    label: string;
    hint?: string;
    error?: string;
    icon?: ReactNode;
    trailing?: ReactNode;
    mono?: boolean;
  }
>(function Field(
  { label, hint, error, icon, trailing, mono, id, className, ...props },
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
      <div
        className={cx(
          "flex items-center gap-2.5 rounded-lg border bg-surface px-3 py-2.5 focus-within:ring-2 focus-within:ring-primary/30",
          error ? "border-error" : "border-line focus-within:border-primary",
        )}
      >
        {icon}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={cx(
            "w-full bg-transparent text-sm text-ink outline-none placeholder:text-muted",
            mono && "font-mono",
          )}
          {...props}
        />
        {trailing}
      </div>
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
