import { NextRequest } from "next/server";
import { expect, test } from "vitest";

import { proxy } from "./proxy";

test("proxy redirects to login with next when no cookie", () => {
  const response = proxy(
    new NextRequest("http://localhost:3000/cases/FR-10482"),
  );

  expect(response.status).toBe(307);
  expect(response.headers.get("location")).toBe(
    "http://localhost:3000/login?next=%2Fcases%2FFR-10482",
  );
});

test("proxy lets requests with a session through", () => {
  const response = proxy(
    new NextRequest("http://localhost:3000/alerts", {
      headers: { Cookie: "ofi_session=tok" },
    }),
  );

  expect(response.headers.get("location")).toBeNull();
});

test("proxy lets /login through", () => {
  const response = proxy(new NextRequest("http://localhost:3000/login"));

  expect(response.headers.get("location")).toBeNull();
});
