import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test, vi } from "vitest";

import {
  CHAT_SUMMARY_JSON,
  LIMITED_TO_DATASET,
  MONEY_PATHS_JSON,
  caseRoutes,
  page,
} from "@/test/fixtures";
import { apiError, callsOf, jsonResponse, stubFetch } from "@/test/http";
import { renderWithClient } from "@/test/render";

import { CasePage } from "./CasePage";

vi.mock("reagraph", () => import("@/test/reagraph-mock"));
vi.mock("next/navigation", () => import("@/test/next-navigation"));

const PATH_LIMITATION =
  "Includes a reversal record; the original transfer and its reversal are shown separately, not netted.";

function stubCase(overrides: Record<string, () => Response> = {}) {
  const paths = {
    ...MONEY_PATHS_JSON,
    paths: [
      {
        ...MONEY_PATHS_JSON.paths[0],
        limitations: [LIMITED_TO_DATASET, PATH_LIMITATION],
      },
    ],
  };
  return stubFetch(
    caseRoutes({
      "/api/cases/FR-10482/money-paths": () => jsonResponse({ data: paths }),
      ...overrides,
    }),
  );
}

describe("CasePage", () => {
  test("renders why it fired with metric tiles", async () => {
    stubCase();
    renderWithClient(<CasePage caseId="FR-10482" />);

    const why = await screen.findByRole("region", { name: "Why it fired" });
    expect(within(why).getByText("5 m 28 s")).toBeInTheDocument();
    expect(within(why).getByText("30 m")).toBeInTheDocument();
    expect(within(why).getByText("₹48,500.00")).toBeInTheDocument();
    expect(within(why).getByText("₹45,000.00")).toBeInTheDocument();
    expect(within(why).getByText(/not a finding of fraud/)).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 1, name: /FR-10482/ }),
    ).toBeInTheDocument();
  });

  test("rule caveats disclosure lists caveats", async () => {
    stubCase();
    renderWithClient(<CasePage caseId="FR-10482" />);

    await userEvent
      .setup()
      .click(await screen.findByRole("button", { name: /rule caveats/i }));

    expect(
      screen.getByText(/routinely pass funds through/),
    ).toBeInTheDocument();
  });

  test("timeline rows show IST times and right-aligned amounts", async () => {
    stubCase();
    renderWithClient(<CasePage caseId="FR-10482" />);

    const row = await screen.findByRole("row", { name: /TX-1001/ });
    expect(row).toHaveTextContent("ACC-001 → BEN-B");
    expect(row).toHaveTextContent("10:02:14");
    expect(within(row).getByText("₹48,500.00")).toHaveClass("text-right");
    expect(row).toHaveTextContent("settled");
  });

  test("clicking a timeline row marks it selected", async () => {
    stubCase();
    renderWithClient(<CasePage caseId="FR-10482" />);

    const row = await screen.findByRole("row", { name: /TX-1002/ });
    await userEvent.setup().click(row);

    expect(row).toHaveAttribute("aria-selected", "true");
  });

  test("evidence chip selects its transaction", async () => {
    stubCase();
    renderWithClient(<CasePage caseId="FR-10482" />);

    const evidence = await screen.findByRole("region", { name: "Evidence" });
    await userEvent.setup().click(
      await within(evidence).findByRole("button", {
        name: /EV-10482-TX-1001/,
      }),
    );

    expect(await screen.findByRole("row", { name: /TX-1001/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(
      within(evidence).getByText("EV-10482-AL-ROT-TX-1002"),
    ).toBeInTheDocument();
  });

  test("limitations show selected path limitations", async () => {
    stubCase();
    renderWithClient(<CasePage caseId="FR-10482" />);

    const limitations = await screen.findByRole("region", {
      name: "Limitations",
    });
    await waitFor(() => expect(limitations).toHaveTextContent(PATH_LIMITATION));
  });

  test("shows case not found", async () => {
    stubCase({
      "/api/cases/FR-10482": () =>
        apiError("CASE_NOT_FOUND", 404, { message: "Case not found" }),
    });
    renderWithClient(<CasePage caseId="FR-10482" />);

    expect(
      await screen.findByRole("heading", { name: "Case not found" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /back to cases/i }),
    ).toHaveAttribute("href", "/cases");
  });

  test("auditor sees permission denied on case page", async () => {
    const fetchMock = stubCase({
      "/api/cases/FR-10482": () =>
        apiError("AUTH_FORBIDDEN", 403, { message: "Forbidden" }),
    });
    renderWithClient(<CasePage caseId="FR-10482" />);

    expect(
      await screen.findByRole("heading", {
        name: "You don't have access to this page",
      }),
    ).toBeInTheDocument();
    // Every extra call would be audited as another denied event.
    // /api/auth/me (the viewer's role) is not case data and is cached app-wide in practice.
    expect(
      callsOf(fetchMock)
        .map(([url]) => url)
        .filter((url) => url !== "/api/auth/me"),
    ).toEqual(["/api/cases/FR-10482"]);
  });

  test("collapsing left column leaves an accessible rail button", async () => {
    stubCase();
    renderWithClient(<CasePage caseId="FR-10482" />);
    const user = userEvent.setup();

    await user.click(
      await screen.findByRole("button", { name: "Collapse case context" }),
    );

    expect(
      screen.queryByRole("region", { name: "Why it fired" }),
    ).not.toBeInTheDocument();
    await user.click(
      screen.getByRole("button", { name: "Expand case context" }),
    );
    expect(
      screen.getByRole("region", { name: "Why it fired" }),
    ).toBeInTheDocument();
  });

  test("copilot panel lists the case's chats", async () => {
    // Two chats: a case with exactly one opens it directly (see CopilotPanel tests).
    const second = {
      ...CHAT_SUMMARY_JSON,
      id: "c0ffee00-0000-4000-8000-000000000002",
      title: "Second look at TX-1002",
    };
    stubCase({
      "/api/cases/FR-10482/chats": () =>
        jsonResponse(page([CHAT_SUMMARY_JSON, second])),
    });
    renderWithClient(<CasePage caseId="FR-10482" />);

    const copilot = await screen.findByRole("region", { name: "AI copilot" });
    expect(
      await within(copilot).findByText("Where did the money go?"),
    ).toBeVisible();
    expect(within(copilot).getByText("Second look at TX-1002")).toBeVisible();
    expect(within(copilot).getByText(/FR-10482 · 2 chats/)).toBeVisible();
  });
});
