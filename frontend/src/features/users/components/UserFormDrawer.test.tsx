import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, test, vi } from "vitest";

import { jsonResponse, renderWithClient } from "@/test/render";

import { userSchema } from "../schemas";
import { UserFormDrawer } from "./UserFormDrawer";

const USER_JSON = {
  id: "u-analyst",
  username: "analyst.demo",
  role: "analyst",
  is_active: true,
  created_at: "2026-09-15T04:31:00Z",
  updated_at: "2026-09-15T04:31:00Z",
};
const USER = userSchema.parse(USER_JSON);

const errorBody = (code: string, details: object[] = []) => ({
  error: { code, message: "Rejected", details, request_id: "req-9" },
});

afterEach(() => vi.unstubAllGlobals());

async function fillCreate(password = "long-enough-pass") {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Username"), "new.analyst");
  await user.type(screen.getByLabelText("Temporary password"), password);
  await user.click(screen.getByRole("button", { name: "Create user" }));
}

describe("UserFormDrawer", () => {
  test("UserFormDrawer maps 422 password detail to field error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          jsonResponse(
            errorBody("VALIDATION_FAILED", [
              { field: "body.password", message: "Password is too common" },
            ]),
            422,
          ),
        ),
      ),
    );
    renderWithClient(<UserFormDrawer mode="create" open onClose={vi.fn()} />);

    await fillCreate();

    expect(await screen.findByText("Password is too common")).toBeVisible();
    expect(screen.getByLabelText("Temporary password")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
  });

  test("maps 409 USER_USERNAME_TAKEN to username", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(jsonResponse(errorBody("USER_USERNAME_TAKEN"), 409)),
      ),
    );
    renderWithClient(<UserFormDrawer mode="create" open onClose={vi.fn()} />);

    await fillCreate();

    expect(
      await screen.findByText("This username is already taken."),
    ).toBeVisible();
    expect(screen.getByLabelText("Username")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
  });

  test("short password is rejected before any request", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    renderWithClient(<UserFormDrawer mode="create" open onClose={vi.fn()} />);

    await fillCreate("short");

    expect(
      await screen.findByText("Use at least 12 characters."),
    ).toBeVisible();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  test("create posts username, password and role, then closes", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve(
        jsonResponse(
          {
            data: {
              id: "u-new",
              username: "new.analyst",
              role: "auditor",
              is_active: true,
              created_at: "2026-09-15T04:31:00Z",
              updated_at: "2026-09-15T04:31:00Z",
            },
          },
          201,
        ),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const onClose = vi.fn();
    renderWithClient(<UserFormDrawer mode="create" open onClose={onClose} />);

    await userEvent
      .setup()
      .click(screen.getByRole("radio", { name: "Auditor" }));
    expect(screen.getByText(/Reads the audit log only/)).toBeVisible();
    await fillCreate();

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const [url, init] = fetchMock.mock.calls[0] as unknown as [
      string,
      RequestInit,
    ];
    expect(url).toBe("/api/users");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({
      username: "new.analyst",
      password: "long-enough-pass",
      role: "auditor",
    });
  });

  test("edit sends only changed fields", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve(
        jsonResponse({
          data: {
            id: "u-analyst",
            username: "analyst.demo",
            role: "analyst",
            is_active: false,
            created_at: "2026-09-15T04:31:00Z",
            updated_at: "2026-09-15T04:40:00Z",
          },
        }),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const onClose = vi.fn();
    renderWithClient(
      <UserFormDrawer mode="edit" user={USER} open onClose={onClose} />,
    );
    const user = userEvent.setup();

    expect(screen.getByLabelText("Username")).toHaveAttribute("readonly");
    expect(screen.getByText(/Saved as audit event user.updated/)).toBeVisible();
    await user.click(screen.getByRole("switch", { name: "Active" }));
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const [url, init] = fetchMock.mock.calls[0] as unknown as [
      string,
      RequestInit,
    ];
    expect(url).toBe("/api/users/u-analyst");
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(init.body as string)).toEqual({ is_active: false });
  });

  test("own account: role and status are locked, password can change", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve(jsonResponse({ data: { ...USER_JSON } })),
    );
    vi.stubGlobal("fetch", fetchMock);
    const onClose = vi.fn();
    renderWithClient(
      <UserFormDrawer mode="edit" user={USER} isSelf open onClose={onClose} />,
    );
    const user = userEvent.setup();

    expect(screen.getByRole("radio", { name: "Supervisor" })).toBeDisabled();
    expect(screen.getByRole("switch", { name: "Active" })).toBeDisabled();
    expect(
      screen.getByText(/You cannot change your own role or status/),
    ).toBeVisible();
    await user.type(
      screen.getByLabelText("New password"),
      "a-new-long-password",
    );
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const [, init] = fetchMock.mock.calls[0] as unknown as [
      string,
      RequestInit,
    ];
    expect(JSON.parse(init.body as string)).toEqual({
      password: "a-new-long-password",
    });
  });

  test("submit is disabled while the request is in flight", async () => {
    let resolve: (r: Response) => void = () => {};
    const fetchMock = vi.fn(() => new Promise<Response>((r) => (resolve = r)));
    vi.stubGlobal("fetch", fetchMock);
    renderWithClient(<UserFormDrawer mode="create" open onClose={vi.fn()} />);

    await fillCreate();
    const submit = screen.getByRole("button", { name: "Create user" });
    expect(submit).toBeDisabled();
    await userEvent.setup().click(submit);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    resolve(jsonResponse({ data: { ...USER_JSON } }, 201));
  });

  test("409 USER_SELF_LOCKOUT shows a banner", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(jsonResponse(errorBody("USER_SELF_LOCKOUT"), 409)),
      ),
    );
    renderWithClient(
      <UserFormDrawer mode="edit" user={USER} open onClose={vi.fn()} />,
    );
    const user = userEvent.setup();

    await user.click(screen.getByRole("radio", { name: "Supervisor" }));
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Rejected");
  });
});
