import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test } from "vitest";

import { router } from "@/test/next-navigation";

import { LinkRow, Table, Td } from "./Table";
import { vi } from "vitest";

vi.mock("next/navigation", () => import("@/test/next-navigation"));

describe("Table", () => {
  test("shows the empty message instead of an empty table", () => {
    render(
      <Table empty="No rows match.">
        <tbody />
      </Table>,
    );

    expect(screen.getByText("No rows match.")).toBeVisible();
    expect(screen.queryByRole("table")).toBeNull();
  });
});

describe("LinkRow", () => {
  const renderRow = () =>
    render(
      <table>
        <tbody>
          <LinkRow href="/cases/FR-1" label="FR-1">
            <Td>
              <LinkRow.Link>FR-1</LinkRow.Link>
            </Td>
            <Td>title</Td>
          </LinkRow>
        </tbody>
      </table>,
    );

  test("the whole row navigates on click", async () => {
    renderRow();

    await userEvent.setup().click(screen.getByText("title"));

    expect(router.push).toHaveBeenCalledWith("/cases/FR-1");
  });

  test("keyboard users get a real link, and clicking it does not navigate twice", async () => {
    renderRow();
    const link = screen.getByRole("link", { name: "FR-1" });

    expect(link).toHaveAttribute("href", "/cases/FR-1");
    await userEvent.setup().click(link);
    expect(router.push).not.toHaveBeenCalled();
  });
});
