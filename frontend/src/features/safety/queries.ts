import { useMutation, useQuery } from "@tanstack/react-query";

import { fetchSafetyChecks, runSafetyChecks } from "./api";

export const safetyKeys = {
  all: ["safety"] as const,
  checks: () => [...safetyKeys.all, "checks"] as const,
};

export const useSafetyChecks = () =>
  useQuery({
    queryKey: safetyKeys.checks(),
    queryFn: ({ signal }) => fetchSafetyChecks(signal),
  });

/** Runs are not stored: the page shows the run just made (the audit log records it). */
export const useRunSafetyChecks = () =>
  useMutation({
    mutationKey: [...safetyKeys.all, "run"],
    mutationFn: runSafetyChecks,
  });
