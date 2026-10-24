import { afterEach, describe, expect, test, vi } from "vitest";
import { z } from "zod";

import { apiClient } from "./api-client";
import { ApiError } from "./api-error";
import { envelope, pageEnvelope } from "./schemas";

const item = z
  .object({ case_id: z.string() })
  .transform((v) => ({ caseId: v.case_id }));

function respond(status: number, body: unknown) {
  return vi.fn().mockResolvedValue(
    new Response(JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("apiClient", () => {
  test("unwraps data envelope", async () => {
    vi.stubGlobal("fetch", respond(200, { data: { case_id: "FR-10482" } }));

    await expect(
      apiClient.get("/cases/FR-10482", envelope(item)),
    ).resolves.toEqual({
      caseId: "FR-10482",
    });
  });

  test("unwraps page envelope", async () => {
    vi.stubGlobal(
      "fetch",
      respond(200, {
        data: [{ case_id: "A" }],
        page: { total: 1, limit: 50, offset: 0 },
      }),
    );

    await expect(apiClient.get("/cases", pageEnvelope(item))).resolves.toEqual({
      items: [{ caseId: "A" }],
      page: { total: 1, limit: 50, offset: 0 },
    });
  });

  test("maps error envelope to ApiError with code, details, requestId", async () => {
    vi.stubGlobal(
      "fetch",
      respond(422, {
        error: {
          code: "VALIDATION_FAILED",
          message: "Request validation failed",
          details: [{ field: "query.limit", message: "too big" }],
          request_id: "req-1",
        },
      }),
    );

    const error = await apiClient
      .get("/cases", envelope(item))
      .catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 422,
      code: "VALIDATION_FAILED",
      details: [{ field: "query.limit", message: "too big" }],
      requestId: "req-1",
    });
  });

  test("schema mismatch becomes UNEXPECTED_RESPONSE", async () => {
    vi.stubGlobal("fetch", respond(200, { data: { wrong: true } }));

    await expect(
      apiClient.get("/cases/X", envelope(item)),
    ).rejects.toMatchObject({
      code: "UNEXPECTED_RESPONSE",
    });
  });

  test("network failure becomes NETWORK_ERROR", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );

    await expect(apiClient.get("/cases", envelope(item))).rejects.toMatchObject(
      {
        code: "NETWORK_ERROR",
      },
    );
  });

  test("passes abort signal and serializes params, skipping undefined", async () => {
    const fetchMock = respond(200, { data: { case_id: "A" } });
    vi.stubGlobal("fetch", fetchMock);
    const controller = new AbortController();

    await apiClient.get("/alerts", envelope(item), {
      signal: controller.signal,
      params: { case_id: "FR-10482", limit: 10, rule_id: undefined },
    });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/alerts?case_id=FR-10482&limit=10");
    expect(init.signal).toBeInstanceOf(AbortSignal);
  });

  test("post sends JSON body", async () => {
    const fetchMock = respond(201, { data: { case_id: "A" } });
    vi.stubGlobal("fetch", fetchMock);

    await apiClient.post("/users", { username: "a" }, envelope(item));

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ username: "a" }));
    expect(new Headers(init.headers).get("Content-Type")).toBe(
      "application/json",
    );
  });
});
