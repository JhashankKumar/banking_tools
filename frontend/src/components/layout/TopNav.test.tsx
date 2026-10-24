import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { navigation } from "@/test/next-navigation";
import { ME, renderWithClient } from "@/test/render";

import { TopNav } from "./TopNav";

vi.mock("next/navigation", () => import("@/test/next-navigation"));

beforeEach(() => {
  navigation.pathname = "/alerts";
});

describe("TopNav", () => {
  test("shows Audit only for auditor", () => {
    renderWithClient(<TopNav me={ME.auditor} />);

    const links = screen.getAllByRole("link").map((l) => l.textContent);
    expect(links).toContain("Audit");
    expect(links).not.toContain("Alerts");
    expect(links).not.toContain("Cases");
  });

  test("supervisor nav has Reviews; analyst nav does not", () => {
    const { unmount } = renderWithClient(<TopNav me={ME.supervisor} />);
    expect(screen.getByRole("link", { name: "Reviews" })).toHaveAttribute(
      "href",
      "/reviews",
    );
    unmount();

    renderWithClient(<TopNav me={ME.analyst} />);
    expect(screen.queryByRole("link", { name: "Reviews" })).toBeNull();
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
