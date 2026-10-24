import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test, vi } from "vitest";

import { copilotAnswerSchema } from "@/features/copilot/schemas";
import { ANSWER_JSON, NOTE_JSON } from "@/test/fixtures";
import { apiError, callsOf, jsonResponse, stubFetch } from "@/test/http";
import { renderWithClient } from "@/test/render";

import { NoteEditorDrawer } from "./NoteEditorDrawer";

const answer = copilotAnswerSchema.parse(ANSWER_JSON);
const SOURCE = "c0ffee00-0000-4000-8000-0000000000a2";

describe("NoteEditorDrawer", () => {
  test("save as note prefills body from answer and posts source_message_id", async () => {
    const fetchMock = stubFetch(jsonResponse({ data: NOTE_JSON }, 201));
    const onClose = vi.fn();
    renderWithClient(
      <NoteEditorDrawer
        caseId="FR-10482"
        target={{ kind: "draft", sourceMessageId: SOURCE, answer }}
        onClose={onClose}
      />,
    );
    const body = screen.getByLabelText("Note");

    expect(
      screen.getByText("AI-drafted · you can edit before saving"),
    ).toBeVisible();
    expect((body as HTMLTextAreaElement).value).toContain(
      "What the records show\n- TX-1001 moved ₹48,500.00 from ACC-001 to BEN-B. [EV-10482-TX-1001]",
    );
    expect((body as HTMLTextAreaElement).value).toContain(
      "Not established\n- Ownership of ACC-C.",
    );
    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: "Save note" }));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const [[url, init]] = callsOf(fetchMock);
    expect(url).toBe("/api/cases/FR-10482/notes");
    expect(JSON.parse(init.body as string)).toMatchObject({
      source_message_id: SOURCE,
    });
  });

  test("citation error maps to body field", async () => {
    stubFetch(
      apiError("NOTE_CITATION_INVALID", 422, {
        message: "The note cites records that are not part of this case.",
        details: [
          { field: "body", message: "Unknown citation EV-10483-TX-3001" },
        ],
      }),
    );
    renderWithClient(
      <NoteEditorDrawer
        caseId="FR-10482"
        target={{ kind: "draft", sourceMessageId: SOURCE, answer }}
        onClose={vi.fn()}
      />,
    );

    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: "Save note" }));

    expect(
      await screen.findByText("Unknown citation EV-10483-TX-3001"),
    ).toBeVisible();
    expect(screen.getByLabelText("Note")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
  });

  test("editing an existing note patches it", async () => {
    const fetchMock = stubFetch(jsonResponse({ data: NOTE_JSON }));
    renderWithClient(
      <NoteEditorDrawer
        caseId="FR-10482"
        target={{ kind: "edit", noteId: NOTE_JSON.id, body: NOTE_JSON.body }}
        onClose={vi.fn()}
      />,
    );
    const user = userEvent.setup();

    await user.type(screen.getByLabelText("Note"), " More.");
    await user.click(screen.getByRole("button", { name: "Save note" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [[url, init]] = callsOf(fetchMock);
    expect(url).toBe(`/api/cases/FR-10482/notes/${NOTE_JSON.id}`);
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(init.body as string)).toEqual({
      body: `${NOTE_JSON.body} More.`,
    });
  });
});
