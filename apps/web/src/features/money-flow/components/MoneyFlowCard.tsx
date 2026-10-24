"use client";

import dynamic from "next/dynamic";
import { useMemo, useRef, useState } from "react";

import { useTheme } from "@/components/theme/use-theme";
import { Segmented } from "@/components/ui/Segmented";
import { StatePanel } from "@/components/ui/StatePanel";
import { QueryError } from "@/components/layout/QueryState";
import { useCaseSelection } from "@/features/cases/case-selection";
import type { CasePageData } from "@/features/cases/hooks/useCasePage";

import type { FlowEdge } from "../schemas";
import { toGraphData } from "../to-graph-data";
import { EdgeDetailCard } from "./EdgeDetailCard";
import { GraphAccessibleList } from "./GraphAccessibleList";
import { GraphControls } from "./GraphControls";
import { GraphLegend } from "./GraphLegend";
import { PathChips } from "./PathChips";

const ReagraphView = dynamic(() => import("./ReagraphView"), {
  ssr: false,
  loading: () => <StatePanel kind="loading" title="Loading graph" />,
});

const WINDOWS = [1, 6, 12, 24, 48, 72, 168];
const HOPS = [1, 2, 3, 4, 5];
const select =
  "rounded-full border border-line bg-surface px-2.5 py-1 text-xs text-ink";

export function MoneyFlowCard({ data }: { data: CasePageData }) {
  const selection = useCaseSelection();
  const { theme } = useTheme();
  const [mode, setMode] = useState<"look" | "view">("look");
  const [caseOnly, setCaseOnly] = useState(false);
  const [pathOnly, setPathOnly] = useState(false);
  const [layoutKey, setLayoutKey] = useState(0);
  const beforeView = useRef({ left: true, right: true });

  const graph = data.graphQuery.data;
  const pathsData = data.moneyPathsQuery.data;
  const paths = useMemo(() => pathsData?.paths ?? [], [pathsData]);
  const path =
    selection.selectedPathIndex === null
      ? null
      : (paths[selection.selectedPathIndex] ?? null);

  const graphData = useMemo(
    () =>
      graph
        ? toGraphData(graph, path, {
            nodes: caseOnly ? "case" : "all",
            edges: pathOnly && path ? "path" : "all",
            theme,
          })
        : null,
    [graph, path, caseOnly, pathOnly, theme],
  );
  const edgesById = useMemo(() => {
    const map = new Map<string, { edge: FlowEdge; inCase: boolean }>();
    for (const e of graph?.edges ?? [])
      map.set(e.transactionId, { edge: e, inCase: e.inCase });
    for (const p of paths)
      for (const e of p.edges)
        if (!map.has(e.transactionId))
          map.set(e.transactionId, { edge: e, inCase: false });
    return map;
  }, [graph, paths]);
  const selected = selection.selectedTransactionId
    ? edgesById.get(selection.selectedTransactionId)
    : undefined;

  const changeMode = (next: "look" | "view") => {
    if (next === mode) return;
    if (next === "view") {
      beforeView.current = {
        left: selection.leftOpen,
        right: selection.rightOpen,
      };
      selection.setLeftOpen(false);
      selection.setRightOpen(false);
    } else {
      selection.setLeftOpen(beforeView.current.left);
      selection.setRightOpen(beforeView.current.right);
    }
    setMode(next);
  };

  return (
    <section
      aria-label="Money-flow network"
      className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-4 shadow-sm"
    >
      <header className="flex flex-wrap items-center gap-2.5">
        <h2 className="text-sm font-semibold text-ink">Money-flow network</h2>
        <div className="ml-auto flex items-center gap-2">
          <Segmented
            label="Graph view"
            value={mode}
            onChange={changeMode}
            options={[
              { value: "look", label: "3D look" },
              { value: "view", label: "3D view" },
            ]}
          />
          <label className="sr-only" htmlFor="graph-window">
            Time window
          </label>
          <select
            id="graph-window"
            className={select}
            value={data.windowHours}
            onChange={(e) => data.setWindowHours(Number(e.target.value))}
          >
            {WINDOWS.map((w) => (
              <option key={w} value={w}>
                Window {w} h
              </option>
            ))}
          </select>
          <label className="sr-only" htmlFor="graph-hops">
            Max hops
          </label>
          <select
            id="graph-hops"
            className={select}
            value={data.maxHops}
            onChange={(e) => data.setMaxHops(Number(e.target.value))}
          >
            {HOPS.map((h) => (
              <option key={h} value={h}>
                Hops {h}
              </option>
            ))}
          </select>
        </div>
      </header>
      <PathChips
        paths={paths}
        selected={selection.selectedPathIndex}
        onSelect={selection.selectPath}
      />
      <GraphControls
        caseOnly={caseOnly}
        pathOnly={pathOnly && path !== null}
        pathAvailable={path !== null}
        onCaseOnly={setCaseOnly}
        onPathOnly={setPathOnly}
        onRelayout={() => setLayoutKey((k) => k + 1)}
      />
      {(graph?.truncated || data.moneyPathsQuery.data?.truncated) && (
        <p className="text-xs text-review">
          Some transactions or paths are not shown because a limit was reached.
        </p>
      )}
      <div
        className={`relative overflow-hidden rounded-xl bg-raised ${mode === "view" ? "h-[640px]" : "h-[500px]"}`}
      >
        {data.graphQuery.isPending ? (
          <StatePanel kind="loading" title="Loading graph" />
        ) : data.graphQuery.isError ? (
          <QueryError error={data.graphQuery.error} noun="Graph" />
        ) : graphData && graphData.nodes.length === 0 ? (
          <StatePanel kind="empty" title="No transactions in this window" />
        ) : (
          graphData && (
            <>
              <ReagraphView
                key={layoutKey}
                data={graphData}
                mode={mode}
                theme={theme}
                selectedEdgeId={selection.selectedTransactionId}
                onEdgeClick={selection.selectTransaction}
              />
              {selected && (
                <EdgeDetailCard
                  edge={selected.edge}
                  inCase={selected.inCase}
                  onClose={() => selection.selectTransaction(null)}
                  onShowInTimeline={() =>
                    document
                      .getElementById(`tx-row-${selected.edge.transactionId}`)
                      ?.scrollIntoView({ block: "center" })
                  }
                  onAskCopilot={() => selection.setRightOpen(true)}
                />
              )}
              {mode === "look" && (
                <p className="absolute bottom-3 left-3 text-[11px] text-muted">
                  3D look · exact values in the timeline
                </p>
              )}
            </>
          )
        )}
      </div>
      {mode === "view" && (
        <p className="text-[11px] text-muted">
          3D is for exploring. Exact amounts, times and evidence stay in the
          timeline and edge details.
        </p>
      )}
      <GraphLegend />
      <GraphAccessibleList
        edges={[...edgesById.values()].map((v) => v.edge)}
        onSelect={selection.selectTransaction}
      />
    </section>
  );
}
