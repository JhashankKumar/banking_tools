import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import Page from "./page";

test("home page shows product name, tagline, and synthetic-data notice", () => {
  render(<Page />);

  expect(
    screen.getByRole("heading", { level: 1, name: "OpenFraud Investigator" }),
  ).toBeDefined();
  expect(
    screen.getByText(
      "Trace the money. Connect the evidence. Investigate with AI.",
    ),
  ).toBeDefined();
  expect(screen.getByText(/synthetic data only/i)).toBeDefined();
});
