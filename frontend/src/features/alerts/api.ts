import { apiClient } from "@/lib/api-client";
import { pageEnvelope } from "@/lib/schemas";

import { alertSchema } from "./schemas";

export interface AlertListParams {
  limit: number;
  offset: number;
  ruleId?: string;
  caseId?: string;
}

export const fetchAlerts = (p: AlertListParams, signal?: AbortSignal) =>
  apiClient.get("/alerts", pageEnvelope(alertSchema), {
    signal,
    params: {
      limit: p.limit,
      offset: p.offset,
      rule_id: p.ruleId,
      case_id: p.caseId,
    },
  });
