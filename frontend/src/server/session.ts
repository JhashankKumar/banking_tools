/**
 * Server-side session helpers for the backend-for-frontend. Only route handlers and proxy.ts
 * import this module; the access token never reaches browser JavaScript.
 */
import { NextResponse, type NextRequest } from "next/server";

export const SESSION_COOKIE = "ofi_session";
const SESSION_SECONDS = 1800; // matches the API's 30-minute access token

export function sessionCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_SECONDS,
  };
}

export function apiUrl(path: string): string {
  const base = process.env.OFI_API_URL;
  if (!base) throw new Error("OFI_API_URL is not set");
  return `${base.replace(/\/$/, "")}${path}`;
}

/** True only when the request carries an Origin header equal to this app's origin. */
export function isSameOrigin(request: NextRequest): boolean {
  const origin = request.headers.get("origin");
  return origin !== null && origin === request.nextUrl.origin;
}

export function errorResponse(
  status: number,
  code: string,
  message: string,
): NextResponse {
  return NextResponse.json(
    { error: { code, message, details: [], request_id: null } },
    { status },
  );
}

export const forbiddenOrigin = () =>
  errorResponse(403, "AUTH_FORBIDDEN", "Cross-origin request rejected");
