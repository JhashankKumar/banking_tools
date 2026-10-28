import { render, screen } from "@testing-library/react";
import { Check, X } from "lucide-react";
import { describe, expect, test } from "vitest";

import { StatusChip, type StatusStyles } from "./StatusChip";

const STYLES: StatusStyles<"ok" | "bad"> = {
  ok: { tone: "success", icon: Check, label: "All good" },
  bad: { tone: "error", icon: X },
};

describe("StatusChip", () => {
  test("shows icon and label, never colour alone", () => {
    render(<StatusChip value="ok" styles={STYLES} />);

    const chip = screen.getByText("All good");
    expect(chip).toHaveClass("text-success");
    expect(chip.querySelector("svg")).not.toBeNull();
  });

  test("falls back to the raw value as label", () => {
    render(<StatusChip value="bad" styles={STYLES} />);

    expect(screen.getByText("bad")).toHaveClass("text-error");
  });
});
