"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { useAlerts } from "@/features/alerts/queries";
import {
  caseGraphSchema,
  moneyPathsSchema,
} from "@/features/money-flow/schemas";
import { useRules } from "@/features/rules/queries";
import { transactionSchema } from "@/features/transactions/schemas";
import { apiClient } from "@/lib/api-client";
import { envelope, pageEnvelope } from "@/lib/schemas";

import { caseKeys, useCase } from "../queries";

export function useCasePage(caseId: string) {
  const [windowHours, setWindowHours] = useState(24);
  const [maxHops, setMaxHops] = useState(3);
  const [txOffset, setTxOffset] = useState(0);
  const base = `/cases/${encodeURIComponent(caseId)}`;

  const caseQuery = useCase(caseId);
  const transactionsQuery = useQuery({
    queryKey: caseKeys.transactions(caseId, { limit: 50, offset: txOffset }),
    queryFn: ({ signal }) =>
      apiClient.get(`${base}/transactions`, pageEnvelope(transactionSchema), {
        signal,
        params: { limit: 50, offset: txOffset },
      }),
    enabled: caseQuery.isSuccess,
  });
  const alertsQuery = useAlerts(
    { limit: 50, offset: 0, caseId },
    { enabled: caseQuery.isSuccess },
  );
  const rulesQuery = useRules({ enabled: caseQuery.isSuccess });
  const moneyPathsQuery = useQuery({
    queryKey: caseKeys.moneyPaths(caseId, maxHops, windowHours),
    queryFn: ({ signal }) =>
      apiClient.get(`${base}/money-paths`, envelope(moneyPathsSchema), {
        signal,
        params: { max_hops: maxHops, window_hours: windowHours },
      }),
    enabled: caseQuery.isSuccess,
  });
  const graphQuery = useQuery({
    queryKey: caseKeys.graph(caseId, windowHours),
    queryFn: ({ signal }) =>
      apiClient.get(`${base}/graph`, envelope(caseGraphSchema), {
        signal,
        params: { window_hours: windowHours },
      }),
    enabled: caseQuery.isSuccess,
  });

  return {
    caseQuery,
    transactionsQuery,
    alertsQuery,
    rulesQuery,
    moneyPathsQuery,
    graphQuery,
    windowHours,
    setWindowHours,
    maxHops,
    setMaxHops,
    setTxOffset,
  };
}
export type CasePageData = ReturnType<typeof useCasePage>;
