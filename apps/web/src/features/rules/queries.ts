import { useQuery } from "@tanstack/react-query";
import { z } from "zod";

import { apiClient } from "@/lib/api-client";
import { envelope } from "@/lib/schemas";

import { ruleSchema } from "./schemas";

export const ruleKeys = { all: ["rules"] as const };

export const useRules = ({ enabled = true } = {}) =>
  useQuery({
    queryKey: ruleKeys.all,
    enabled,
    queryFn: ({ signal }) =>
      apiClient.get("/rules", envelope(z.array(ruleSchema)), { signal }),
    staleTime: 10 * 60_000,
  });
