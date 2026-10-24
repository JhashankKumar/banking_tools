import type { Theme as ReagraphTheme } from "reagraph";

import type { Theme } from "@/components/theme/use-theme";

/**
 * The WebGL canvas needs concrete colours, so the theme tokens are mirrored here.
 * A test asserts these match src/app/globals.css.
 */
export const PALETTE = {
  light: {
    "bg-surface": "#ffffff",
    "bg-surface-raised": "#eef2f7",
    border: "#d9e0ea",
    text: "#0f1b2d",
    "text-muted": "#52607a",
    primary: "#1d4ed8",
    selected: "#0f766e",
    review: "#b45309",
    reversal: "#6d28d9",
    counterparty: "#5f6b7e",
  },
  dark: {
    "bg-surface": "#111a2e",
    "bg-surface-raised": "#17223a",
    border: "#26344f",
    text: "#e6ecf5",
    "text-muted": "#93a1b8",
    primary: "#60a5fa",
    selected: "#2dd4bf",
    review: "#fbbf24",
    reversal: "#a78bfa",
    counterparty: "#94a3b8",
  },
} as const satisfies Record<Theme, Record<string, string>>;
export type Palette = (typeof PALETTE)[Theme];

export function reagraphTheme(theme: Theme): ReagraphTheme {
  const p = PALETTE[theme];
  return {
    canvas: { background: p["bg-surface-raised"], fog: p["bg-surface-raised"] },
    node: {
      fill: p.primary,
      activeFill: p.selected,
      opacity: 1,
      selectedOpacity: 1,
      inactiveOpacity: 0.35,
      label: {
        color: p.text,
        stroke: p["bg-surface-raised"],
        activeColor: p.selected,
      },
      subLabel: {
        color: p["text-muted"],
        stroke: p["bg-surface-raised"],
        activeColor: p["text-muted"],
      },
    },
    ring: { fill: p.primary, activeFill: p.selected },
    edge: {
      fill: p.counterparty,
      activeFill: p.selected,
      opacity: 0.9,
      selectedOpacity: 1,
      inactiveOpacity: 0.2,
      label: {
        color: p["text-muted"],
        stroke: p["bg-surface-raised"],
        activeColor: p.selected,
        fontSize: 6,
      },
    },
    arrow: { fill: p.counterparty, activeFill: p.selected },
    lasso: {
      border: `1px solid ${p.primary}`,
      background: "rgba(29, 78, 216, 0.1)",
    },
    cluster: {
      stroke: p.border,
      opacity: 1,
      selectedOpacity: 1,
      inactiveOpacity: 0.1,
      label: { stroke: p["bg-surface-raised"], color: p.text },
    },
  };
}
