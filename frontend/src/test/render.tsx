import { QueryClientProvider } from "@tanstack/react-query";
import {
  render,
  renderHook,
  type RenderHookResult,
  type RenderResult,
} from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";

import type { Me } from "@/features/auth/schemas";
import { makeQueryClient } from "@/lib/query-client";

function testClient() {
  const client = makeQueryClient();
  client.setDefaultOptions({
    queries: { retry: false },
    mutations: { retry: false },
  });
  return client;
}

/** Render with a fresh QueryClient (no retries) per test. */
export function renderWithClient(ui: ReactElement): RenderResult {
  return render(
    <QueryClientProvider client={testClient()}>{ui}</QueryClientProvider>,
  );
}

/** renderHook with a fresh QueryClient (no retries), for page hooks. */
export function renderHookWithClient<T>(
  hook: () => T,
): RenderHookResult<T, unknown> {
  const client = testClient();
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return renderHook(hook, { wrapper });
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
