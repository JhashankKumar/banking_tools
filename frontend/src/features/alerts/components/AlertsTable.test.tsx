import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test, vi } from "vitest";

import { ALERT_JSON } from "@/test/fixtures";
import { router } from "@/test/next-navigation";

import { alertSchema } from "../schemas";
import { AlertsTable } from "./AlertsTable";

vi.mock("next/navigation", () => import("@/test/next-navigation"));

const alert = alertSchema.parse(ALERT_JSON);

describe("AlertsTable", () => {
  test("renders AL-ROT-TX-1002 row with IST time", () => {
    render(
      <AlertsTable alerts={[alert]} caseStatus={{ "FR-10482": "open" }} />,
    );

    const row = screen.getByRole("row", { name: /AL-ROT-TX-1002/ });
    expect(row).toHaveTextContent("RAPID_ONWARD_TRANSFER v2");
    expect(row).toHaveTextContent("BEN-B");
    expect(row).toHaveTextContent("15 Sep 2026, 10:07:42 IST");
    expect(row).toHaveTextContent("FR-10482 · Open");
    expect(row).toHaveTextContent("not a finding of fraud");
  });

  test("row click navigates to case", async () => {
    render(<AlertsTable alerts={[alert]} caseStatus={{}} />);

    await userEvent
      .setup()
      .click(screen.getByRole("row", { name: /AL-ROT-TX-1002/ }));

    expect(router.push).toHaveBeenCalledWith("/cases/FR-10482");
  });

  test("alert ID links to its case for keyboard users", () => {
    render(<AlertsTable alerts={[alert]} caseStatus={{}} />);

    expect(
      screen.getByRole("link", { name: "AL-ROT-TX-1002" }),
    ).toHaveAttribute("href", "/cases/FR-10482");
  });

  test("empty state when no rows", () => {
    render(<AlertsTable alerts={[]} caseStatus={{}} />);

    expect(
      screen.getByText("No alerts match these filters."),
    ).toBeInTheDocument();
  });
});
