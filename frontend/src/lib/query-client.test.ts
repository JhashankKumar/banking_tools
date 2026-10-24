import { expect, test, vi } from "vitest";

import { ApiError } from "./api-error";
import { makeQueryClient } from "./query-client";

test("redirects to login on AUTH_NOT_AUTHENTICATED", async () => {
  const assign = vi.fn();
  vi.stubGlobal("location", {
    ...window.location,
    pathname: "/cases/FR-10482",
    assign,
  });
  const client = makeQueryClient();

  await client
    .fetchQuery({
      queryKey: ["x"],
      retry: false,
      queryFn: () =>
        Promise.reject(
          new ApiError({
            status: 401,
            code: "AUTH_NOT_AUTHENTICATED",
            message: "Not authenticated",
          }),
        ),
    })
    .catch(() => undefined);

  expect(assign).toHaveBeenCalledWith("/login?next=%2Fcases%2FFR-10482");
});

test("does not redirect on other errors", async () => {
  const assign = vi.fn();
  vi.stubGlobal("location", {
    ...window.location,
    pathname: "/alerts",
    assign,
  });
  const client = makeQueryClient();

  await client
    .fetchQuery({
      queryKey: ["y"],
      retry: false,
      queryFn: () =>
        Promise.reject(
          new ApiError({
            status: 403,
            code: "AUTH_FORBIDDEN",
            message: "Forbidden",
          }),
        ),
    })
    .catch(() => undefined);

  expect(assign).not.toHaveBeenCalled();
});

test("does not retry an unexpected response shape", async () => {
  const client = makeQueryClient();
  const queryFn = vi.fn(() =>
    Promise.reject(
      new ApiError({
        status: 200,
        code: "UNEXPECTED_RESPONSE",
        message: "Unexpected response from the server.",
      }),
    ),
  );

  await client
    .fetchQuery({ queryKey: ["shape"], queryFn, retryDelay: 0 })
    .catch(() => undefined);

  expect(queryFn).toHaveBeenCalledTimes(1);
});
