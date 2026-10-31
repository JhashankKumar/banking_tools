import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test } from "vitest";

import { SAFETY_CHECKS_JSON, SAFETY_RUN_JSON } from "@/test/fixtures";
import { apiError, jsonResponse, stubFetch } from "@/test/http";
import { renderWithClient } from "@/test/render";

import { SafetyChecksView } from "./SafetyChecksView";

const CHECKS = "/api/safety/checks";
const RUNS = "/api/safety/runs";
const runButton = () => screen.getByRole("button", { name: "Run checks" });

describe("SafetyChecksView", () => {
  test("catalogue renders grouped by category with Not run yet", async () => {
    stubFetch({ [CHECKS]: () => jsonResponse({ data: SAFETY_CHECKS_JSON }) });
    renderWithClient(<SafetyChecksView />);

    const groups = await screen.findAllByRole("heading", { level: 2 });
    expect(groups.map((g) => g.textContent)).toEqual([
      "Prompt injection",
      "Access control",
    ]);
    expect(screen.getAllByText("Not run yet")).toHaveLength(3);
    expect(screen.queryByText("Passed")).toBeNull();
  });

  test("run shows tiles and results", async () => {
    stubFetch({
      [CHECKS]: () => jsonResponse({ data: SAFETY_CHECKS_JSON }),
      [RUNS]: () => jsonResponse({ data: SAFETY_RUN_JSON }),
    });
    renderWithClient(<SafetyChecksView />);
    const user = userEvent.setup();
    await screen.findAllByText("Not run yet");

    await user.click(runButton());

    const tiles = await screen.findByRole("group", { name: "Run summary" });
    for (const label of ["Passed", "Failed", "Skipped", "Duration"])
      expect(within(tiles).getByText(label)).toBeVisible();
    expect(within(tiles).getByText("4.2 s")).toBeVisible();
    const row = screen.getByRole("row", { name: /INJ-02/ });
    expect(row).toHaveTextContent("The model asks a tool for another case.");
    expect(row).toHaveTextContent("Tools are bound to the run's case.");
    expect(row).toHaveTextContent("The tool accepted another case's ID.");
    expect(within(row).getByText("Failed")).toBeVisible();
    expect(screen.queryByText("Not run yet")).toBeNull();
  });

  test("failed checks sort first within their group", async () => {
    stubFetch({
      [CHECKS]: () => jsonResponse({ data: SAFETY_CHECKS_JSON }),
      [RUNS]: () => jsonResponse({ data: SAFETY_RUN_JSON }),
    });
    renderWithClient(<SafetyChecksView />);
    const user = userEvent.setup();
    await screen.findAllByText("Not run yet");

    await user.click(runButton());

    const section = await screen.findByRole("region", {
      name: "Prompt injection",
    });
    const ids = within(section)
      .getAllByRole("row")
      .slice(1)
      .map((r) => r.getAttribute("aria-label"));
    expect(ids).toEqual(["INJ-02", "INJ-01"]);
  });

  test("409 shows that a run is already in progress", async () => {
    stubFetch({
      [CHECKS]: () => jsonResponse({ data: SAFETY_CHECKS_JSON }),
      [RUNS]: () =>
        apiError("SAFETY_RUN_IN_PROGRESS", 409, {
          message: "A safety run is already in progress.",
        }),
    });
    renderWithClient(<SafetyChecksView />);
    const user = userEvent.setup();
    await screen.findAllByText("Not run yet");

    await user.click(runButton());

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "A run is already in progress.",
    );
  });

  test("button disabled while running", async () => {
    let release: (r: Response) => void = () => undefined;
    stubFetch({
      [CHECKS]: () => jsonResponse({ data: SAFETY_CHECKS_JSON }),
      // Held open until the test releases it; stubFetch awaits whatever the handler returns.
      [RUNS]: () =>
        new Promise<Response>((resolve) => {
          release = resolve;
        }) as unknown as Response,
    });
    renderWithClient(<SafetyChecksView />);
    const user = userEvent.setup();
    await screen.findAllByText("Not run yet");

    await user.click(runButton());

    expect(runButton()).toBeDisabled();
    expect(screen.getByRole("status")).toHaveTextContent("Running the checks…");
    release(jsonResponse({ data: SAFETY_RUN_JSON }));
    await waitFor(() => expect(runButton()).toBeEnabled());
  });

  test("no Run button when the role has no access", async () => {
    stubFetch({ [CHECKS]: () => apiError("AUTH_FORBIDDEN", 403) });
    renderWithClient(<SafetyChecksView />);

    expect(
      await screen.findByText("You don't have access to this page"),
    ).toBeVisible();
    expect(screen.queryByRole("button", { name: "Run checks" })).toBeNull();
  });
});
