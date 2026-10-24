import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { StatePanel } from "./StatePanel";

test("shows permission denied for 403", () => {
  render(
    <StatePanel
      kind="forbidden"
      title="You don't have access to this page"
      requestId="req-7"
    />,
  );

  expect(
    screen.getByRole("heading", { name: "You don't have access to this page" }),
  ).toBeInTheDocument();
  expect(screen.getByText(/req-7/)).toBeInTheDocument();
});

test("loading state is announced", () => {
  render(<StatePanel kind="loading" title="Loading alerts" />);

  expect(screen.getByRole("status")).toHaveTextContent("Loading alerts");
});
