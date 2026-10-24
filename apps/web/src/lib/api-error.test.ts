import { expect, test } from "vitest";

import { ApiError, userMessage } from "./api-error";

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
