"use client";

import { cx } from "./cx";

export function Toggle({
  label,
  checked,
  onChange,
  disabled,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cx(
        "inline-flex h-5 w-9 items-center rounded-full px-0.5 transition disabled:opacity-50",
        checked ? "justify-end bg-selected" : "justify-start bg-line",
      )}
    >
      <span className="h-4 w-4 rounded-full bg-surface shadow" />
    </button>
  );
}
