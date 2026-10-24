import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test, vi } from "vitest";

import { apiError, stubFetch } from "@/test/http";
import { router } from "@/test/next-navigation";
import { ME, renderWithClient } from "@/test/render";

import { UserMenu } from "./UserMenu";

vi.mock("next/navigation", () => import("@/test/next-navigation"));

describe("UserMenu", () => {
  test("signs out and goes to login", async () => {
    stubFetch(new Response(null, { status: 204 }));
    renderWithClient(<UserMenu me={ME.analyst} />);

    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: /sign out/i }));

    expect(router.replace).toHaveBeenCalledWith("/login");
  });

  test("failed sign-out says so and does not pretend the session ended", async () => {
    stubFetch(
      apiError("SERVICE_UNAVAILABLE", 503, {
        message: "The API is not reachable.",
      }),
    );
    renderWithClient(<UserMenu me={ME.analyst} />);

    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: /sign out/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Sign-out failed",
    );
    expect(router.replace).not.toHaveBeenCalled();
  });
});
