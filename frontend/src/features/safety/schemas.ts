import { z } from "zod";

import { isoUtcSchema } from "@/lib/schemas";

/** Same order as the API's catalogue (backend/app/modules/safety/contract.py). */
export const CATEGORY_ORDER = [
  "Prompt injection",
  "Customer information",
  "Access control",
  "Tool abuse",
  "Grounding",
  "Limits",
  "Audit and secrets",
] as const;
export type Category = (typeof CATEGORY_ORDER)[number];

export const CHECK_STATUSES = ["passed", "failed", "skipped"] as const;
export type CheckStatus = (typeof CHECK_STATUSES)[number];

const checkFields = {
  id: z.string(),
  category: z.enum(CATEGORY_ORDER),
  attack: z.string(),
  defence: z.string(),
};

export const safetyCheckSchema = z.object(checkFields);
export type SafetyCheck = z.output<typeof safetyCheckSchema>;

export const safetyRunSchema = z
  .object({
    ran_at: isoUtcSchema,
    duration_ms: z.number(),
    counts: z.object({
      passed: z.number(),
      failed: z.number(),
      skipped: z.number(),
    }),
    results: z.array(
      z
        .object({
          ...checkFields,
          status: z.enum(CHECK_STATUSES),
          observed: z.string(),
          duration_ms: z.number(),
        })
        .transform(({ duration_ms, ...r }) => ({
          ...r,
          durationMs: duration_ms,
        })),
    ),
  })
  .transform((r) => ({
    ranAt: r.ran_at,
    durationMs: r.duration_ms,
    counts: r.counts,
    results: r.results,
  }));
export type SafetyRun = z.output<typeof safetyRunSchema>;
export type SafetyResult = SafetyRun["results"][number];
