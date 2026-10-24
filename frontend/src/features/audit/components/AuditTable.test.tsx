import { QueryClientProvider } from "@tanstack/react-query";
import {
  act,
  render,
  renderHook,
  screen,
  waitFor,
} from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, test, vi } from "vitest";

import { makeQueryClient } from "@/lib/query-client";
import { jsonResponse } from "@/test/render";
import { page } from "@/test/fixtures";

import { useAuditPage } from "../hooks/useAuditPage";
import { auditEventSchema } from "../schemas";
import { AuditTable } from "./AuditTable";

const EVENT = {
  id: 1,
  occurred_at: "2026-09-15T04:37:42Z",
  actor_user_id: "u-analyst",
  actor_username: "analyst.demo",
  action: "case.viewed",
  resource_type: "case",
  resource_id: "FR-10482",
  outcome: "success",
  request_id: "req-1",
  details: {},
};
const EVENTS_JSON = [
  EVENT,
  {
    ...EVENT,
    id: 2,
    actor_user_id: null,
    actor_username: null,
    action: "detection.run",
    resource_type: null,
    resource_id: null,
    request_id: null,
  },
  {
    ...EVENT,
    id: 3,
    actor_user_id: null,
    actor_username: null,
    action: "auth.login.failed",
    resource_type: null,
    resource_id: null,
    outcome: "failure",
    request_id: "req-3",
  },
  {
    ...EVENT,
    id: 4,
    action: "audit.viewed",
    resource_type: null,
    resource_id: null,
    outcome: "denied",
    request_id: "req-4",
  },
];
const events = EVENTS_JSON.map((e) => auditEventSchema.parse(e));

afterEach(() => vi.unstubAllGlobals());

describe("AuditTable", () => {
  test("AuditTable shows actor username, system for detection.run, unknown for failed login", () => {
    render(<AuditTable events={events} />);

    expect(screen.getByRole("row", { name: "Event 1" })).toHaveTextContent(
      "analyst.demo",
    );
    expect(screen.getByRole("row", { name: "Event 2" })).toHaveTextContent(
      "system",
    );
    expect(screen.getByRole("row", { name: "Event 3" })).toHaveTextContent(
      "unknown",
    );
    expect(screen.getByRole("row", { name: "Event 1" })).toHaveTextContent(
      "15 Sep 2026, 10:07:42 IST",
    );
  });

  test("outcome chips have icon and text", () => {
    render(<AuditTable events={events} />);

    for (const [id, text] of [
      ["1", "success"],
      ["3", "failure"],
      ["4", "denied"],
    ]) {
      const chip = screen
        .getByRole("row", { name: `Event ${id}` })
        .querySelector("[data-outcome]");
      expect(chip).toHaveTextContent(text);
      expect(chip?.querySelector("svg")).not.toBeNull();
    }
  });

  test("empty state when no rows", () => {
    render(<AuditTable events={[]} />);

    expect(
      screen.getByText("No audit events match these filters."),
    ).toBeInTheDocument();
  });
});

describe("useAuditPage", () => {
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={makeQueryClient()}>
      {children}
    </QueryClientProvider>
  );

  test("outcome filter is client-side", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve(jsonResponse(page(EVENTS_JSON))),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useAuditPage(), { wrapper });
    await waitFor(() => expect(result.current.rows).toHaveLength(4));

    act(() => result.current.setOutcome("denied"));

    expect(result.current.rows.map((e) => e.id)).toEqual([4]);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0])).not.toContain("outcome");
  });

  test("action filter is sent to the server", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve(jsonResponse(page(EVENTS_JSON))),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useAuditPage(), { wrapper });
    await waitFor(() => expect(result.current.rows).toHaveLength(4));

    act(() => result.current.setAction("auth.login.failed"));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(String(fetchMock.mock.calls[1])).toContain(
      "/api/audit-logs?limit=50&offset=0&action=auth.login.failed",
    );
  });

  test("KPIs count the loaded page", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(jsonResponse(page(EVENTS_JSON)))),
    );
    const { result } = renderHook(() => useAuditPage(), { wrapper });

    await waitFor(() =>
      expect(result.current.kpis).toEqual({
        events: 4,
        denied: 1,
        failedSignIns: 1,
        detectionRuns: 1,
      }),
    );
  });
});
