import { NextResponse, type NextRequest } from "next/server";

import {
  SESSION_COOKIE,
  forbiddenOrigin,
  isSameOrigin,
} from "@/server/session";

export function POST(request: NextRequest): NextResponse {
  if (!isSameOrigin(request)) return forbiddenOrigin();
  const response = new NextResponse(null, { status: 204 });
  response.cookies.set(SESSION_COOKIE, "", {
    path: "/",
    maxAge: 0,
    httpOnly: true,
  });
  return response;
}
