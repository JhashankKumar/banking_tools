import { z } from "zod";

/** `{ "data": T }` → T */
export function envelope<T extends z.ZodType>(item: T): z.ZodType<z.output<T>> {
  return z
    .object({ data: item })
    .transform((v: unknown) => (v as { data: z.output<T> }).data);
}

const pageMetaSchema = z.object({
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});
export type PageMeta = z.output<typeof pageMetaSchema>;
export interface Page<T> {
  items: T[];
  page: PageMeta;
}

/** `{ "data": T[], "page": {...} }` → `{ items, page }` */
export function pageEnvelope<T extends z.ZodType>(
  item: T,
): z.ZodType<Page<z.output<T>>> {
  return z
    .object({ data: z.array(item), page: pageMetaSchema })
    .transform((v: unknown) => {
      const { data, page } = v as { data: z.output<T>[]; page: PageMeta };
      return { items: data, page };
    });
}

export const errorEnvelopeSchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
    details: z.array(z.object({ field: z.string(), message: z.string() })),
    request_id: z.string().nullable(),
  }),
});

export const partyRefSchema = z.object({
  type: z.enum(["account", "beneficiary"]),
  id: z.string(),
});
export type PartyRef = z.output<typeof partyRefSchema>;

/** Money stays a two-decimal string end to end; display with formatMoney. */
export const moneySchema = z.string().regex(/^\d+\.\d{2}$/);
export const isoUtcSchema = z.iso.datetime();
