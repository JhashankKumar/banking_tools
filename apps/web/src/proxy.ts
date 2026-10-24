import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/server/session";

/** Sends page requests without a session to /login. Authorisation stays with the API. */
export function proxy(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl;
  if (pathname === "/login" || request.cookies.has(SESSION_COOKIE))
    return NextResponse.next();
  const login = new URL("/login", request.url);
  login.searchParams.set("next", pathname);
  return NextResponse.redirect(login);
}

export const config = {
  // Pages only: not the BFF, session routes, Next internals, or static files.
  matcher: ["/((?!login|session|bff|_next|favicon.ico|.*\\..*).*)"],
};
