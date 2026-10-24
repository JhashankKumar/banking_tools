import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { QueryOpts } from "@/lib/query-client";

import { askQuestion, fetchChat, fetchChats, type AskBody } from "./api";

export const copilotKeys = {
  all: ["copilot"] as const,
  chats: (caseId: string) => [...copilotKeys.all, "chats", caseId] as const,
  chat: (caseId: string, chatId: string) =>
    [...copilotKeys.all, "chat", caseId, chatId] as const,
};

export const useChats = (caseId: string) =>
  useQuery({
    queryKey: copilotKeys.chats(caseId),
    queryFn: ({ signal }) => fetchChats(caseId, signal),
  });

export const useChat = (
  caseId: string,
  chatId: string,
  { enabled = true }: QueryOpts = {},
) =>
  useQuery({
    queryKey: copilotKeys.chat(caseId, chatId),
    enabled,
    queryFn: ({ signal }) => fetchChat(caseId, chatId, signal),
  });

export function useAsk(caseId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [...copilotKeys.all, "ask", caseId],
    mutationFn: (body: AskBody) => askQuestion(caseId, body),
    onSettled: (data) =>
      Promise.all([
        client.invalidateQueries({ queryKey: copilotKeys.chats(caseId) }),
        data &&
          client.invalidateQueries({
            queryKey: copilotKeys.chat(caseId, data.chat.id),
          }),
      ]),
  });
}
