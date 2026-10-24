import type {
  GraphEdge as ReagraphEdge,
  GraphNode as ReagraphNode,
} from "reagraph";

import type { Theme } from "@/components/theme/use-theme";
import { formatMoney, formatTime } from "@/lib/format";
import type { PartyRef } from "@/lib/schemas";

import { PALETTE } from "./graph-theme";
import { nodeIcon } from "./icons";
import type { CaseGraph, FlowEdge, GraphNode, MoneyPath } from "./schemas";

export interface GraphViewOptions {
  nodes: "all" | "case";
  edges: "all" | "path";
  theme: Theme;
}

export interface GraphData {
  nodes: ReagraphNode[];
  edges: ReagraphEdge[];
  actives: string[];
}

type AnyEdge = FlowEdge & { inCase?: boolean };

/** Pure mapping from API graph + selected money path to what Reagraph draws. */
export function toGraphData(
  graph: CaseGraph,
  path: MoneyPath | null,
  opts: GraphViewOptions,
): GraphData {
  const palette = PALETTE[opts.theme];
  const pathEdgeIds = new Set(path?.edges.map((e) => e.transactionId) ?? []);
  const pathNodeIds = new Set(
    path?.edges.flatMap((e) => [e.source.id, e.destination.id]) ?? [],
  );

  // A path can leave the one-level neighbourhood; add whatever the graph doesn't have.
  const edges: AnyEdge[] = [...graph.edges];
  const known = new Set(edges.map((e) => e.transactionId));
  for (const e of path?.edges ?? [])
    if (!known.has(e.transactionId)) edges.push(e);
  const nodes: GraphNode[] = [...graph.nodes];
  const nodeIds = new Set(nodes.map((n) => n.id));
  const addParty = (p: PartyRef) => {
    if (nodeIds.has(p.id)) return;
    nodeIds.add(p.id);
    nodes.push({
      id: p.id,
      type: p.type,
      label: p.id,
      status: null,
      isCaseParty: false,
      alertIds: [],
    });
  };
  edges.forEach((e) => (addParty(e.source), addParty(e.destination)));

  let visibleNodes =
    opts.nodes === "case" ? nodes.filter((n) => n.isCaseParty) : nodes;
  const visibleIds = new Set(visibleNodes.map((n) => n.id));
  let visibleEdges = edges.filter(
    (e) => visibleIds.has(e.source.id) && visibleIds.has(e.destination.id),
  );
  if (opts.edges === "path" && path) {
    visibleEdges = visibleEdges.filter((e) => pathEdgeIds.has(e.transactionId));
    const touched = new Set(
      visibleEdges.flatMap((e) => [e.source.id, e.destination.id]),
    );
    visibleNodes = visibleNodes.filter((n) => touched.has(n.id));
  }

  const positions = timeOrderedPositions(
    visibleNodes,
    visibleEdges,
    pathNodeIds,
  );

  return {
    nodes: visibleNodes.map((n) => ({
      id: n.id,
      label: n.alertIds.length > 0 ? `${n.id} ⚑` : n.id,
      subLabel: n.label !== n.id ? n.label : n.type,
      icon: nodeIcon(n.type, opts.theme),
      fill: pathNodeIds.has(n.id)
        ? palette.selected
        : n.isCaseParty
          ? palette.primary
          : palette.counterparty,
      size: n.isCaseParty ? 14 : 10,
      data: {
        alert: n.alertIds.length > 0,
        type: n.type,
        isCaseParty: n.isCaseParty,
        position: positions.get(n.id),
      },
    })),
    edges: visibleEdges.map((e) => ({
      id: e.transactionId,
      source: e.source.id,
      target: e.destination.id,
      label: `${formatMoney(e.amount, e.currency)} · ${formatTime(e.occurredAt)}`,
      fill: pathEdgeIds.has(e.transactionId)
        ? palette.selected
        : e.kind === "reversal"
          ? palette.reversal
          : palette.counterparty,
      dashed: !e.isFinal && e.kind !== "reversal",
      interpolation: "curved",
      size: pathEdgeIds.has(e.transactionId) ? 3 : 1.5,
    })),
    actives: [...pathNodeIds, ...pathEdgeIds],
  };
}

const COLUMN = 110;
const LANE = 60;

/**
 * Left-to-right layout for the "3D look": x follows when a party first appears (senders before
 * receivers of the same transfer), so money visibly flows rightwards. Path parties sit on the
 * centre line; other case parties and counterparties alternate above and below it.
 */
function timeOrderedPositions(
  nodes: GraphNode[],
  edges: AnyEdge[],
  pathNodeIds: Set<string>,
): Map<string, { x: number; y: number }> {
  const firstSeen = new Map<string, string>();
  const see = (id: string, key: string) => {
    const current = firstSeen.get(id);
    if (current === undefined || key < current) firstSeen.set(id, key);
  };
  for (const e of edges) {
    see(e.source.id, `${e.occurredAt}|0|${e.transactionId}`);
    see(e.destination.id, `${e.occurredAt}|1|${e.transactionId}`);
  }
  const ordered = [...nodes].sort((a, b) => {
    const ka = firstSeen.get(a.id) ?? "~";
    const kb = firstSeen.get(b.id) ?? "~";
    return ka === kb ? a.id.localeCompare(b.id) : ka < kb ? -1 : 1;
  });
  const offset = ((ordered.length - 1) * COLUMN) / 2;
  let side = 0;
  return new Map(
    ordered.map((n, i) => {
      if (pathNodeIds.has(n.id))
        return [n.id, { x: i * COLUMN - offset, y: 0 }];
      side += 1;
      const lane = n.isCaseParty ? 1 : 2;
      return [
        n.id,
        { x: i * COLUMN - offset, y: (side % 2 === 0 ? -1 : 1) * lane * LANE },
      ];
    }),
  );
}
