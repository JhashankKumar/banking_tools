import { afterEach, describe, expect, test, vi } from "vitest";

import { ApiError } from "@/lib/api-error";

import { login, logout } from "./api";

afterEach(() => vi.unstubAllGlobals());

describe("auth api", () => {
  test("network failure on sign-in becomes NETWORK_ERROR ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );

    const error = await login({ username: "a.b", password: "x" }).catch(
      (e: unknown) => e,
    );

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).code).toBe("NETWORK_ERROR");
  });

  test("sign-in and sign-out use the shared client (timeout signal, JSON body)", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve(new Response(null, { status: 204 })),
    );
    vi.stubGlobal("fetch", fetchMock);

    await login({ username: "a.b", password: "a-long-password" });
    await logout();

    const [[loginUrl, loginInit], [logoutUrl, logoutInit]] = fetchMock.mock
      .calls as unknown as [string, RequestInit][];
    expect(loginUrl).toBe("/auth/login");
    expect(loginInit.signal).toBeInstanceOf(AbortSignal);
    expect(JSON.parse(loginInit.body as string)).toEqual({
      username: "a.b",
      password: "a-long-password",
    });
    expect(logoutUrl).toBe("/auth/logout");
    expect(logoutInit.method).toBe("POST");
  });
});
