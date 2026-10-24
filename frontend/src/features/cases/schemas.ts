import { z } from "zod";

import { isoUtcSchema } from "@/lib/schemas";

export const caseStatusSchema = z.enum([
  "open",
  "in_review",
  "escalated",
  "closed",
]);
export type CaseStatus = z.output<typeof caseStatusSchema>;
export const CASE_STATUS_LABEL: Record<CaseStatus, string> = {
  open: "Open",
  in_review: "In review",
  escalated: "Escalated",
  closed: "Closed",
};

export const caseSummarySchema = z
  .object({
    id: z.string(),
    title: z.string(),
    status: caseStatusSchema,
    opened_at: isoUtcSchema,
    alert_count: z.number(),
    transaction_count: z.number(),
  })
  .transform((c) => ({
    id: c.id,
    title: c.title,
    status: c.status,
    openedAt: c.opened_at,
    alertCount: c.alert_count,
    transactionCount: c.transaction_count,
  }));
export type CaseSummary = z.output<typeof caseSummarySchema>;

export const caseSchema = z
  .object({
    id: z.string(),
    title: z.string(),
    status: caseStatusSchema,
    opened_at: isoUtcSchema,
    alert_ids: z.array(z.string()),
    transaction_count: z.number(),
  })
  .transform((c) => ({
    id: c.id,
    title: c.title,
    status: c.status,
    openedAt: c.opened_at,
    alertIds: c.alert_ids,
    transactionCount: c.transaction_count,
  }));
export type Case = z.output<typeof caseSchema>;
