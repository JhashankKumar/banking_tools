import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { CASE_SUMMARY_JSON } from "@/test/fixtures";

import { caseSummarySchema } from "../schemas";
import { CasesTable } from "./CasesTable";

vi.mock("next/navigation", () => import("@/test/next-navigation"));

test("CasesTable renders counts and links", () => {
  render(<CasesTable cases={[caseSummarySchema.parse(CASE_SUMMARY_JSON)]} />);

  const row = screen.getByRole("row", { name: /FR-10482/ });
  expect(row).toHaveTextContent("Open");
  expect(row).toHaveTextContent("15 Sep 2026, 10:30:00 IST");
  expect(screen.getByRole("link", { name: "FR-10482" })).toHaveAttribute(
    "href",
    "/cases/FR-10482",
  );
  expect(row.textContent).toMatch(/1.*2/);
});
