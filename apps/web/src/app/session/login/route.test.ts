import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { POST } from "./route";
import { POST as LOGOUT } from "../logout/route";

const ORIGIN = "http://localhost:3000";

function loginRequest(body: unknown, origin: string | null = ORIGIN) {
  const headers = new Headers({ "Content-Type": "application/json" });
  if (origin) headers.set("Origin", origin);
  return new NextRequest(`${ORIGIN}/session/login`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
}

beforeEach(() => vi.stubEnv("OFI_API_URL", "http://api.test"));
afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("POST /session/login", () => {
  test("login sets httpOnly session cookie and returns 204", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({
        access_token: "tok-123",
        token_type: "bearer",
        expires_in: 1800,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await POST(
      loginRequest({ username: "analyst.demo", password: "secret-password" }),
    );

    expect(response.status).toBe(204);
    const cookie = response.headers.get("set-cookie") ?? "";
    expect(cookie).toContain("ofi_session=tok-123");
    expect(cookie).toMatch(/HttpOnly/i);
    expect(cookie).toMatch(/SameSite=lax/i);
    expect(cookie).toContain("Max-Age=1800");
    expect(cookie).toContain("Path=/");
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://api.test/api/v1/auth/token");
    expect(String(init.body)).toBe(
      "username=analyst.demo&password=secret-password",
    );
  });

  test("login passes API 401 body through unchanged", async () => {
    const body = {
      error: {
        code: "AUTH_INVALID_CREDENTIALS",
        message: "Invalid username or password",
        details: [],
        request_id: "r1",
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(Response.json(body, { status: 401 })),
    );

    const response = await POST(
      loginRequest({ username: "analyst.demo", password: "wrong" }),
    );

    expect(response.status).toBe(401);
    expect(await response.json()).toEqual(body);
    expect(response.headers.get("set-cookie")).toBeNull();
  });

  test("login rejects cross-origin", async () => {
    vi.stubGlobal("fetch", vi.fn());

    const response = await POST(
      loginRequest(
        { username: "a.b.c", password: "x" },
        "https://evil.example",
      ),
    );

    expect(response.status).toBe(403);
    expect(fetch).not.toHaveBeenCalled();
  });
});

test("logout clears cookie", async () => {
  const request = new NextRequest(`${ORIGIN}/session/logout`, {
    method: "POST",
    headers: { Origin: ORIGIN, Cookie: "ofi_session=tok-123" },
  });

  const response = await LOGOUT(request);

  expect(response.status).toBe(204);
  expect(response.headers.get("set-cookie")).toMatch(
    /ofi_session=;.*(Max-Age=0|Expires=Thu, 01 Jan 1970)/i,
  );
});
