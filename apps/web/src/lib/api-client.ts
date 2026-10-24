import type { z } from "zod";

import { ApiError } from "./api-error";
import { BFF_BASE, REQUEST_TIMEOUT_MS } from "./config";
import { errorEnvelopeSchema } from "./schemas";

type Params = Record<string, string | number | undefined>;
interface RequestOptions {
  signal?: AbortSignal;
  params?: Params;
}

function buildUrl(path: string, params?: Params): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value !== undefined) query.set(key, String(value));
  }
  const qs = query.toString();
  return `${BFF_BASE}${path}${qs ? `?${qs}` : ""}`;
}

async function toApiError(response: Response): Promise<ApiError> {
  const body: unknown = await response.json().catch(() => null);
  const parsed = errorEnvelopeSchema.safeParse(body);
  if (!parsed.success) {
    return new ApiError({
      status: response.status,
      code: "UNEXPECTED_RESPONSE",
      message: "Unexpected response from the server.",
      requestId: response.headers.get("X-Request-ID"),
    });
  }
  const { code, message, details, request_id } = parsed.data.error;
  return new ApiError({
    status: response.status,
    code,
    message,
    details,
    requestId: request_id,
  });
}

async function request<S extends z.ZodType>(
  method: "GET" | "POST" | "PATCH",
  path: string,
  schema: S,
  { signal, params }: RequestOptions = {},
  body?: unknown,
): Promise<z.output<S>> {
  const signals = [
    AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    ...(signal ? [signal] : []),
  ];
  const headers = new Headers({ Accept: "application/json" });
  if (body !== undefined) headers.set("Content-Type", "application/json");
  let response: Response;
  try {
    response = await fetch(buildUrl(path, params), {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.any(signals),
      credentials: "same-origin",
    });
  } catch (error) {
    const timedOut =
      error instanceof DOMException && error.name === "TimeoutError";
    throw new ApiError({
      status: 0,
      code: timedOut ? "TIMEOUT" : "NETWORK_ERROR",
      message: timedOut
        ? "The server took too long to respond."
        : "Could not reach the server.",
    });
  }
  if (!response.ok) throw await toApiError(response);
  if (response.status === 204) return undefined as z.output<S>;
  const parsed = schema.safeParse(await response.json().catch(() => null));
  if (!parsed.success) {
    throw new ApiError({
      status: response.status,
      code: "UNEXPECTED_RESPONSE",
      message: "Unexpected response from the server.",
      requestId: response.headers.get("X-Request-ID"),
    });
  }
  return parsed.data as z.output<S>;
}

/** The only HTTP client in the app. Paths are API paths without `/api/v1`, e.g. `/cases`. */
export const apiClient = {
  get: <S extends z.ZodType>(path: string, schema: S, opts?: RequestOptions) =>
    request("GET", path, schema, opts),
  post: <S extends z.ZodType>(
    path: string,
    body: unknown,
    schema: S,
    opts?: RequestOptions,
  ) => request("POST", path, schema, opts, body),
  patch: <S extends z.ZodType>(
    path: string,
    body: unknown,
    schema: S,
    opts?: RequestOptions,
  ) => request("PATCH", path, schema, opts, body),
};
