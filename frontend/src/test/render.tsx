import { QueryClientProvider } from "@tanstack/react-query";
import { render, type RenderResult } from "@testing-library/react";
import type { ReactElement } from "react";

import type { Me } from "@/features/auth/schemas";
import { makeQueryClient } from "@/lib/query-client";

/** Render with a fresh QueryClient (no retries) per test. */
export function renderWithClient(ui: ReactElement): RenderResult {
  const client = makeQueryClient();
  client.setDefaultOptions({
    queries: { retry: false },
    mutations: { retry: false },
  });
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
  );
}

export function jsonResponse(
  body: unknown,
  status = 200,
  headers: Record<string, string> = {},
) {
  return new Response(body === null ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

export const ME: Record<Me["role"], Me> = {
  analyst: {
    id: "u-analyst",
    username: "analyst.demo",
    role: "analyst",
    permissions: [
      "alert:read",
      "case:read",
      "evidence:read",
      "transaction:read",
    ],
  },
  supervisor: {
    id: "u-super",
    username: "supervisor.demo",
    role: "supervisor",
    permissions: [
      "alert:read",
      "case:read",
      "case:transition",
      "evidence:read",
      "transaction:read",
      "user:manage",
    ],
  },
  auditor: {
    id: "u-audit",
    username: "auditor.demo",
    role: "auditor",
    permissions: ["audit:read"],
  },
};
