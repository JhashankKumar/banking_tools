import { z } from "zod";

import { isoUtcSchema } from "@/lib/schemas";

export const OUTCOMES = ["success", "denied", "failure"] as const;
export type Outcome = (typeof OUTCOMES)[number];

/** Action names the API records (services/api/app/modules/*); values seen in the data are added at runtime. */
export const KNOWN_ACTIONS = [
  "auth.login.succeeded",
  "auth.login.failed",
  "user.created",
  "user.updated",
  "alert.list.viewed",
  "alert.viewed",
  "case.list.viewed",
  "case.viewed",
  "case.transactions.viewed",
  "case.graph.viewed",
  "case.money_paths.viewed",
  "detection.run",
  "audit.viewed",
] as const;

export const auditEventSchema = z
  .object({
    id: z.number(),
    occurred_at: isoUtcSchema,
    actor_username: z.string().nullable(),
    action: z.string(),
    resource_type: z.string().nullable(),
    resource_id: z.string().nullable(),
    outcome: z.enum(OUTCOMES),
    request_id: z.string().nullable(),
    details: z.record(z.string(), z.string()),
  })
  .transform((e) => ({
    id: e.id,
    occurredAt: e.occurred_at,
    actorUsername: e.actor_username,
    action: e.action,
    resourceType: e.resource_type,
    resourceId: e.resource_id,
    outcome: e.outcome,
    requestId: e.request_id,
    details: e.details,
  }));
export type AuditEvent = z.output<typeof auditEventSchema>;

/** Who to show in the Actor column when the event has no signed-in user. */
export const actorLabel = (e: AuditEvent): string =>
  e.actorUsername ?? (e.action === "detection.run" ? "system" : "unknown");
