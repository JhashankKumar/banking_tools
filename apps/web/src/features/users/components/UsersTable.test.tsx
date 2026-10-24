import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test, vi } from "vitest";

import { userSchema } from "../schemas";
import { UsersTable } from "./UsersTable";

const USERS_JSON = [
  {
    id: "u-super",
    username: "supervisor.demo",
    role: "supervisor",
    is_active: true,
    created_at: "2026-09-15T04:30:00Z",
    updated_at: "2026-09-15T04:30:00Z",
  },
  {
    id: "u-analyst",
    username: "analyst.demo",
    role: "analyst",
    is_active: false,
    created_at: "2026-09-15T04:31:00Z",
    updated_at: "2026-09-15T04:31:00Z",
  },
];
const users = USERS_JSON.map((u) => userSchema.parse(u));

describe("UsersTable", () => {
  test("UsersTable marks own row and still offers edit for a password change", async () => {
    const onEdit = vi.fn();
    render(<UsersTable users={users} meId="u-super" onEdit={onEdit} />);

    const own = screen.getByRole("row", { name: "supervisor.demo" });
    expect(own).toHaveTextContent("You");
    expect(own).toHaveTextContent("Role and status locked");
    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: "Edit supervisor.demo" }));

    expect(onEdit).toHaveBeenCalledWith(users[0]);
  });

  test("other rows show role, status and an Edit button", async () => {
    const onEdit = vi.fn();
    render(<UsersTable users={users} meId="u-super" onEdit={onEdit} />);

    const row = screen.getByRole("row", { name: "analyst.demo" });
    expect(row).toHaveTextContent("Analyst");
    expect(row).toHaveTextContent("Inactive");
    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: "Edit analyst.demo" }));

    expect(onEdit).toHaveBeenCalledWith(users[1]);
  });
});
