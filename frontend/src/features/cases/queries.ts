import { useQuery } from "@tanstack/react-query";

import {
  fetchCase,
  fetchCaseGraph,
  fetchCases,
  fetchCaseTransactions,
  fetchMoneyPaths,
  type PageParams,
} from "./api";

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
    queryFn: ({ signal }) => fetchCases(p, signal),
  });

export const useCase = (id: string) =>
  useQuery({
    queryKey: caseKeys.detail(id),
    queryFn: ({ signal }) => fetchCase(id, signal),
  });

export const useCaseTransactions = (
  id: string,
  p: PageParams,
  { enabled = true } = {},
) =>
  useQuery({
    queryKey: caseKeys.transactions(id, p),
    enabled,
    queryFn: ({ signal }) => fetchCaseTransactions(id, p, signal),
  });

export const useMoneyPaths = (
  id: string,
  maxHops: number,
  windowHours: number,
  { enabled = true } = {},
) =>
  useQuery({
    queryKey: caseKeys.moneyPaths(id, maxHops, windowHours),
    enabled,
    queryFn: ({ signal }) => fetchMoneyPaths(id, maxHops, windowHours, signal),
  });

export const useCaseGraph = (
  id: string,
  windowHours: number,
  { enabled = true } = {},
) =>
  useQuery({
    queryKey: caseKeys.graph(id, windowHours),
    enabled,
    queryFn: ({ signal }) => fetchCaseGraph(id, windowHours, signal),
  });
