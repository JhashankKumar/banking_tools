import { useQuery } from "@tanstack/react-query";

import { fetchRules } from "./api";

export const ruleKeys = { all: ["rules"] as const };

export const useRules = ({ enabled = true } = {}) =>
  useQuery({
    queryKey: ruleKeys.all,
    enabled,
    queryFn: ({ signal }) => fetchRules(signal),
    staleTime: 10 * 60_000,
  });
