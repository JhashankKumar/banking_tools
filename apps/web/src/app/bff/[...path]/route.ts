import { NextResponse, type NextRequest } from "next/server";

import {
  SESSION_COOKIE,
  apiUrl,
  errorResponse,
  forbiddenOrigin,
  isSameOrigin,
} from "@/server/session";

/**
 * Backend-for-frontend: forwards same-origin browser calls to the API with the bearer token
 * from the httpOnly session cookie. Only plain path segments are allowed, so the target is
 * always `${OFI_API_URL}/api/v1/...`.
 */
const SAFE_SEGMENT = /^[A-Za-z0-9._-]+$/;
type Context = { params: Promise<{ path: string[] }> };

async function forward(
  request: NextRequest,
  { params }: Context,
): Promise<NextResponse> {
  const { path } = await params;
  if (!path.every((s) => SAFE_SEGMENT.test(s) && s !== "." && s !== "..")) {
    return errorResponse(400, "VALIDATION_FAILED", "Invalid API path");
  }
  if (request.method !== "GET" && !isSameOrigin(request))
    return forbiddenOrigin();
  // Reads are audited by the API, so a cross-site navigation must not record views as the victim.
  const fetchSite = request.headers.get("sec-fetch-site");
  if (fetchSite !== null && fetchSite !== "same-origin")
    return forbiddenOrigin();
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token)
    return errorResponse(401, "AUTH_NOT_AUTHENTICATED", "Not authenticated");

  const headers = new Headers({
    Authorization: `Bearer ${token}`,
    Accept: "application/json",
  });
  const requestId = request.headers.get("x-request-id");
  if (requestId) headers.set("X-Request-ID", requestId);
  const hasBody = request.method !== "GET";
  if (hasBody) headers.set("Content-Type", "application/json");

  let upstream: Response;
  try {
    upstream = await fetch(
      apiUrl(`/api/v1/${path.join("/")}${request.nextUrl.search}`),
      {
        method: request.method,
        headers,
        body: hasBody ? await request.text() : undefined,
        cache: "no-store",
      },
    );
  } catch {
    return errorResponse(
      503,
      "SERVICE_UNAVAILABLE",
      "The API is not reachable.",
    );
  }
  const out = new Headers({
    "Content-Type": upstream.headers.get("content-type") ?? "application/json",
    "X-Content-Type-Options": "nosniff",
  });
  const upstreamId = upstream.headers.get("x-request-id");
  if (upstreamId) out.set("X-Request-ID", upstreamId);
  const body = upstream.status === 204 ? null : await upstream.arrayBuffer();
  return new NextResponse(body, { status: upstream.status, headers: out });
}

export const GET = forward;
export const POST = forward;
export const PATCH = forward;
