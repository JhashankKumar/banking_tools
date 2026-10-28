import type { LucideIcon } from "lucide-react";

import { Chip, type Tone } from "./Chip";

export interface StatusStyle {
  tone: Tone;
  icon: LucideIcon;
  /** Shown text; defaults to the raw value. */
  label?: string;
}
export type StatusStyles<V extends string> = Record<V, StatusStyle>;

/** A status shown with an icon and text, never colour alone. Each domain supplies its map. */
export function StatusChip<V extends string>({
  value,
  styles,
  outline = false,
}: {
  value: V;
  styles: StatusStyles<V>;
  outline?: boolean;
}) {
  const { tone, icon: Icon, label } = styles[value];
  return (
    <Chip tone={tone} outline={outline} icon={<Icon aria-hidden size={12} />}>
      {label ?? value}
    </Chip>
  );
}
