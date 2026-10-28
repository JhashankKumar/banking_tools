import { formatDateTime } from "@/lib/format";

import type { ChatSummary } from "../schemas";

export function ChatList({
  chats,
  onOpen,
}: {
  chats: ChatSummary[];
  onOpen: (id: string) => void;
}) {
  if (chats.length === 0) {
    return (
      <p className="rounded-lg bg-raised p-3 text-xs text-muted">
        No chats yet. Start one with + New chat.
      </p>
    );
  }
  return (
    <ul className="flex flex-col gap-2">
      {chats.map((c) => (
        <li key={c.id}>
          <button
            type="button"
            onClick={() => onOpen(c.id)}
            className="flex w-full flex-col gap-0.5 rounded-lg border border-line px-3 py-2 text-left hover:border-primary hover:bg-raised"
          >
            <span className="text-xs font-semibold text-ink">
              {c.title}
              {!c.isOwn && (
                <span className="font-normal text-muted">
                  {" "}
                  · {c.authorUsername}
                </span>
              )}
            </span>
            <span className="text-[11px] text-muted">
              {formatDateTime(c.updatedAt)} · {c.messageCount}{" "}
              {c.messageCount === 1 ? "message" : "messages"}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}
