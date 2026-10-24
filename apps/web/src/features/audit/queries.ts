import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { pageEnvelope } from "@/lib/schemas";

import { auditEventSchema } from "./schemas";

export interface AuditListParams {
  limit: number;
  offset: number;
  action?: string;
}

export const auditKeys = {
  all: ["audit"] as const,
  list: (p: AuditListParams) => [...auditKeys.all, "list", p] as const,
};

export const useAuditEvents = (p: AuditListParams) =>
  useQuery({
    queryKey: auditKeys.list(p),
    queryFn: ({ signal }) =>
      apiClient.get("/audit-logs", pageEnvelope(auditEventSchema), {
        signal,
        params: { limit: p.limit, offset: p.offset, action: p.action },
      }),
  });
