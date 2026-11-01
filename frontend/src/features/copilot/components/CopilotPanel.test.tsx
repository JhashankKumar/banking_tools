import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test, vi } from "vitest";

import {
  ANSWER_JSON,
  CHAT_JSON,
  CHAT_SUMMARY_JSON,
  DECLINE_JSON,
  page,
} from "@/test/fixtures";
import { apiError, callsOf, jsonResponse, stubFetch } from "@/test/http";
import { renderWithClient } from "@/test/render";

import { CopilotPanel } from "./CopilotPanel";

const CHATS = "/api/cases/FR-10482/chats";
const ASK = "/api/cases/FR-10482/copilot/questions";
const askReply = (answer: object) =>
  jsonResponse({
    data: {
      chat: CHAT_SUMMARY_JSON,
      message: { ...CHAT_JSON.messages[1], answer },
    },
  });

function renderPanel(onSaveAsNote = vi.fn()) {
  return renderWithClient(
    <CopilotPanel caseId="FR-10482" onSaveAsNote={onSaveAsNote} />,
  );
}

const barButton = () => screen.getByTestId("copilot-bar-button");

const SECOND_CHAT = {
  ...CHAT_SUMMARY_JSON,
  id: "c0ffee00-0000-4000-8000-000000000002",
  title: "Second look at TX-1002",
  message_count: 4,
};

describe("CopilotPanel", () => {
  test("a case with exactly one chat opens it by default; ‹ Chats shows the list", async () => {
    stubFetch({
      [`${CHATS}/`]: () => jsonResponse({ data: CHAT_JSON }),
      [CHATS]: () => jsonResponse(page([CHAT_SUMMARY_JSON])),
    });
    renderPanel();
    const user = userEvent.setup();

    expect(
      await screen.findByRole("article", { name: "Copilot answer" }),
    ).toBeVisible();
    expect(barButton()).toHaveTextContent("‹ Chats");

    // Back to the list stays on the list: the auto-open happens once, on first load.
    await user.click(barButton());
    expect(barButton()).toHaveTextContent("+ New chat");
    expect(screen.getByText(/FR-10482 · 1 chat/)).toBeVisible();
    expect(
      screen.getByRole("button", { name: /Where did the money go\?/ }),
    ).toBeVisible();
  });

  test("a case with several chats starts on the list", async () => {
    stubFetch({
      [CHATS]: () => jsonResponse(page([CHAT_SUMMARY_JSON, SECOND_CHAT])),
    });
    renderPanel();

    expect(await screen.findByText("Second look at TX-1002")).toBeVisible();
    expect(screen.getByText("Where did the money go?")).toBeVisible();
    expect(barButton()).toHaveTextContent("+ New chat");
    expect(screen.queryByRole("log", { name: "Conversation" })).toBeNull();
  });

  test("button toggles between New chat and Chats", async () => {
    stubFetch({
      [CHATS]: () => jsonResponse(page([CHAT_SUMMARY_JSON, SECOND_CHAT])),
    });
    renderPanel();
    const user = userEvent.setup();

    expect(await screen.findByText("Where did the money go?")).toBeVisible();
    expect(screen.getByText(/· 2 messages$/)).toBeVisible();
    expect(barButton()).toHaveTextContent("+ New chat");
    expect(screen.getByText(/FR-10482 · 2 chats/)).toBeVisible();

    await user.click(barButton());
    expect(barButton()).toHaveTextContent("‹ Chats");

    await user.click(barButton());
    expect(barButton()).toHaveTextContent("+ New chat");
  });

  test("new chat shows suggestions and asking one posts question with null chat_id", async () => {
    const fetchMock = stubFetch({
      [`${CHATS}/`]: () => jsonResponse({ data: CHAT_JSON }),
      [CHATS]: () => jsonResponse(page([])),
      [ASK]: () => askReply(ANSWER_JSON),
    });
    renderPanel();
    const user = userEvent.setup();

    expect(
      await screen.findByText("No chats yet. Start one with + New chat."),
    ).toBeVisible();
    await user.click(barButton());
    for (const s of [
      "Why did the alert fire?",
      "Where did the money go?",
      "What is not established?",
      "Draft a case note",
    ])
      expect(screen.getByRole("button", { name: s })).toBeVisible();
    await user.click(
      screen.getByRole("button", { name: "Where did the money go?" }),
    );

    await waitFor(() =>
      expect(callsOf(fetchMock).some(([url]) => url === ASK)).toBe(true),
    );
    const [, init] = callsOf(fetchMock).find(([url]) => url === ASK) ?? [];
    expect(JSON.parse(init?.body as string)).toEqual({
      chat_id: null,
      question: "Where did the money go?",
    });
    expect(await screen.findByText("What the records show")).toBeVisible();
    expect(barButton()).toHaveTextContent("‹ Chats");
  });

  test("the only chat opens by default with cited answer sections", async () => {
    stubFetch({
      [`${CHATS}/`]: () => jsonResponse({ data: CHAT_JSON }),
      [CHATS]: () => jsonResponse(page([CHAT_SUMMARY_JSON])),
    });
    renderPanel();

    const answer = await screen.findByRole("article", {
      name: "Copilot answer",
    });
    for (const heading of [
      "What the records show",
      "Calculated",
      "Not established",
      "Next checks",
    ])
      expect(within(answer).getByText(heading)).toBeVisible();
    expect(
      within(answer).getByText("Found money paths (24 h, 3 hops)"),
    ).toBeVisible();
    expect(
      within(answer).getByText("Signal for review; not a finding of fraud."),
    ).toBeVisible();
    expect(
      screen.getByText("Where did the money go?", { selector: "p" }),
    ).toBeVisible();
  });

  test("an opened chat sits scrolled to its newest message, above a pinned ask box", async () => {
    vi.spyOn(HTMLElement.prototype, "scrollHeight", "get").mockReturnValue(800);
    stubFetch({
      [`${CHATS}/`]: () => jsonResponse({ data: CHAT_JSON }),
      [CHATS]: () => jsonResponse(page([CHAT_SUMMARY_JSON])),
    });
    renderPanel();

    await screen.findByRole("article", { name: "Copilot answer" });

    const log = screen.getByRole("log", { name: "Conversation" });
    await waitFor(() => expect(log.scrollTop).toBe(800));
    expect(log).not.toContainElement(
      screen.getByPlaceholderText("Ask a follow-up…"),
    );
    vi.restoreAllMocks();
  });

  test("a new answer scrolls the conversation to the bottom", async () => {
    stubFetch({
      [`${CHATS}/`]: () => jsonResponse({ data: CHAT_JSON }),
      [CHATS]: () => jsonResponse(page([])),
      [ASK]: () => askReply(ANSWER_JSON),
    });
    renderPanel();
    const user = userEvent.setup();

    await user.click(barButton());
    const log = screen.getByRole("log", { name: "Conversation" });
    log.scrollTop = 0;
    vi.spyOn(HTMLElement.prototype, "scrollHeight", "get").mockReturnValue(
      1200,
    );
    await user.click(
      screen.getByRole("button", { name: "Why did the alert fire?" }),
    );
    await screen.findByRole("article", { name: "Copilot answer" });

    await waitFor(() => expect(log.scrollTop).toBe(1200));
    vi.restoreAllMocks();
  });

  test("save as case note passes the answer and message id", async () => {
    stubFetch({
      [`${CHATS}/`]: () => jsonResponse({ data: CHAT_JSON }),
      [CHATS]: () => jsonResponse(page([CHAT_SUMMARY_JSON])),
    });
    const onSave = vi.fn();
    renderPanel(onSave);
    const user = userEvent.setup();

    await user.click(
      await screen.findByRole("button", { name: "Save as case note" }),
    );

    expect(onSave).toHaveBeenCalledWith(
      CHAT_JSON.messages[1].id,
      expect.objectContaining({
        kind: "answer",
        notEstablished: ["Ownership of ACC-C."],
      }),
    );
  });

  test("decline shows customer-details card and no Save as case note", async () => {
    stubFetch({
      [`${CHATS}/`]: () =>
        jsonResponse({
          data: {
            ...CHAT_JSON,
            messages: [
              {
                ...CHAT_JSON.messages[0],
                question: "What is the customer's phone?",
              },
              { ...CHAT_JSON.messages[1], answer: DECLINE_JSON },
            ],
          },
        }),
      [CHATS]: () => jsonResponse(page([CHAT_SUMMARY_JSON])),
    });
    renderPanel();

    expect(
      await screen.findByText("I can't help with customer details."),
    ).toBeVisible();
    expect(
      screen.getByText(/I only analyse the fraud signal on this case/),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Trace where the funds went" }),
    ).toBeVisible();
    expect(
      screen.queryByRole("button", { name: "Save as case note" }),
    ).toBeNull();
  });

  test("supervisor reading others chat sees read-only note and no input", async () => {
    const others = {
      ...CHAT_JSON,
      is_own: false,
      author_username: "analyst.demo",
    };
    stubFetch({
      [`${CHATS}/`]: () => jsonResponse({ data: others }),
      [CHATS]: () =>
        jsonResponse(page([{ ...CHAT_SUMMARY_JSON, is_own: false }])),
    });
    renderPanel();

    expect(
      await screen.findByText("Read-only: analyst.demo's chat."),
    ).toBeVisible();
    expect(
      screen.queryByRole("textbox", { name: "Ask the copilot" }),
    ).toBeNull();
    expect(
      screen.queryByRole("button", { name: "Save as case note" }),
    ).toBeNull();
  });

  test("limit error shows retry time", async () => {
    stubFetch({
      [CHATS]: () => jsonResponse(page([])),
      [ASK]: () => {
        const response = apiError("COPILOT_LIMIT_REACHED", 429, {
          message: "You've reached the limit of 20 copilot questions per hour.",
        });
        response.headers.set("Retry-After", "600");
        return response;
      },
    });
    renderPanel();
    const user = userEvent.setup();
    await screen.findByText("No chats yet. Start one with + New chat.");
    await user.click(barButton());

    await user.type(
      screen.getByRole("textbox", { name: "Ask the copilot" }),
      "Why?{Enter}",
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "You've reached the limit of 20 copilot questions per hour.",
    );
    expect(screen.getByText("Try again in 10 min.")).toBeVisible();
  });

  test("after a 503 the kept chat opens and a retry asks in it", async () => {
    let asked = 0;
    const fetchMock = stubFetch({
      [`${CHATS}/`]: () =>
        jsonResponse({
          data: { ...CHAT_JSON, messages: CHAT_JSON.messages.slice(0, 1) },
        }),
      [CHATS]: () => jsonResponse(page([])),
      [ASK]: () =>
        asked++ === 0
          ? apiError("COPILOT_UNAVAILABLE", 503, {
              message: "The copilot is unavailable right now.",
              details: [{ field: "chat_id", message: CHAT_JSON.id }],
            })
          : askReply(ANSWER_JSON),
    });
    renderPanel();
    const user = userEvent.setup();
    await screen.findByText("No chats yet. Start one with + New chat.");
    await user.click(barButton());
    const ask = (q: string) =>
      user.type(
        screen.getByRole("textbox", { name: "Ask the copilot" }),
        `${q}{Enter}`,
      );

    await ask("Where did the money go?");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The copilot is unavailable right now.",
    );
    expect(
      await screen.findByRole("textbox", { name: "Ask the copilot" }),
    ).toHaveAttribute("placeholder", "Ask a follow-up…");
    await ask("Where did the money go?");
    await waitFor(() => expect(asked).toBe(2));
    const bodies = callsOf(fetchMock)
      .filter(([url]) => url === ASK)
      .map(
        ([, init]) => JSON.parse(String(init?.body)) as { chat_id: unknown },
      );
    expect(bodies.map((b) => b.chat_id)).toEqual([null, CHAT_JSON.id]);
  });
});
