import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test } from "vitest";

import { NOTE_JSON, STATUS_CHANGE_JSON, page } from "@/test/fixtures";
import { callsOf, jsonResponse, stubFetch } from "@/test/http";
import { renderWithClient } from "@/test/render";

import { CaseNotesCard } from "./CaseNotesCard";

const NOTES = "/api/cases/FR-10482/notes";

describe("CaseNotesCard", () => {
  test("lists notes with status, provenance and citations", async () => {
    stubFetch({
      [NOTES]: () => jsonResponse(page([NOTE_JSON])),
      "/api/cases/FR-10482/status-changes": () => jsonResponse(page([])),
    });
    renderWithClient(<CaseNotesCard caseId="FR-10482" />);

    const card = await screen.findByRole("region", { name: "Case notes" });
    expect(await within(card).findByText("Draft")).toBeVisible();
    expect(
      within(card).getByText("AI-drafted, edited by analyst.demo"),
    ).toBeVisible();
    expect(
      within(card).getByRole("button", { name: /EV-10482-TX-1001/ }),
    ).toBeVisible();
  });

  test("a TX- ID already covered by its evidence chip gets no extra record chip", async () => {
    stubFetch({
      [NOTES]: () =>
        jsonResponse(
          page([
            {
              ...NOTE_JSON,
              cited_ids: ["TX-1001", "EV-10482-TX-1001", "TX-9001"],
            },
          ]),
        ),
      "/api/cases/FR-10482/status-changes": () => jsonResponse(page([])),
    });
    renderWithClient(<CaseNotesCard caseId="FR-10482" />);

    const card = await screen.findByRole("region", { name: "Case notes" });
    await within(card).findByRole("button", { name: /EV-10482-TX-1001/ });
    expect(within(card).queryByRole("button", { name: /^TX-1001/ })).toBeNull();
    expect(
      within(card).getByRole("button", {
        name: "TX-9001, record outside the case",
      }),
    ).toBeVisible();
  });

  test("submit for review refreshes case status", async () => {
    const fetchMock = stubFetch({
      [`${NOTES}/`]: () =>
        jsonResponse({
          data: { ...NOTE_JSON, status: "awaiting_review", can_edit: false },
        }),
      [NOTES]: () => jsonResponse(page([NOTE_JSON])),
      "/api/cases/FR-10482/status-changes": () => jsonResponse(page([])),
      "/api/cases/FR-10482": () => jsonResponse({ data: {} }),
    });
    renderWithClient(<CaseNotesCard caseId="FR-10482" />);

    await userEvent
      .setup()
      .click(await screen.findByRole("button", { name: "Submit for review" }));

    await waitFor(() =>
      expect(
        callsOf(fetchMock).some(
          ([url, init]) =>
            url === `${NOTES}/${NOTE_JSON.id}/submit` && init.method === "POST",
        ),
      ).toBe(true),
    );
    // The mutation invalidates the case detail query, so the header status chip refreshes.
    await waitFor(() =>
      expect(
        callsOf(fetchMock).filter(([url]) => url === NOTES).length,
      ).toBeGreaterThan(1),
    );
  });

  test("status history lists transitions with actor and reason", async () => {
    stubFetch({
      [NOTES]: () => jsonResponse(page([])),
      "/api/cases/FR-10482/status-changes": () =>
        jsonResponse(page([STATUS_CHANGE_JSON])),
    });
    renderWithClient(<CaseNotesCard caseId="FR-10482" />);
    const user = userEvent.setup();

    await user.click(
      await screen.findByRole("button", { name: /Status history/ }),
    );

    expect(
      screen.getByText(
        "Open → In review · analyst.demo · note submitted · 24 Oct 2026, 11:42:00 IST",
      ),
    ).toBeVisible();
  });

  test("no notes yet", async () => {
    stubFetch({
      [NOTES]: () => jsonResponse(page([])),
      "/api/cases/FR-10482/status-changes": () => jsonResponse(page([])),
    });
    renderWithClient(<CaseNotesCard caseId="FR-10482" />);

    expect(
      await screen.findByText(
        "No notes yet. Save a copilot answer as a case note to start one.",
      ),
    ).toBeVisible();
  });
});
