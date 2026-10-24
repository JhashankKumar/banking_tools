import type { ReactNode } from "react";

import { cx } from "./cx";

export type Tone =
  | "neutral"
  | "primary"
  | "selected"
  | "review"
  | "error"
  | "success"
  | "counterparty"
  | "reversal";
const TONES: Record<Tone, string> = {
  neutral: "text-muted border-line",
  primary: "text-primary border-primary",
  selected: "text-selected border-selected",
  review: "text-review border-review",
  error: "text-error border-error",
  success: "text-success border-success",
  counterparty: "text-counterparty border-counterparty",
  reversal: "text-reversal border-reversal",
};
// Filled coloured chips sit on the surface colour: tone text on bg-raised falls just under AA 4.5:1.
const FILLED: Record<Tone, string> = {
  neutral: "text-muted border-transparent bg-raised",
  primary: "text-primary border-primary/30 bg-surface",
  selected: "text-selected border-selected/30 bg-surface",
  review: "text-review border-review/30 bg-surface",
  error: "text-error border-error/30 bg-surface",
  success: "text-success border-success/30 bg-surface",
  counterparty: "text-counterparty border-counterparty/30 bg-surface",
  reversal: "text-reversal border-reversal/30 bg-surface",
};

export function Chip({
  tone = "neutral",
  outline = false,
  mono = false,
  icon,
  children,
  className,
}: {
  tone?: Tone;
  outline?: boolean;
  mono?: boolean;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium whitespace-nowrap",
        "border",
        outline ? `bg-surface ${TONES[tone]}` : FILLED[tone],
        mono && "font-mono",
        className,
      )}
    >
      {icon}
      {children}
    </span>
  );
}
