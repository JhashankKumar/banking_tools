import { useQuery } from "@tanstack/react-query";

import type { QueryOpts } from "@/lib/query-client";

import { fetchAlerts, type AlertListParams } from "./api";

export const alertKeys = {
  all: ["alerts"] as const,
  list: (p: AlertListParams) => [...alertKeys.all, "list", p] as const,
};

export const useAlerts = (
  p: AlertListParams,
  { enabled = true }: QueryOpts = {},
) =>
  useQuery({
    queryKey: alertKeys.list(p),
    enabled,
    queryFn: ({ signal }) => fetchAlerts(p, signal),
  });
