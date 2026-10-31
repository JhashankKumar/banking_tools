import { z } from "zod";

import { apiClient } from "@/lib/api-client";
import { envelope } from "@/lib/schemas";

import { safetyCheckSchema, safetyRunSchema } from "./schemas";

export const fetchSafetyChecks = (signal?: AbortSignal) =>
  apiClient.get("/safety/checks", envelope(z.array(safetyCheckSchema)), {
    signal,
  });

export const runSafetyChecks = () =>
  apiClient.post("/safety/runs", {}, envelope(safetyRunSchema));
