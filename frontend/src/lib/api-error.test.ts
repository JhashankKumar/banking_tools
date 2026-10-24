import { expect, test } from "vitest";

import { ApiError, asApiError, userMessage } from "./api-error";

test("userMessage shows the server message for ApiError", () => {
  const error = new ApiError({
    status: 404,
    code: "CASE_NOT_FOUND",
    message: "Case not found",
  });

  expect(userMessage(error, "Something went wrong")).toBe("Case not found");
});

test("userMessage falls back for anything else", () => {
  expect(userMessage(new Error("boom"), "Something went wrong")).toBe(
    "Something went wrong",
  );
});

test("asApiError keeps an ApiError as it is", () => {
  const error = new ApiError({ status: 409, code: "X", message: "m" });

  expect(asApiError(error)).toBe(error);
});

test("asApiError wraps anything else without leaking its message", () => {
  const wrapped = asApiError(new Error("internal detail"));

  expect(wrapped).toBeInstanceOf(ApiError);
  expect(wrapped.code).toBe("UNEXPECTED_ERROR");
  expect(wrapped.message).toBe("Something went wrong.");
});
