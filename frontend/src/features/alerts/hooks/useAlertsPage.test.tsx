import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, expect, test, vi } from "vitest";

import { makeQueryClient } from "@/lib/query-client";
import {
  ALERT_JSON,
  CASE_SUMMARY_JSON,
  RULES_JSON,
  page,
  routeFetch,
} from "@/test/fixtures";
import { jsonResponse } from "@/test/render";

import { useAlertsPage } from "./useAlertsPage";

afterEach(() => vi.unstubAllGlobals());

function wrapper({ children }: { children: ReactNode }) {
  const client = makeQueryClient();
  client.setDefaultOptions({ queries: { retry: false } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

test("search filters rows client-side and KPIs come from API totals", async () => {
  const other = {
    ...ALERT_JSON,
    id: "AL-ROT-TX-9999",
    case_id: "FR-10486",
    entity: { type: "account", id: "ACC-201" },
  };
  vi.stubGlobal(
    "fetch",
    vi.fn(
      routeFetch({
        "/api/alerts": () => jsonResponse(page([ALERT_JSON, other])),
        "/api/cases": () => jsonResponse(page([CASE_SUMMARY_JSON])),
        "/api/rules": () => jsonResponse({ data: RULES_JSON }),
      }),
    ),
  );
  const { result } = renderHook(() => useAlertsPage(), { wrapper });
  await waitFor(() => expect(result.current.rows).toHaveLength(2));

  act(() => result.current.setSearch("acc-201"));

  expect(result.current.rows.map((a) => a.id)).toEqual(["AL-ROT-TX-9999"]);
  expect(result.current.kpis).toEqual({
    openAlerts: 2,
    cases: 1,
    activeRules: 1,
  });
});

test("rule filter is sent to the server", async () => {
  const fetchMock = vi.fn(
    routeFetch({
      "/api/": () => jsonResponse(page([])),
      "/api/rules": () => jsonResponse({ data: RULES_JSON }),
    }),
  );
  vi.stubGlobal("fetch", fetchMock);
  const { result } = renderHook(() => useAlertsPage(), { wrapper });

  act(() => result.current.setRuleId("RAPID_ONWARD_TRANSFER"));

  await waitFor(() =>
    expect(fetchMock.mock.calls.map((c) => String(c[0]))).toContain(
      "/api/alerts?limit=50&offset=0&rule_id=RAPID_ONWARD_TRANSFER",
    ),
  );
});
