import { NextResponse, type NextRequest } from "next/server";

import {
  SESSION_COOKIE,
  apiUrl,
  errorResponse,
  forbiddenOrigin,
  isSameOrigin,
  sessionCookieOptions,
} from "@/server/session";

/** Exchanges credentials for an API token and keeps it in an httpOnly cookie. */
export async function POST(request: NextRequest): Promise<NextResponse> {
  if (!isSameOrigin(request)) return forbiddenOrigin();
  const body = (await request.json().catch(() => null)) as {
    username?: unknown;
    password?: unknown;
  } | null;
  const username = typeof body?.username === "string" ? body.username : "";
  const password = typeof body?.password === "string" ? body.password : "";

  let upstream: Response;
  try {
    upstream = await fetch(apiUrl("/api/v1/auth/token"), {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username, password }).toString(),
      cache: "no-store",
    });
  } catch {
    return errorResponse(
      503,
      "SERVICE_UNAVAILABLE",
      "The API is not reachable.",
    );
  }
  if (!upstream.ok) {
    return new NextResponse(await upstream.text(), {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  }
  const payload = (await upstream.json().catch(() => null)) as {
    access_token?: unknown;
  } | null;
  const token = payload?.access_token;
  if (typeof token !== "string") {
    return errorResponse(
      502,
      "UNEXPECTED_RESPONSE",
      "Unexpected response from the API.",
    );
  }
  const response = new NextResponse(null, { status: 204 });
  response.cookies.set(SESSION_COOKIE, token, sessionCookieOptions());
  return response;
}
