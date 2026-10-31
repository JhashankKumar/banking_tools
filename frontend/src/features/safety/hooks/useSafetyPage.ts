"use client";

import { ApiError, asApiError } from "@/lib/api-error";

import { useRunSafetyChecks, useSafetyChecks } from "../queries";

const IN_PROGRESS = "A run is already in progress.";

function runError(error: unknown): ApiError | null {
  if (!error) return null;
  const e = asApiError(error);
  return e.code === "SAFETY_RUN_IN_PROGRESS"
    ? new ApiError({ ...e, message: IN_PROGRESS })
    : e;
}

export function useSafetyPage() {
  const checks = useSafetyChecks();
  const run = useRunSafetyChecks();
  return {
    checks,
    run: run.data ?? null,
    running: run.isPending,
    error: runError(run.error),
    start: () => run.mutate(),
  };
}
