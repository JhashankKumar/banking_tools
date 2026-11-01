import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test, vi } from "vitest";

import { apiError, jsonResponse, stubFetch } from "@/test/http";
import { navigation, router } from "@/test/next-navigation";
import { ME, renderWithClient } from "@/test/render";

import { LoginForm } from "./LoginForm";

vi.mock("next/navigation", () => import("@/test/next-navigation"));

async function fill(username: string, password: string) {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Username"), username);
  await user.type(screen.getByLabelText("Password"), password);
  await user.click(screen.getByRole("button", { name: "Sign in" }));
}

const stubLogin = (loginResponse: Response) =>
  stubFetch({
    "/auth/login": () => loginResponse,
    "/api/auth/me": () => jsonResponse({ data: ME.analyst }),
  });

describe("LoginForm", () => {
  test("shows validation error for invalid username", async () => {
    stubLogin(new Response(null, { status: 204 }));
    renderWithClient(<LoginForm />);

    await fill("Not Valid!", "whatever-password");

    expect(
      await screen.findByText(/lowercase letters, digits/i),
    ).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  test("shows API error message and request id on 401", async () => {
    stubLogin(
      apiError("AUTH_INVALID_CREDENTIALS", 401, {
        message: "Invalid username or password",
        requestId: "req-42",
      }),
    );
    renderWithClient(<LoginForm />);

    await fill("analyst.demo", "wrong-password");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Invalid username or password",
    );
    expect(screen.getByRole("alert")).toHaveTextContent("req-42");
  });

  test("clears username and password after a successful sign-in", async () => {
    // Next keeps this route mounted (hidden) after navigating away, so whatever the form
    // still holds reappears on sign-out — and the password would sit in memory meanwhile.
    stubLogin(new Response(null, { status: 204 }));
    renderWithClient(<LoginForm />);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Show password" }));
    await fill("analyst.demo", "a-good-password");

    await waitFor(() => expect(router.replace).toHaveBeenCalled());
    expect(screen.getByLabelText("Username")).toHaveValue("");
    expect(screen.getByLabelText("Password")).toHaveValue("");
    expect(screen.getByLabelText("Password")).toHaveAttribute(
      "type",
      "password",
    );
  });

  test("keeps what was typed after a failed sign-in", async () => {
    stubLogin(
      apiError("AUTH_INVALID_CREDENTIALS", 401, {
        message: "Invalid username or password",
      }),
    );
    renderWithClient(<LoginForm />);

    await fill("analyst.demo", "wrong-password");

    await screen.findByRole("alert");
    expect(screen.getByLabelText("Username")).toHaveValue("analyst.demo");
  });

  test("redirects to next path on success", async () => {
    navigation.search = "next=%2Fcases%2FFR-10482";
    stubLogin(new Response(null, { status: 204 }));
    renderWithClient(<LoginForm />);

    await fill("analyst.demo", "a-good-password");

    await waitFor(() =>
      expect(router.replace).toHaveBeenCalledWith("/cases/FR-10482"),
    );
  });

  test("ignores external next values", async () => {
    navigation.search = "next=%2F%2Fevil.example";
    stubLogin(new Response(null, { status: 204 }));
    renderWithClient(<LoginForm />);

    await fill("analyst.demo", "a-good-password");

    await waitFor(() => expect(router.replace).toHaveBeenCalledWith("/alerts"));
  });

  test.each([
    ["tab", "next=%2F%09%2Fevil.example"],
    ["newline", "next=%2F%0A%2Fevil.example"],
    ["backslash", "next=%2F%5Cevil.example"],
    ["absolute URL", "next=https%3A%2F%2Fevil.example%2F"],
  ])("ignores next that escapes the origin via %s", async (_, query) => {
    navigation.search = query;
    stubLogin(new Response(null, { status: 204 }));
    renderWithClient(<LoginForm />);

    await fill("analyst.demo", "a-good-password");

    await waitFor(() => expect(router.replace).toHaveBeenCalledWith("/alerts"));
  });

  test("keeps query and hash of a same-origin next", async () => {
    navigation.search = "next=%2Faudit%3Faction%3Dx%23top";
    stubLogin(new Response(null, { status: 204 }));
    renderWithClient(<LoginForm />);

    await fill("analyst.demo", "a-good-password");

    await waitFor(() =>
      expect(router.replace).toHaveBeenCalledWith("/audit?action=x#top"),
    );
  });

  test("does not show any password value in the demo users hint", () => {
    stubLogin(new Response(null, { status: 204 }));
    renderWithClient(<LoginForm />);

    expect(
      screen.getByText(/analyst\.demo · supervisor\.demo · auditor\.demo/),
    ).toBeInTheDocument();
    expect(screen.getByText(/never shown here/i)).toBeInTheDocument();
  });
});
