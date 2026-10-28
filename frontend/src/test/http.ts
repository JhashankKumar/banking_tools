import { vi, type Mock } from "vitest";

type FetchInput = string | URL | Request;
type Handler = (
  input: FetchInput,
  init?: RequestInit,
) => Response | Promise<Response>;
export type FetchMock = Mock<
  (input: FetchInput, init?: RequestInit) => Promise<Response>
>;

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

/** An API error envelope, as the backend (and the API proxy) sends it. */
export function apiError(
  code: string,
  status: number,
  {
    message = "Rejected",
    details = [],
    requestId = "req-test",
  }: {
    message?: string;
    details?: { field: string; message: string }[];
    requestId?: string | null;
  } = {},
) {
  return jsonResponse(
    { error: { code, message, details, request_id: requestId } },
    status,
  );
}

const pathOf = (input: FetchInput) =>
  (typeof input === "string"
    ? input
    : input instanceof URL
      ? input.toString()
      : input.url
  ).replace(/^https?:\/\/[^/]+/, "");

/** Routes by longest matching path prefix; anything unmatched is a 404 envelope. */
export function routeFetch(routes: Record<string, () => Response>): Handler {
  return (input) => {
    const path = pathOf(input);
    const key = Object.keys(routes)
      .sort((a, b) => b.length - a.length)
      .find((prefix) => path.startsWith(prefix));
    return key
      ? routes[key]()
      : apiError("NOT_FOUND", 404, { message: "Not found" });
  };
}

/**
 * Replaces global fetch for one test (setup.ts restores it) and returns the mock.
 * - nothing: a mock that must not be called (assert with `not.toHaveBeenCalled()`)
 * - a Response: answered on every call (cloned, so the body can be read each time)
 * - a function: called per request; may throw or reject to simulate network failures
 * - a route map: `{ "/api/cases": () => jsonResponse(...) }`, see routeFetch
 */
export function stubFetch(
  source?: Response | Handler | Record<string, () => Response>,
): FetchMock {
  const handler: Handler | undefined =
    source === undefined
      ? undefined
      : source instanceof Response
        ? () => source.clone()
        : typeof source === "function"
          ? source
          : routeFetch(source);
  const mock: FetchMock = vi.fn((input: FetchInput, init?: RequestInit) =>
    handler
      ? Promise.resolve().then(() => handler(input, init))
      : Promise.resolve(new Response(null)),
  );
  vi.stubGlobal("fetch", mock);
  return mock;
}

/** The recorded calls as [url, init] pairs (URLs exactly as requested), without casts. */
export const callsOf = (mock: FetchMock) =>
  mock.mock.calls.map(
    ([input, init]) =>
      [
        input instanceof Request ? input.url : String(input),
        init ?? {},
      ] as const,
  );
