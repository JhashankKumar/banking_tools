import { z } from "zod";

import { isoUtcSchema, moneySchema, partyRefSchema } from "@/lib/schemas";

export const transactionStatusSchema = z.enum([
  "initiated",
  "pending",
  "accepted",
  "posted",
  "settled",
  "failed",
  "reversed",
  "returned",
  "disputed",
]);
export type TransactionStatus = z.output<typeof transactionStatusSchema>;

export const transactionSchema = z
  .object({
    id: z.string(),
    source: partyRefSchema,
    destination: partyRefSchema,
    amount: moneySchema,
    currency: z.string(),
    occurred_at: isoUtcSchema,
    status: transactionStatusSchema,
    source_status: z.string(),
    rail: z.string().nullable(),
    reference: z.string().nullable(),
    description: z.string().nullable(),
    reversal_of_transaction_id: z.string().nullable(),
    evidence_id: z.string().nullable(),
  })
  .transform((t) => ({
    id: t.id,
    source: t.source,
    destination: t.destination,
    amount: t.amount,
    currency: t.currency,
    occurredAt: t.occurred_at,
    status: t.status,
    sourceStatus: t.source_status,
    rail: t.rail,
    reference: t.reference,
    description: t.description,
    reversalOf: t.reversal_of_transaction_id,
    evidenceId: t.evidence_id,
  }));
export type Transaction = z.output<typeof transactionSchema>;
