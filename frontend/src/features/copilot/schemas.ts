import { z } from "zod";

import { isoUtcSchema } from "@/lib/schemas";

export const answerItemSchema = z.object({
  text: z.string(),
  citations: z.array(z.string()),
});
export type AnswerItem = z.output<typeof answerItemSchema>;

export const copilotAnswerSchema = z
  .object({
    kind: z.enum(["answer", "decline"]),
    records: z.array(answerItemSchema),
    calculated: z.array(answerItemSchema),
    not_established: z.array(z.string()),
    next_checks: z.array(z.string()),
    suggestions: z.array(z.string()),
    steps: z.array(z.string()),
  })
  .transform((a) => ({
    kind: a.kind,
    records: a.records,
    calculated: a.calculated,
    notEstablished: a.not_established,
    nextChecks: a.next_checks,
    suggestions: a.suggestions,
    steps: a.steps,
  }));
export type CopilotAnswer = z.output<typeof copilotAnswerSchema>;

export const chatSummarySchema = z
  .object({
    id: z.string(),
    title: z.string(),
    author_username: z.string(),
    updated_at: isoUtcSchema,
    message_count: z.number(),
    is_own: z.boolean(),
  })
  .transform((c) => ({
    id: c.id,
    title: c.title,
    authorUsername: c.author_username,
    updatedAt: c.updated_at,
    messageCount: c.message_count,
    isOwn: c.is_own,
  }));
export type ChatSummary = z.output<typeof chatSummarySchema>;

export const messageSchema = z
  .object({
    id: z.string(),
    role: z.enum(["user", "assistant"]),
    question: z.string().nullable(),
    answer: copilotAnswerSchema.nullable(),
    created_at: isoUtcSchema,
  })
  .transform((m) => ({
    id: m.id,
    role: m.role,
    question: m.question,
    answer: m.answer,
    createdAt: m.created_at,
  }));
export type ChatMessage = z.output<typeof messageSchema>;

export const chatSchema = z
  .object({
    id: z.string(),
    title: z.string(),
    author_username: z.string(),
    is_own: z.boolean(),
    messages: z.array(messageSchema),
  })
  .transform((c) => ({
    id: c.id,
    title: c.title,
    authorUsername: c.author_username,
    isOwn: c.is_own,
    messages: c.messages,
  }));
export type Chat = z.output<typeof chatSchema>;

export const askOutSchema = z.object({
  chat: chatSummarySchema,
  message: messageSchema,
});
export type AskOut = z.output<typeof askOutSchema>;
