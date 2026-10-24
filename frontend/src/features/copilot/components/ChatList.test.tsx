import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { CHAT_SUMMARY_JSON } from "@/test/fixtures";

import { chatSummarySchema } from "../schemas";
import { ChatList } from "./ChatList";

test("one message is singular", () => {
  render(
    <ChatList
      chats={[
        chatSummarySchema.parse({ ...CHAT_SUMMARY_JSON, message_count: 1 }),
      ]}
      onOpen={vi.fn()}
    />,
  );

  expect(screen.getByText(/· 1 message$/)).toBeVisible();
});
