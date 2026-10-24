import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { ME, jsonResponse, renderWithClient } from "@/test/render";

import { LoginForm } from "./LoginForm";

const replace = vi.fn();
let search = "";
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(search),
}));

beforeEach(() => {
  replace.mockReset();
  search = "";
});
afterEach(() => vi.unstubAllGlobals());

async function fill(username: string, password: string) {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Username"), username);
  await user.type(screen.getByLabelText("Password"), password);
  await user.click(screen.getByRole("button", { name: "Sign in" }));
}

function stubLogin(loginResponse: Response) {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      Promise.resolve(
        url === "/session/login"
          ? loginResponse
          : jsonResponse({ data: ME.analyst }),
      ),
    ),
  );
}

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
      jsonResponse(
        {
          error: {
            code: "AUTH_INVALID_CREDENTIALS",
            message: "Invalid username or password",
            details: [],
            request_id: "req-42",
          },
        },
        401,
      ),
    );
    renderWithClient(<LoginForm />);

    await fill("analyst.demo", "wrong-password");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Invalid username or password",
    );
    expect(screen.getByRole("alert")).toHaveTextContent("req-42");
  });

  test("redirects to next path on success", async () => {
    search = "next=%2Fcases%2FFR-10482";
    stubLogin(new Response(null, { status: 204 }));
    renderWithClient(<LoginForm />);

    await fill("analyst.demo", "a-good-password");

    await waitFor(() =>
      expect(replace).toHaveBeenCalledWith("/cases/FR-10482"),
    );
  });

  test("ignores external next values", async () => {
    search = "next=%2F%2Fevil.example";
    stubLogin(new Response(null, { status: 204 }));
    renderWithClient(<LoginForm />);

    await fill("analyst.demo", "a-good-password");

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/alerts"));
  });

  test.each([
    ["tab", "next=%2F%09%2Fevil.example"],
    ["newline", "next=%2F%0A%2Fevil.example"],
    ["backslash", "next=%2F%5Cevil.example"],
    ["absolute URL", "next=https%3A%2F%2Fevil.example%2F"],
  ])("ignores next that escapes the origin via %s", async (_, query) => {
    search = query;
    stubLogin(new Response(null, { status: 204 }));
    renderWithClient(<LoginForm />);

    await fill("analyst.demo", "a-good-password");

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/alerts"));
  });

  test("keeps query and hash of a same-origin next", async () => {
    search = "next=%2Faudit%3Faction%3Dx%23top";
    stubLogin(new Response(null, { status: 204 }));
    renderWithClient(<LoginForm />);

    await fill("analyst.demo", "a-good-password");

    await waitFor(() =>
      expect(replace).toHaveBeenCalledWith("/audit?action=x#top"),
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
