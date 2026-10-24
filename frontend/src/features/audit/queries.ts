import { useQuery } from "@tanstack/react-query";

import { fetchAuditEvents, type AuditListParams } from "./api";

export const auditKeys = {
  all: ["audit"] as const,
  list: (p: AuditListParams) => [...auditKeys.all, "list", p] as const,
};

export const useAuditEvents = (p: AuditListParams) =>
  useQuery({
    queryKey: auditKeys.list(p),
    queryFn: ({ signal }) => fetchAuditEvents(p, signal),
  });
