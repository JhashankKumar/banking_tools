import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, test, vi } from "vitest";

import { jsonResponse, ME, renderWithClient } from "@/test/render";

import { UserMenu } from "./UserMenu";

const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn() }),
}));

afterEach(() => {
  vi.unstubAllGlobals();
  replace.mockReset();
});

describe("UserMenu", () => {
  test("signs out and goes to login", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response(null, { status: 204 }))),
    );
    renderWithClient(<UserMenu me={ME.analyst} />);

    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: /sign out/i }));

    expect(replace).toHaveBeenCalledWith("/login");
  });

  test("failed sign-out says so and does not pretend the session ended", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          jsonResponse(
            {
              error: {
                code: "SERVICE_UNAVAILABLE",
                message: "The API is not reachable.",
                details: [],
                request_id: null,
              },
            },
            503,
          ),
        ),
      ),
    );
    renderWithClient(<UserMenu me={ME.analyst} />);

    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: /sign out/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Sign-out failed",
    );
    expect(replace).not.toHaveBeenCalled();
  });
});
