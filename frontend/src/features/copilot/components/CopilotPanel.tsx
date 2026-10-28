"use client";

import { Sparkles } from "lucide-react";

import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { QueryView } from "@/components/ui/QueryView";

import { useCopilotPanel } from "../hooks/useCopilotPanel";
import type { CopilotAnswer } from "../schemas";
import { AnswerView } from "./AnswerView";
import { AskBox } from "./AskBox";
import { ChatList } from "./ChatList";
import { DeclineCard } from "./DeclineCard";

export const SUGGESTED_QUESTIONS = [
  "Why did the alert fire?",
  "Where did the money go?",
  "What is not established?",
  "Draft a case note",
];

const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;

/**
 * Case-scoped copilot. One top-right button: "+ New chat" on the list of chats, "‹ Chats"
 * inside a chat (back to the list).
 */
export function CopilotPanel({
  caseId,
  onSaveAsNote,
  onSelectTransaction,
}: {
  caseId: string;
  onSaveAsNote?: (messageId: string, answer: CopilotAnswer) => void;
  onSelectTransaction?: (transactionId: string) => void;
}) {
  const p = useCopilotPanel(caseId);
  const chatCount = p.chats.data?.page.total ?? 0;
  const title =
    p.view === "list"
      ? null
      : p.view === "new"
        ? "New chat"
        : (p.chat.data?.title ?? "Chat");

  return (
    <section
      aria-label="AI copilot"
      className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-4 shadow-sm"
    >
      <header className="flex items-center gap-2">
        <Sparkles aria-hidden size={16} className="shrink-0 text-primary" />
        <h2 className="min-w-0 truncate text-sm font-semibold text-ink">
          {title ?? (
            <>
              AI copilot{" "}
              <span className="text-[11px] font-normal text-muted">
                · {caseId} · {plural(chatCount, "chat")}
              </span>
            </>
          )}
        </h2>
        <button
          type="button"
          data-testid="copilot-bar-button"
          onClick={p.view === "list" ? p.newChat : p.backToList}
          className={
            p.view === "list"
              ? "ml-auto shrink-0 rounded-lg border border-primary bg-primary px-2.5 py-1 text-xs font-semibold text-on-primary"
              : "ml-auto shrink-0 rounded-lg border border-primary bg-surface px-2.5 py-1 text-xs font-semibold text-primary"
          }
        >
          {p.view === "list" ? "+ New chat" : "‹ Chats"}
        </button>
      </header>

      {p.view === "list" && (
        <QueryView query={p.chats} noun="Chats" loading="Loading chats">
          {(data) => <ChatList chats={data.items} onOpen={p.openChat} />}
        </QueryView>
      )}

      {p.view === "new" && (
        <div className="flex flex-col gap-2">
          <p className="text-xs text-muted">
            Ask about {caseId}. I analyse the fraud signal only and cite
            evidence IDs.
          </p>
          <div className="flex flex-wrap gap-1.5">
            {SUGGESTED_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                disabled={p.pending}
                onClick={() => p.ask(q)}
                className="rounded-full border border-primary px-2 py-0.5 text-[11px] text-primary disabled:opacity-60"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {p.view === "chat" && (
        <QueryView query={p.chat} noun="Chat" loading="Loading chat">
          {(chat) => (
            <div className="flex flex-col gap-2.5">
              {chat.messages.map((m) =>
                m.role === "user" ? (
                  <p
                    key={m.id}
                    className="max-w-[85%] self-end rounded-xl rounded-br-sm bg-primary px-2.5 py-1.5 text-xs text-on-primary"
                  >
                    {m.question}
                  </p>
                ) : m.answer?.kind === "decline" ? (
                  <DeclineCard
                    key={m.id}
                    answer={m.answer}
                    onAsk={chat.isOwn ? p.ask : undefined}
                  />
                ) : (
                  m.answer && (
                    <AnswerView
                      key={m.id}
                      answer={m.answer}
                      onSelectTransaction={onSelectTransaction}
                      onSave={
                        chat.isOwn && onSaveAsNote && m.answer
                          ? () => onSaveAsNote(m.id, m.answer as CopilotAnswer)
                          : undefined
                      }
                    />
                  )
                ),
              )}
              {!chat.isOwn && (
                <p className="rounded-lg bg-raised px-2.5 py-1.5 text-[11px] text-muted">
                  Read-only: {chat.authorUsername}&apos;s chat.
                </p>
              )}
            </div>
          )}
        </QueryView>
      )}

      {p.pending && (
        <p role="status" className="text-[11px] text-muted">
          Checking the case records…
        </p>
      )}
      {p.error && (
        <div className="flex flex-col gap-1">
          <ErrorBanner error={p.error} />
          {p.error.retryAfter !== null && (
            <p className="text-[11px] text-muted">
              Try again in {Math.max(1, Math.ceil(p.error.retryAfter / 60))}{" "}
              min.
            </p>
          )}
        </div>
      )}

      {(p.view === "new" || (p.view === "chat" && p.chat.data?.isOwn)) && (
        <AskBox
          placeholder={
            p.view === "new" ? `Ask about ${caseId}…` : "Ask a follow-up…"
          }
          disabled={p.pending}
          onAsk={p.ask}
        />
      )}
    </section>
  );
}
