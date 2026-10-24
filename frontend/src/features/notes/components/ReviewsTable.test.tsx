import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { REVIEW_QUEUE_JSON } from "@/test/fixtures";

import { reviewQueueItemSchema } from "../schemas";
import { ReviewsTable } from "./ReviewsTable";

vi.mock("next/navigation", () => import("@/test/next-navigation"));

test("reviews table links to case", () => {
  render(
    <ReviewsTable items={[reviewQueueItemSchema.parse(REVIEW_QUEUE_JSON)]} />,
  );

  const row = screen.getByRole("row", { name: /FR-10482/ });
  expect(row).toHaveTextContent("analyst.demo");
  expect(row).toHaveTextContent("24 Oct 2026, 11:55:00 IST");
  expect(screen.getByRole("link", { name: "FR-10482" })).toHaveAttribute(
    "href",
    "/cases/FR-10482",
  );
});

test("empty queue message", () => {
  render(<ReviewsTable items={[]} />);

  expect(
    screen.getByText("No notes are waiting for your review."),
  ).toBeVisible();
});
