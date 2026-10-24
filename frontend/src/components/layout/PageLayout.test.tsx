import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { PageLayout } from "./PageLayout";

test("PageLayout renders the page heading, subtitle, action and content", () => {
  render(
    <PageLayout
      title="Users"
      subtitle="Manage access."
      action={<button>New</button>}
    >
      <p>table</p>
    </PageLayout>,
  );

  expect(
    screen.getByRole("heading", { level: 1, name: "Users" }),
  ).toBeVisible();
  expect(screen.getByText("Manage access.")).toBeVisible();
  expect(screen.getByRole("button", { name: "New" })).toBeVisible();
  expect(screen.getByText("table")).toBeVisible();
});
