import { z } from "zod";

export const ruleSchema = z
  .object({
    id: z.string(),
    version: z.string(),
    code: z.string(),
    title: z.string(),
    description: z.string(),
    required_fields: z.array(z.string()),
    false_positive_caveats: z.array(z.string()),
    parameters: z.record(z.string(), z.string()),
  })
  .transform((r) => ({
    id: r.id,
    version: r.version,
    code: r.code,
    title: r.title,
    description: r.description,
    requiredFields: r.required_fields,
    falsePositiveCaveats: r.false_positive_caveats,
    parameters: r.parameters,
  }));
export type Rule = z.output<typeof ruleSchema>;
