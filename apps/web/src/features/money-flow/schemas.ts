import { z } from "zod";

import { transactionStatusSchema } from "@/features/transactions/schemas";
import { isoUtcSchema, moneySchema, partyRefSchema } from "@/lib/schemas";

const edgeFields = {
  transaction_id: z.string(),
  kind: z.enum(["transfer", "reversal"]),
  source: partyRefSchema,
  destination: partyRefSchema,
  amount: moneySchema,
  currency: z.string(),
  occurred_at: isoUtcSchema,
  status: transactionStatusSchema,
  is_final: z.boolean(),
  reversed_by: z.array(z.string()),
  rail: z.string().nullable(),
  reference: z.string().nullable(),
  evidence_id: z.string().nullable(),
};

interface WireEdge {
  transaction_id: string;
  kind: "transfer" | "reversal";
  source: z.output<typeof partyRefSchema>;
  destination: z.output<typeof partyRefSchema>;
  amount: string;
  currency: string;
  occurred_at: string;
  status: z.output<typeof transactionStatusSchema>;
  is_final: boolean;
  reversed_by: string[];
  rail: string | null;
  reference: string | null;
  evidence_id: string | null;
}

const toEdge = (e: WireEdge) => ({
  transactionId: e.transaction_id,
  kind: e.kind,
  source: e.source,
  destination: e.destination,
  amount: e.amount,
  currency: e.currency,
  occurredAt: e.occurred_at,
  status: e.status,
  isFinal: e.is_final,
  reversedBy: e.reversed_by,
  rail: e.rail,
  reference: e.reference,
  evidenceId: e.evidence_id,
});
export type FlowEdge = ReturnType<typeof toEdge>;

export const graphEdgeSchema = z
  .object({ ...edgeFields, in_case: z.boolean() })
  .transform((e) => ({ ...toEdge(e), inCase: e.in_case }));
export type GraphEdge = z.output<typeof graphEdgeSchema>;

export const graphNodeSchema = z
  .object({
    id: z.string(),
    type: z.enum(["account", "beneficiary"]),
    label: z.string(),
    status: z.string().nullable(),
    is_case_party: z.boolean(),
    alert_ids: z.array(z.string()),
  })
  .transform((n) => ({
    id: n.id,
    type: n.type,
    label: n.label,
    status: n.status,
    isCaseParty: n.is_case_party,
    alertIds: n.alert_ids,
  }));
export type GraphNode = z.output<typeof graphNodeSchema>;

export const caseGraphSchema = z
  .object({
    case_id: z.string(),
    window: z.object({ start: isoUtcSchema, end: isoUtcSchema }).nullable(),
    truncated: z.boolean(),
    nodes: z.array(graphNodeSchema),
    edges: z.array(graphEdgeSchema),
  })
  .transform((g) => ({
    caseId: g.case_id,
    window: g.window,
    truncated: g.truncated,
    nodes: g.nodes,
    edges: g.edges,
  }));
export type CaseGraph = z.output<typeof caseGraphSchema>;

const pathEdgeSchema = z
  .object({ ...edgeFields, hop: z.number() })
  .transform((e) => ({ ...toEdge(e), hop: e.hop }));
export type PathEdge = z.output<typeof pathEdgeSchema>;

export const moneyPathSchema = z
  .object({
    hops: z.number(),
    is_cycle: z.boolean(),
    returned_by_reversal: z.boolean(),
    has_non_final_edges: z.boolean(),
    contains_reversal: z.boolean(),
    currencies: z.array(z.string()),
    started_at: isoUtcSchema,
    ended_at: isoUtcSchema,
    elapsed_seconds: z.number(),
    limitations: z.array(z.string()),
    edges: z.array(pathEdgeSchema),
  })
  .transform((p) => ({
    hops: p.hops,
    isCycle: p.is_cycle,
    returnedByReversal: p.returned_by_reversal,
    hasNonFinalEdges: p.has_non_final_edges,
    containsReversal: p.contains_reversal,
    currencies: p.currencies,
    startedAt: p.started_at,
    endedAt: p.ended_at,
    elapsedSeconds: p.elapsed_seconds,
    limitations: p.limitations,
    edges: p.edges,
  }));
export type MoneyPath = z.output<typeof moneyPathSchema>;

export const moneyPathsSchema = z
  .object({ truncated: z.boolean(), paths: z.array(moneyPathSchema) })
  .transform((m) => ({ truncated: m.truncated, paths: m.paths }));
export type MoneyPaths = z.output<typeof moneyPathsSchema>;

/** Shown when no money path is selected (same sentence as the API's graph/paths.py). */
export const DATASET_LIMITATION =
  "Limited to records in this dataset. A path does not establish ownership, intent, available balance, or settlement finality.";
