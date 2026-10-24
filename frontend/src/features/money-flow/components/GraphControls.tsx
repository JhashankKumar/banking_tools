import { RefreshCw } from "lucide-react";

import { Toggle } from "@/components/ui/Toggle";

export function GraphControls({
  caseOnly,
  pathOnly,
  pathAvailable,
  onCaseOnly,
  onPathOnly,
  onRelayout,
}: {
  caseOnly: boolean;
  pathOnly: boolean;
  pathAvailable: boolean;
  onCaseOnly: (v: boolean) => void;
  onPathOnly: (v: boolean) => void;
  onRelayout: () => void;
}) {
  return (
    <div
      role="group"
      aria-label="Graph view options"
      className="flex flex-wrap items-center gap-x-5 gap-y-2 rounded-lg border border-line bg-surface px-3 py-2"
    >
      <p className="text-xs font-semibold text-ink">View</p>
      <div className="flex items-center gap-2 text-[11px]">
        <span className={caseOnly ? "text-muted" : "text-ink"}>All nodes</span>
        <Toggle
          label="Case parties only"
          checked={caseOnly}
          onChange={onCaseOnly}
        />
        <span className={caseOnly ? "text-ink" : "text-muted"}>
          Case parties
        </span>
      </div>
      <div className="flex items-center gap-2 text-[11px]">
        <span className={pathOnly ? "text-muted" : "text-ink"}>All edges</span>
        <Toggle
          label="Money path only"
          checked={pathOnly}
          onChange={onPathOnly}
          disabled={!pathAvailable}
        />
        <span className={pathOnly ? "text-ink" : "text-muted"}>Money path</span>
      </div>
      <button
        type="button"
        onClick={onRelayout}
        className="ml-auto flex items-center justify-center gap-1.5 rounded-lg border border-line px-2.5 py-1 text-xs font-medium text-ink hover:bg-raised"
      >
        <RefreshCw aria-hidden size={12} /> Re-layout
      </button>
    </div>
  );
}
