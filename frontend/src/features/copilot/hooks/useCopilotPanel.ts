"use client";

import { useState } from "react";

import { asApiError } from "@/lib/api-error";

import { keptChatId } from "../api";
import { useAsk, useChat, useChats } from "../queries";

export type PanelView = "list" | "chat" | "new";

/** Panel navigation (list ⇄ chat) and asking; one chat is open at a time. */
export function useCopilotPanel(caseId: string) {
  const [view, setView] = useState<PanelView>("list");
  const [chatId, setChatId] = useState<string | null>(null);
  const chats = useChats(caseId);
  const chat = useChat(caseId, chatId ?? "", {
    enabled: view === "chat" && chatId !== null,
  });
  const askMutation = useAsk(caseId);

  const openChat = (id: string) => {
    askMutation.reset();
    setChatId(id);
    setView("chat");
  };

  return {
    view,
    chats,
    chat,
    pending: askMutation.isPending,
    error: askMutation.error ? asApiError(askMutation.error) : null,
    openChat,
    newChat: () => {
      askMutation.reset();
      setChatId(null);
      setView("new");
    },
    backToList: () => {
      askMutation.reset();
      setView("list");
    },
    ask: (question: string) =>
      askMutation.mutate(
        { chatId: view === "chat" ? chatId : null, question },
        {
          onSuccess: (data) => openChat(data.chat.id),
          // The question was kept in a chat: show it there (with the error) so a retry
          // asks in that chat instead of starting another.
          onError: (failure) => {
            const kept = keptChatId(failure);
            if (kept === null) return;
            setChatId(kept);
            setView("chat");
          },
        },
      ),
  };
}
export type CopilotPanelState = ReturnType<typeof useCopilotPanel>;
