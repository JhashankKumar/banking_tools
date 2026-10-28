import { render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { Pagination } from "./Pagination";

const page = { total: 7, limit: 50, offset: 0 };

describe("Pagination", () => {
  test("defaults to newest first", () => {
    render(<Pagination page={page} noun="events" onOffset={vi.fn()} />);

    expect(screen.getByText("1–7 of 7 events · newest first")).toBeVisible();
  });

  test("states a different sort order when given one", () => {
    render(
      <Pagination page={page} noun="users" order="A–Z" onOffset={vi.fn()} />,
    );

    expect(screen.getByText("1–7 of 7 users · A–Z")).toBeVisible();
  });
});
