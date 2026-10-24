"use client";

import { cx } from "./cx";

/** Single-choice control rendered as a radio group (keyboard and screen-reader friendly). */
export function Segmented<T extends string>({
  label,
  options,
  value,
  onChange,
  size = "sm",
  disabled = false,
}: {
  label: string;
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
  size?: "sm" | "md";
  disabled?: boolean;
}) {
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className="inline-flex overflow-hidden rounded-lg border border-line"
    >
      {options.map((o) => {
        const on = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={on}
            disabled={disabled}
            onClick={() => onChange(o.value)}
            className={cx(
              "font-semibold transition disabled:cursor-not-allowed disabled:opacity-60",
              size === "sm"
                ? "px-2.5 py-1 text-xs"
                : "flex-1 px-3 py-2 text-xs",
              on ? "bg-primary text-on-primary" : "text-muted hover:bg-raised",
            )}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
