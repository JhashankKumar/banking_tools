"use client";

import { useState } from "react";

import { useAlerts } from "@/features/alerts/queries";
import { useRules } from "@/features/rules/queries";

import {
  useCase,
  useCaseGraph,
  useCaseTransactions,
  useMoneyPaths,
} from "../queries";

export function useCasePage(caseId: string) {
  const [windowHours, setWindowHours] = useState(24);
  const [maxHops, setMaxHops] = useState(3);
  const [txOffset, setTxOffset] = useState(0);

  const caseQuery = useCase(caseId);
  // Nothing else is requested until the case loads: unknown or forbidden cases cost one call.
  const ready = { enabled: caseQuery.isSuccess };
  const transactionsQuery = useCaseTransactions(
    caseId,
    { limit: 50, offset: txOffset },
    ready,
  );
  const alertsQuery = useAlerts({ limit: 50, offset: 0, caseId }, ready);
  const rulesQuery = useRules(ready);
  const moneyPathsQuery = useMoneyPaths(caseId, maxHops, windowHours, ready);
  const graphQuery = useCaseGraph(caseId, windowHours, ready);

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
