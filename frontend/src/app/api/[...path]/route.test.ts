import { NextRequest } from "next/server";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { callsOf, stubFetch } from "@/test/http";

import { GET, POST } from "./route";

const ORIGIN = "http://localhost:3000";
const ctx = (...path: string[]) => ({ params: Promise.resolve({ path }) });

function req(
  path: string,
  {
    cookie = true,
    origin = ORIGIN,
    ...init
  }: RequestInit & { cookie?: boolean; origin?: string | null } = {},
) {
  const headers = new Headers(init.headers);
  if (cookie) headers.set("Cookie", "ofi_session=tok-123");
  if (origin !== null) headers.set("Origin", origin);
  return new NextRequest(`${ORIGIN}/api/${path}`, {
    method: init.method,
    body: init.body,
    headers,
  });
}

beforeEach(() => vi.stubEnv("OFI_API_URL", "http://api.test"));

describe("/api proxy", () => {
  test("api proxy forwards bearer token and query", async () => {
    const fetchMock = stubFetch(Response.json({ data: [] }));

    const response = await GET(
      req("alerts?case_id=FR-10482&limit=5"),
      ctx("alerts"),
    );

    expect(response.status).toBe(200);
    const [[url, init]] = callsOf(fetchMock);
    expect(url).toBe("http://api.test/api/v1/alerts?case_id=FR-10482&limit=5");
    expect(new Headers(init.headers).get("Authorization")).toBe(
      "Bearer tok-123",
    );
  });

  test("api proxy returns 401 envelope without cookie", async () => {
    stubFetch();

    const response = await GET(req("alerts", { cookie: false }), ctx("alerts"));

    expect(response.status).toBe(401);
    expect((await response.json()).error.code).toBe("AUTH_NOT_AUTHENTICATED");
    expect(fetch).not.toHaveBeenCalled();
  });

  test("API response that breaks mid-body becomes a 502 envelope", async () => {
    const broken = new ReadableStream({
      start: (c) => c.error(new Error("connection reset")),
    });
    stubFetch(new Response(broken, { status: 200 }));

    const response = await GET(req("alerts"), ctx("alerts"));

    expect(response.status).toBe(502);
    expect((await response.json()).error.code).toBe("UNEXPECTED_RESPONSE");
  });

  test("rejects cross-origin non-GET", async () => {
    stubFetch();

    const response = await POST(
      req("users", {
        method: "POST",
        body: "{}",
        origin: "https://evil.example",
      }),
      ctx("users"),
    );

    expect(response.status).toBe(403);
    expect(fetch).not.toHaveBeenCalled();
  });

  test.each(["cross-site", "same-site", "none"])(
    "rejects GET with Sec-Fetch-Site %s before reaching the API",
    async (site) => {
      stubFetch();

      const response = await GET(
        req("cases/FR-10482", { headers: { "Sec-Fetch-Site": site } }),
        ctx("cases", "FR-10482"),
      );

      expect(response.status).toBe(403);
      expect(fetch).not.toHaveBeenCalled();
    },
  );

  test("allows same-origin GET and marks the response nosniff", async () => {
    stubFetch(Response.json({ data: [] }));

    const response = await GET(
      req("alerts", { headers: { "Sec-Fetch-Site": "same-origin" } }),
      ctx("alerts"),
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("X-Content-Type-Options")).toBe("nosniff");
  });

  test("rejects non-GET without Origin header", async () => {
    stubFetch();

    const response = await POST(
      req("users", { method: "POST", body: "{}", origin: null }),
      ctx("users"),
    );

    expect(response.status).toBe(403);
  });

  test.each([[".."], ["users", "..", "health"], ["a%2Fb"], ["http:"]])(
    "api proxy rejects path traversal segments %j",
    async (...segments) => {
      stubFetch();

      const response = await GET(req("x"), ctx(...segments));

      expect(response.status).toBe(400);
      expect(fetch).not.toHaveBeenCalled();
    },
  );

  test("api proxy passes through API status, body and X-Request-ID", async () => {
    const body = {
      error: {
        code: "CASE_NOT_FOUND",
        message: "Case not found",
        details: [],
        request_id: "r9",
      },
    };
    stubFetch(
      Response.json(body, {
        status: 404,
        headers: { "X-Request-ID": "r9" },
      }),
    );

    const response = await GET(req("cases/FR-99999"), ctx("cases", "FR-99999"));

    expect(response.status).toBe(404);
    expect(response.headers.get("X-Request-ID")).toBe("r9");
    expect(await response.json()).toEqual(body);
  });

  test("api proxy forwards JSON body on same-origin POST", async () => {
    const fetchMock = stubFetch(Response.json({ data: {} }, { status: 201 }));

    const response = await POST(
      req("users", {
        method: "POST",
        body: JSON.stringify({ username: "a.b" }),
        headers: { "Content-Type": "application/json" },
      }),
      ctx("users"),
    );

    expect(response.status).toBe(201);
    const [[, init]] = callsOf(fetchMock);
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ username: "a.b" }));
  });
});
