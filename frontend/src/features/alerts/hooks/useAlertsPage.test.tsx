import { act, waitFor } from "@testing-library/react";
import { expect, test } from "vitest";

import {
  ALERT_JSON,
  CASE_SUMMARY_JSON,
  RULES_JSON,
  page,
} from "@/test/fixtures";
import { callsOf, jsonResponse, stubFetch } from "@/test/http";
import { renderHookWithClient } from "@/test/render";

import { useAlertsPage } from "./useAlertsPage";

test("search filters rows client-side and KPIs come from API totals", async () => {
  const other = {
    ...ALERT_JSON,
    id: "AL-ROT-TX-9999",
    case_id: "FR-10486",
    entity: { type: "account", id: "ACC-201" },
  };
  stubFetch({
    "/api/alerts": () => jsonResponse(page([ALERT_JSON, other])),
    "/api/cases": () => jsonResponse(page([CASE_SUMMARY_JSON])),
    "/api/rules": () => jsonResponse({ data: RULES_JSON }),
  });
  const { result } = renderHookWithClient(() => useAlertsPage());
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
  const fetchMock = stubFetch({
    "/api/": () => jsonResponse(page([])),
    "/api/rules": () => jsonResponse({ data: RULES_JSON }),
  });
  const { result } = renderHookWithClient(() => useAlertsPage());

  act(() => result.current.setRuleId("RAPID_ONWARD_TRANSFER"));

  await waitFor(() =>
    expect(callsOf(fetchMock).map(([url]) => url)).toContain(
      "/api/alerts?limit=50&offset=0&rule_id=RAPID_ONWARD_TRANSFER",
    ),
  );
});
