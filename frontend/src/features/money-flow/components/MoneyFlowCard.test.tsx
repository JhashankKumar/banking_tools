import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test, vi } from "vitest";

import { CasePage } from "@/features/cases/components/CasePage";
import { GRAPH_JSON, caseRoutes } from "@/test/fixtures";
import { callsOf, jsonResponse, stubFetch, type FetchMock } from "@/test/http";
import { renderWithClient } from "@/test/render";

vi.mock("reagraph", () => import("@/test/reagraph-mock"));
vi.mock("next/navigation", () => import("@/test/next-navigation"));

const OUT_EDGE = {
  ...GRAPH_JSON.edges[1],
  transaction_id: "TX-OUT",
  source: { type: "account", id: "ACC-C" },
  destination: { type: "account", id: "ACC-OUT" },
  evidence_id: null,
  in_case: false,
};

const stub = () =>
  stubFetch(
    caseRoutes({
      "/api/cases/FR-10482/graph": () =>
        jsonResponse({
          data: {
            ...GRAPH_JSON,
            nodes: [
              ...GRAPH_JSON.nodes,
              {
                id: "ACC-OUT",
                type: "account",
                label: "ACC-OUT",
                status: "active",
                is_case_party: false,
                alert_ids: [],
              },
            ],
            edges: [...GRAPH_JSON.edges, OUT_EDGE],
          },
        }),
    }),
  );

const urls = (m: FetchMock) => callsOf(m).map(([url]) => url);
const canvas = () => screen.findByTestId("reagraph");

describe("MoneyFlowCard", () => {
  test("first path is pre-selected", async () => {
    stub();
    renderWithClient(<CasePage caseId="FR-10482" />);

    await waitFor(async () =>
      expect((await canvas()).dataset.actives).toContain("TX-1001"),
    );
    expect(
      screen.getByRole("button", { name: /Path 1 · 2 hops · 5 m 28 s/ }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  test("selecting All transactions clears path and actives", async () => {
    stub();
    renderWithClient(<CasePage caseId="FR-10482" />);
    await waitFor(async () =>
      expect((await canvas()).dataset.actives).toContain("TX-1001"),
    );

    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: "All transactions" }));

    expect((await canvas()).dataset.actives).toBe("");
  });

  test("window picker refetches graph and money paths with window_hours", async () => {
    const fetchMock = stub();
    renderWithClient(<CasePage caseId="FR-10482" />);
    await canvas();

    await userEvent
      .setup()
      .selectOptions(screen.getByLabelText("Time window"), "48");

    await waitFor(() => {
      expect(urls(fetchMock)).toContain(
        "/api/cases/FR-10482/graph?window_hours=48",
      );
      expect(urls(fetchMock)).toContain(
        "/api/cases/FR-10482/money-paths?max_hops=3&window_hours=48",
      );
    });
  });

  test("hops picker refetches only money paths", async () => {
    const fetchMock = stub();
    renderWithClient(<CasePage caseId="FR-10482" />);
    await canvas();
    const graphCalls = urls(fetchMock).filter((u) =>
      u.includes("/graph"),
    ).length;

    await userEvent
      .setup()
      .selectOptions(screen.getByLabelText("Max hops"), "5");

    await waitFor(() =>
      expect(urls(fetchMock)).toContain(
        "/api/cases/FR-10482/money-paths?max_hops=5&window_hours=24",
      ),
    );
    expect(urls(fetchMock).filter((u) => u.includes("/graph")).length).toBe(
      graphCalls,
    );
  });

  test("3D view switches layout to forceDirected3d and collapses side columns", async () => {
    stub();
    renderWithClient(<CasePage caseId="FR-10482" />);
    expect((await canvas()).dataset.layout).toBe("custom");
    const user = userEvent.setup();

    await user.click(screen.getByRole("radio", { name: "3D view" }));

    await waitFor(async () =>
      expect((await canvas()).dataset.layout).toBe("forceDirected3d"),
    );
    expect((await canvas()).dataset.camera).toBe("rotate");
    expect(
      screen.queryByRole("region", { name: "Why it fired" }),
    ).not.toBeInTheDocument();
    expect(screen.getByText(/Drag to orbit/)).toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: "3D look" }));
    expect(
      await screen.findByRole("region", { name: "Why it fired" }),
    ).toBeInTheDocument();
  });

  test("clicking an edge opens detail card and selects timeline row", async () => {
    stub();
    renderWithClient(<CasePage caseId="FR-10482" />);

    await userEvent
      .setup()
      .click(await screen.findByRole("button", { name: "edge TX-1002" }));

    const card = await screen.findByRole("region", {
      name: "Transaction TX-1002",
    });
    expect(card).toHaveTextContent("BEN-B → ACC-C");
    expect(card).toHaveTextContent("₹45,000.00");
    expect(card).toHaveTextContent("15 Sep 2026, 10:07:42 IST");
    expect(card).toHaveTextContent("IMPS · SYN-REF-1002");
    expect(card).toHaveTextContent("EV-10482-TX-1002");
    expect(screen.getByRole("row", { name: /TX-1002/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
  });

  test("out-of-case edge disables Show in timeline", async () => {
    stub();
    renderWithClient(<CasePage caseId="FR-10482" />);

    await userEvent
      .setup()
      .click(await screen.findByRole("button", { name: "edge TX-OUT" }));

    const card = await screen.findByRole("region", {
      name: "Transaction TX-OUT",
    });
    expect(
      within(card).getByRole("button", { name: /Show in timeline/ }),
    ).toBeDisabled();
    expect(card).toHaveTextContent("Not one of this case's transactions");
  });

  test("accessible list button selects edge", async () => {
    stub();
    renderWithClient(<CasePage caseId="FR-10482" />);

    const list = await screen.findByRole("list", {
      name: "Graph transactions",
    });
    await userEvent.setup().click(
      await within(list).findByRole("button", {
        name: /TX-1001: ACC-001 to BEN-B, ₹48,500.00/,
      }),
    );

    expect(
      await screen.findByRole("region", { name: "Transaction TX-1001" }),
    ).toBeInTheDocument();
  });
});
