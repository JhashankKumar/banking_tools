import { Search } from "lucide-react";
import type { ReactNode } from "react";

const selectClass =
  "rounded-full border border-line bg-surface px-3 py-1 text-xs text-ink";

/** Row of list filters above a table. */
export function FilterBar({ children }: { children: ReactNode }) {
  return <div className="flex items-center gap-2.5">{children}</div>;
}

/** Client-side text search box with a visible icon and an accessible label. */
export function SearchInput({
  label,
  placeholder,
  value,
  onChange,
  mono = false,
}: {
  label: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  mono?: boolean;
}) {
  return (
    <label className="flex w-80 items-center gap-2 rounded-lg border border-line bg-surface px-3 py-2">
      <Search aria-hidden size={14} className="text-muted" />
      <span className="sr-only">{label}</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`w-full bg-transparent text-xs text-ink outline-none placeholder:font-sans placeholder:text-muted ${mono ? "font-mono" : ""}`}
      />
    </label>
  );
}

/** Pill-shaped select whose first option, "<label>: all", means no filter (undefined). */
export function FilterSelect<V extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: V | undefined;
  options: { value: V; label?: string }[];
  onChange: (value: V | undefined) => void;
}) {
  return (
    <select
      aria-label={label}
      className={selectClass}
      value={value ?? ""}
      onChange={(e) => onChange((e.target.value || undefined) as V | undefined)}
    >
      <option value="">{label}: all</option>
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label ?? o.value}
        </option>
      ))}
    </select>
  );
}
