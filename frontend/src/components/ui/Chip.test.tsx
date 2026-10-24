import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { Chip } from "./Chip";

describe("Chip", () => {
  // Tone text on bg-raised is 4.46:1 for review and success, under WCAG AA 4.5:1.
  test.each(["review", "success", "selected", "error"] as const)(
    "filled %s chip sits on the surface colour for AA contrast",
    (tone) => {
      render(<Chip tone={tone}>label</Chip>);

      expect(screen.getByText("label")).toHaveClass("bg-surface");
      expect(screen.getByText("label")).not.toHaveClass("bg-raised");
    },
  );

  test("filled neutral chip keeps the raised fill", () => {
    render(<Chip>label</Chip>);

    expect(screen.getByText("label")).toHaveClass("bg-raised");
  });
});
