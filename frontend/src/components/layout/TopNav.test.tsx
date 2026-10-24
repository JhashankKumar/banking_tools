import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test, vi } from "vitest";

import { ME, renderWithClient } from "@/test/render";

import { TopNav } from "./TopNav";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/alerts",
}));

describe("TopNav", () => {
  test("shows Audit only for auditor", () => {
    renderWithClient(<TopNav me={ME.auditor} />);

    const links = screen.getAllByRole("link").map((l) => l.textContent);
    expect(links).toContain("Audit");
    expect(links).not.toContain("Alerts");
    expect(links).not.toContain("Cases");
  });

  test("shows Users for supervisor and hides Audit", () => {
    renderWithClient(<TopNav me={ME.supervisor} />);

    const links = screen.getAllByRole("link").map((l) => l.textContent);
    expect(links).toEqual(expect.arrayContaining(["Alerts", "Cases", "Users"]));
    expect(links).not.toContain("Audit");
  });

  test("marks the current section", () => {
    renderWithClient(<TopNav me={ME.analyst} />);

    expect(screen.getByRole("link", { name: "Alerts" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  test("theme switch sets data-theme and persists", async () => {
    renderWithClient(<TopNav me={ME.analyst} />);

    await userEvent.setup().click(screen.getByRole("radio", { name: /dark/i }));

    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(localStorage.getItem("ofi-theme")).toBe("dark");
  });
});
