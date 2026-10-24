import { useQuery } from "@tanstack/react-query";

import type { QueryOpts } from "@/lib/query-client";

import { fetchRules } from "./api";

export const ruleKeys = { all: ["rules"] as const };

export const useRules = ({ enabled = true }: QueryOpts = {}) =>
  useQuery({
    queryKey: ruleKeys.all,
    enabled,
    queryFn: ({ signal }) => fetchRules(signal),
    staleTime: 10 * 60_000,
  });
