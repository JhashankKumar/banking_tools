/** Test double for reagraph's WebGL GraphCanvas (jsdom has no WebGL). */
import { forwardRef, useImperativeHandle } from "react";

interface Props {
  nodes: { id: string; label?: string }[];
  edges: { id: string; label?: string }[];
  layoutType?: string;
  cameraMode?: string;
  actives?: string[];
  onNodeClick?: (node: { id: string }) => void;
  onEdgeClick?: (edge: { id: string }) => void;
}

export const GraphCanvas = forwardRef(function GraphCanvas(props: Props, ref) {
  useImperativeHandle(ref, () => ({
    centerGraph() {},
    fitNodesInView() {},
    zoomIn() {},
    zoomOut() {},
    resetControls() {},
  }));
  return (
    <div
      data-testid="reagraph"
      data-layout={props.layoutType}
      data-camera={props.cameraMode}
      data-actives={(props.actives ?? []).join(",")}
    >
      {props.nodes.map((n) => (
        <button
          key={n.id}
          type="button"
          data-kind="node"
          onClick={() => props.onNodeClick?.({ id: n.id })}
        >
          node {n.id}
        </button>
      ))}
      {props.edges.map((e) => (
        <button
          key={e.id}
          type="button"
          data-kind="edge"
          onClick={() => props.onEdgeClick?.({ id: e.id })}
        >
          edge {e.id}
        </button>
      ))}
    </div>
  );
});

export const SphereWithIcon = () => null;
export const Badge = () => null;
