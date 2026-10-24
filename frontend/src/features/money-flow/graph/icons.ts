import type { Theme } from "@/components/theme/use-theme";

const PATHS = {
  account:
    '<path d="M3 21h18"/><path d="M6 17v-6"/><path d="M10 17v-6"/><path d="M14 17v-6"/><path d="M18 17v-6"/><path d="M12 3 20 8H4z"/>',
  beneficiary:
    '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
};
const ON_NODE: Record<Theme, string> = { light: "#ffffff", dark: "#0b1220" };

/** Node icon as an SVG data URI (bank for accounts, person for beneficiaries). */
export function nodeIcon(
  type: "account" | "beneficiary",
  theme: Theme,
): string {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="${ON_NODE[theme]}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${PATHS[type]}</svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}
