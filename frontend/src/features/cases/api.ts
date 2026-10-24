import {
  caseGraphSchema,
  moneyPathsSchema,
} from "@/features/money-flow/schemas";
import { transactionSchema } from "@/features/transactions/schemas";
import { apiClient } from "@/lib/api-client";
import { envelope, pageEnvelope } from "@/lib/schemas";

import { caseSchema, caseSummarySchema } from "./schemas";

export interface PageParams {
  limit: number;
  offset: number;
}

const casePath = (id: string) => `/cases/${encodeURIComponent(id)}`;

export const fetchCases = (p: PageParams, signal?: AbortSignal) =>
  apiClient.get("/cases", pageEnvelope(caseSummarySchema), {
    signal,
    params: { limit: p.limit, offset: p.offset },
  });

export const fetchCase = (id: string, signal?: AbortSignal) =>
  apiClient.get(casePath(id), envelope(caseSchema), { signal });

export const fetchCaseTransactions = (
  id: string,
  p: PageParams,
  signal?: AbortSignal,
) =>
  apiClient.get(
    `${casePath(id)}/transactions`,
    pageEnvelope(transactionSchema),
    {
      signal,
      params: { limit: p.limit, offset: p.offset },
    },
  );

export const fetchMoneyPaths = (
  id: string,
  maxHops: number,
  windowHours: number,
  signal?: AbortSignal,
) =>
  apiClient.get(`${casePath(id)}/money-paths`, envelope(moneyPathsSchema), {
    signal,
    params: { max_hops: maxHops, window_hours: windowHours },
  });

export const fetchCaseGraph = (
  id: string,
  windowHours: number,
  signal?: AbortSignal,
) =>
  apiClient.get(`${casePath(id)}/graph`, envelope(caseGraphSchema), {
    signal,
    params: { window_hours: windowHours },
  });
