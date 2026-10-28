import { apiClient } from "@/lib/api-client";
import { envelope, pageEnvelope } from "@/lib/schemas";

import { askOutSchema, chatSchema, chatSummarySchema } from "./schemas";

const casePath = (caseId: string) => `/cases/${encodeURIComponent(caseId)}`;

export interface AskBody {
  chatId: string | null;
  question: string;
}

export const fetchChats = (caseId: string, signal?: AbortSignal) =>
  apiClient.get(`${casePath(caseId)}/chats`, pageEnvelope(chatSummarySchema), {
    signal,
  });

export const fetchChat = (
  caseId: string,
  chatId: string,
  signal?: AbortSignal,
) =>
  apiClient.get(
    `${casePath(caseId)}/chats/${encodeURIComponent(chatId)}`,
    envelope(chatSchema),
    { signal },
  );

export const askQuestion = (caseId: string, body: AskBody) =>
  apiClient.post(
    `${casePath(caseId)}/copilot/questions`,
    { chat_id: body.chatId, question: body.question },
    envelope(askOutSchema),
  );
