import { apiClient } from "@/lib/api-client";
import { pageEnvelope } from "@/lib/schemas";

import { auditEventSchema } from "./schemas";

export interface AuditListParams {
  limit: number;
  offset: number;
  action?: string;
}

export const fetchAuditEvents = (p: AuditListParams, signal?: AbortSignal) =>
  apiClient.get("/audit-logs", pageEnvelope(auditEventSchema), {
    signal,
    params: { limit: p.limit, offset: p.offset, action: p.action },
  });
