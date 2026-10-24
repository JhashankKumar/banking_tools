import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { envelope, pageEnvelope } from "@/lib/schemas";

import { caseSchema, caseSummarySchema } from "./schemas";

export interface PageParams {
  limit: number;
  offset: number;
}

/** One key factory for everything under a case (graph and money paths included). */
export const caseKeys = {
  all: ["cases"] as const,
  list: (p: PageParams) => [...caseKeys.all, "list", p] as const,
  detail: (id: string) => [...caseKeys.all, "detail", id] as const,
  transactions: (id: string, p: PageParams) =>
    [...caseKeys.all, "transactions", id, p] as const,
  graph: (id: string, windowHours: number) =>
    [...caseKeys.all, "graph", id, windowHours] as const,
  moneyPaths: (id: string, maxHops: number, windowHours: number) =>
    [...caseKeys.all, "money-paths", id, maxHops, windowHours] as const,
};

export const useCasesList = (p: PageParams) =>
  useQuery({
    queryKey: caseKeys.list(p),
    queryFn: ({ signal }) =>
      apiClient.get("/cases", pageEnvelope(caseSummarySchema), {
        signal,
        params: { limit: p.limit, offset: p.offset },
      }),
  });

export const useCase = (id: string) =>
  useQuery({
    queryKey: caseKeys.detail(id),
    queryFn: ({ signal }) =>
      apiClient.get(`/cases/${encodeURIComponent(id)}`, envelope(caseSchema), {
        signal,
      }),
  });
