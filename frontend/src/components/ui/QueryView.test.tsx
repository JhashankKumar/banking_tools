import type { UseQueryResult } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { ApiError } from "@/lib/api-error";

import { QueryView } from "./QueryView";

// Only the fields QueryView reads; the cast keeps the tests free of TanStack internals.
const pending = {
  isPending: true,
  isError: false,
} as unknown as UseQueryResult<string[]>;
const failed = (status: number) =>
  ({
    isPending: false,
    isError: true,
    error: new ApiError({
      status,
      code: "X",
      message: "Server said no",
      requestId: "r1",
    }),
  }) as unknown as UseQueryResult<string[]>;
const loaded = (data: string[]) =>
  ({ isPending: false, isError: false, data }) as unknown as UseQueryResult<
    string[]
  >;

describe("QueryView", () => {
  test("shows the loading state with its title", () => {
    render(
      <QueryView query={pending} noun="Cases" loading="Loading cases">
        {() => <p>content</p>}
      </QueryView>,
    );

    expect(screen.getByRole("status")).toHaveTextContent("Loading cases");
    expect(screen.queryByText("content")).toBeNull();
  });

  test("maps 403 to permission denied", () => {
    render(
      <QueryView query={failed(403)} noun="Cases" loading="Loading cases">
        {() => <p>content</p>}
      </QueryView>,
    );

    expect(
      screen.getByRole("heading", {
        name: "You don't have access to this page",
      }),
    ).toBeVisible();
  });

  test("404 can carry its own message and action", () => {
    render(
      <QueryView
        query={failed(404)}
        noun="Case"
        loading="Loading case"
        notFound={{
          message: "No case with ID FR-1.",
          action: <button type="button">Back</button>,
        }}
      >
        {() => <p>content</p>}
      </QueryView>,
    );

    expect(
      screen.getByRole("heading", { name: "Case not found" }),
    ).toBeVisible();
    expect(screen.getByText("No case with ID FR-1.")).toBeVisible();
    expect(screen.getByRole("button", { name: "Back" })).toBeVisible();
  });

  test("renders children with the data", () => {
    render(
      <QueryView
        query={loaded(["a", "b"])}
        noun="Cases"
        loading="Loading cases"
      >
        {(data) => <p>{data.join(",")}</p>}
      </QueryView>,
    );

    expect(screen.getByText("a,b")).toBeVisible();
  });

  test("shows the empty state when the data is empty", () => {
    render(
      <QueryView
        query={loaded([])}
        noun="Graph"
        loading="Loading graph"
        empty={{
          when: (d) => d.length === 0,
          title: "No transactions in this window",
        }}
      >
        {() => <p>content</p>}
      </QueryView>,
    );

    expect(screen.getByText("No transactions in this window")).toBeVisible();
    expect(screen.queryByText("content")).toBeNull();
  });
});
