import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { ApiError } from "@/lib/api-error";

import { ErrorBanner } from "./ErrorBanner";

describe("ErrorBanner", () => {
  test("shows the message, request ID and note as an alert", () => {
    const error = new ApiError({
      status: 401,
      code: "AUTH_INVALID_CREDENTIALS",
      message: "Invalid username or password",
      requestId: "req-7",
    });

    render(<ErrorBanner error={error} note="this attempt was recorded." />);

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Invalid username or password");
    expect(alert).toHaveTextContent(
      "Request ID req-7 · this attempt was recorded.",
    );
  });

  test("renders nothing without an error", () => {
    const { container } = render(<ErrorBanner error={null} />);

    expect(container).toBeEmptyDOMElement();
  });
});
