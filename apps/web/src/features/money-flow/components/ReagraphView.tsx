"use client";

import { Minus, Plus, RotateCcw, Scan } from "lucide-react";
import { useEffect, useRef } from "react";
import {
  Badge,
  GraphCanvas,
  SphereWithIcon,
  type GraphCanvasRef,
  type NodeRendererProps,
} from "reagraph";

import type { Theme } from "@/components/theme/use-theme";

import { PALETTE, reagraphTheme } from "../graph-theme";
import type { GraphData } from "../to-graph-data";

export interface ReagraphViewProps {
  data: GraphData;
  mode: "look" | "view";
  theme: Theme;
  selectedEdgeId: string | null;
  onEdgeClick: (id: string) => void;
}

const control =
  "flex h-8 w-8 items-center justify-center rounded-lg border border-line bg-surface text-muted hover:text-ink";

/** The WebGL graph. Loaded client-only (next/dynamic, ssr: false) by MoneyFlowCard. */
export default function ReagraphView({
  data,
  mode,
  theme,
  selectedEdgeId,
  onEdgeClick,
}: ReagraphViewProps) {
  const ref = useRef<GraphCanvasRef | null>(null);
  const view = mode === "view";
  // Frame the graph once the layout has settled (and whenever the data or mode changes).
  useEffect(() => {
    const timer = window.setTimeout(
      () => ref.current?.fitNodesInView(undefined, { animated: false }),
      400,
    );
    return () => window.clearTimeout(timer);
  }, [data, mode]);
  const palette = PALETTE[theme];
  const positions = new Map(
    data.nodes.map((n) => [
      n.id,
      (n.data as { position?: { x: number; y: number } } | undefined)?.position,
    ]),
  );
  // Coloured sphere with its icon, plus an amber flag badge when the party has alerts.
  const renderNode = (props: NodeRendererProps) => (
    <group>
      <SphereWithIcon {...props} image={props.node.icon ?? ""} />
      {(props.node.data as { alert?: boolean } | undefined)?.alert && (
        <Badge
          {...props}
          label="⚑"
          position="top-right"
          backgroundColor={palette.review}
          textColor={theme === "dark" ? "#0b1220" : "#ffffff"}
          strokeColor={palette["bg-surface"]}
        />
      )}
    </group>
  );
  return (
    <div className="relative h-full w-full">
      <GraphCanvas
        ref={ref}
        nodes={data.nodes}
        edges={data.edges}
        actives={data.actives}
        selections={selectedEdgeId ? [selectedEdgeId] : []}
        layoutType={view ? "forceDirected3d" : "custom"}
        cameraMode={view ? "rotate" : "pan"}
        edgeInterpolation="curved"
        edgeArrowPosition="end"
        edgeLabelPosition="natural"
        labelType="all"
        renderNode={renderNode}
        layoutOverrides={
          view
            ? { linkDistance: 220, nodeStrength: -350 }
            : {
                getNodePosition: (id: string) => {
                  const p = positions.get(id) ?? { x: 0, y: 0 };
                  return { x: p.x, y: p.y, z: 0 } as never;
                },
              }
        }
        draggable
        theme={reagraphTheme(theme)}
        onEdgeClick={(edge) => onEdgeClick(edge.id)}
      />
      <div className="absolute top-3 left-3 flex gap-1.5">
        <button
          type="button"
          aria-label="Zoom in"
          className={control}
          onClick={() => ref.current?.zoomIn()}
        >
          <Plus size={14} />
        </button>
        <button
          type="button"
          aria-label="Zoom out"
          className={control}
          onClick={() => ref.current?.zoomOut()}
        >
          <Minus size={14} />
        </button>
        <button
          type="button"
          aria-label="Fit graph"
          className={control}
          onClick={() => ref.current?.fitNodesInView()}
        >
          <Scan size={14} />
        </button>
        {view && (
          <button
            type="button"
            className="flex h-8 items-center gap-1.5 rounded-lg border border-line bg-surface px-2.5 text-xs font-medium text-ink"
            onClick={() => ref.current?.resetControls(true)}
          >
            <RotateCcw aria-hidden size={14} /> Reset camera
          </button>
        )}
      </div>
      {view && (
        <p className="absolute bottom-3 left-1/2 -translate-x-1/2 rounded-full border border-line bg-surface/90 px-3 py-1.5 text-[11px] text-muted">
          Drag to orbit · Scroll to zoom · Shift-drag to pan · Click an edge for
          details
        </p>
      )}
    </div>
  );
}
