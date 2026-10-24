import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { pageEnvelope } from "@/lib/schemas";

import { alertSchema } from "./schemas";

export interface AlertListParams {
  limit: number;
  offset: number;
  ruleId?: string;
  caseId?: string;
}

export const alertKeys = {
  all: ["alerts"] as const,
  list: (p: AlertListParams) => [...alertKeys.all, "list", p] as const,
};

export const useAlerts = (p: AlertListParams, { enabled = true } = {}) =>
  useQuery({
    queryKey: alertKeys.list(p),
    enabled,
    queryFn: ({ signal }) =>
      apiClient.get("/alerts", pageEnvelope(alertSchema), {
        signal,
        params: {
          limit: p.limit,
          offset: p.offset,
          rule_id: p.ruleId,
          case_id: p.caseId,
        },
      }),
  });
