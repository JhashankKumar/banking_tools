"use client";

import { useState } from "react";

import { asApiError } from "@/lib/api-error";

import { keptChatId } from "../api";
import { useAsk, useChat, useChats } from "../queries";

export type PanelView = "list" | "chat" | "new";

/**
 * Panel navigation (list ⇄ chat) and asking; one chat is open at a time. A case with exactly
 * one chat opens it on first load; after that the list is only left by the user's own action,
 * so "‹ Chats" stays on the list.
 */
export function useCopilotPanel(caseId: string) {
  const [view, setView] = useState<PanelView>("list");
  const [chatId, setChatId] = useState<string | null>(null);
  const [autoOpenChecked, setAutoOpenChecked] = useState(false);
  const chats = useChats(caseId);

  // Adjusting state during render (not in an effect) avoids a flash of the one-item list.
  if (!autoOpenChecked && chats.data) {
    setAutoOpenChecked(true);
    const only = chats.data.page.total === 1 ? chats.data.items[0] : undefined;
    if (only && view === "list") {
      setChatId(only.id);
      setView("chat");
    }
  }

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
