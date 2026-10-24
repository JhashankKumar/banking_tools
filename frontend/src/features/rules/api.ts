import { z } from "zod";

import { apiClient } from "@/lib/api-client";
import { envelope } from "@/lib/schemas";

import { ruleSchema } from "./schemas";

export const fetchRules = (signal?: AbortSignal) =>
  apiClient.get("/rules", envelope(z.array(ruleSchema)), { signal });
