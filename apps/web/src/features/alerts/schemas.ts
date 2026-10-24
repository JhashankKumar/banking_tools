import { z } from "zod";

import { isoUtcSchema, partyRefSchema } from "@/lib/schemas";

export const alertSchema = z
  .object({
    id: z.string(),
    rule: z.object({ id: z.string(), version: z.string(), title: z.string() }),
    entity: partyRefSchema,
    trigger_transaction_id: z.string(),
    transaction_ids: z.array(z.string()),
    case_id: z.string().nullable(),
    triggered_at: isoUtcSchema,
    explanation: z.string(),
    metrics: z.record(z.string(), z.string()),
    evidence_id: z.string().nullable(),
  })
  .transform((a) => ({
    id: a.id,
    rule: a.rule,
    entity: a.entity,
    triggerTransactionId: a.trigger_transaction_id,
    transactionIds: a.transaction_ids,
    caseId: a.case_id,
    triggeredAt: a.triggered_at,
    explanation: a.explanation,
    metrics: a.metrics,
    evidenceId: a.evidence_id,
  }));
export type Alert = z.output<typeof alertSchema>;
