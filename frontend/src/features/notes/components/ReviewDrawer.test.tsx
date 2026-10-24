import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test, vi } from "vitest";

import { NOTE_JSON } from "@/test/fixtures";
import { apiError, callsOf, jsonResponse, stubFetch } from "@/test/http";
import { renderWithClient } from "@/test/render";

import { noteSchema } from "../schemas";
import { CloseCaseDrawer } from "./CloseCaseDrawer";
import { ReviewDrawer } from "./ReviewDrawer";

const note = noteSchema.parse({
  ...NOTE_JSON,
  status: "awaiting_review",
  can_review: true,
});

function renderReview(onClose = vi.fn()) {
  return renderWithClient(
    <ReviewDrawer caseId="FR-10482" note={note} onClose={onClose} />,
  );
}

describe("ReviewDrawer", () => {
  test("return requires comment", async () => {
    const fetchMock = stubFetch(jsonResponse({ data: NOTE_JSON }));
    renderReview();
    const user = userEvent.setup();

    await user.click(screen.getByRole("radio", { name: "Return" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    expect(
      await screen.findByText("Add a comment for the author."),
    ).toBeVisible();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  test("close requires listed reason and comment", async () => {
    const fetchMock = stubFetch(jsonResponse({ data: NOTE_JSON }));
    const onClose = vi.fn();
    renderReview(onClose);
    const user = userEvent.setup();

    await user.click(screen.getByRole("radio", { name: "Close" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    expect(await screen.findByText("Choose a closing reason.")).toBeVisible();

    await user.selectOptions(
      screen.getByLabelText("Closing reason"),
      "No further action",
    );
    await user.type(screen.getByLabelText("Comment"), "Benign after review.");
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const [[url, init]] = callsOf(fetchMock);
    expect(url).toBe(`/api/cases/FR-10482/notes/${NOTE_JSON.id}/review`);
    expect(JSON.parse(init.body as string)).toEqual({
      decision: "approve_close",
      reason: "No further action",
      comment: "Benign after review.",
    });
  });

  test("self review error shown in banner", async () => {
    stubFetch(
      apiError("NOTE_SELF_REVIEW", 409, {
        message:
          "You can't review your own note. Another supervisor must review it.",
      }),
    );
    renderReview();
    const user = userEvent.setup();

    await user.click(screen.getByRole("radio", { name: "Keep open" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "You can't review your own note.",
    );
  });
});

describe("CloseCaseDrawer", () => {
  test("posts the closing reason and comment", async () => {
    const fetchMock = stubFetch(jsonResponse({ data: [] }));
    const onClose = vi.fn();
    renderWithClient(<CloseCaseDrawer caseId="FR-10482" onClose={onClose} />);
    const user = userEvent.setup();

    await user.selectOptions(
      screen.getByLabelText("Closing reason"),
      "Referred externally",
    );
    await user.type(screen.getByLabelText("Comment"), "Handed over.");
    await user.click(screen.getByRole("button", { name: "Close case" }));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const [[url, init]] = callsOf(fetchMock);
    expect(url).toBe("/api/cases/FR-10482/close");
    expect(JSON.parse(init.body as string)).toEqual({
      reason: "Referred externally",
      comment: "Handed over.",
    });
  });
});
