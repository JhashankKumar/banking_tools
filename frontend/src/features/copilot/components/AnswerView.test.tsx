import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test, vi } from "vitest";

import { ANSWER_JSON } from "@/test/fixtures";

import { copilotAnswerSchema } from "../schemas";
import { AnswerView } from "./AnswerView";

const answer = copilotAnswerSchema.parse(ANSWER_JSON);

describe("AnswerView", () => {
  test("EV chip is teal, TX chip is neutral record chip", () => {
    render(<AnswerView answer={answer} />);

    const [evidence] = screen.getAllByRole("button", {
      name: /EV-10482-TX-1001/,
    });
    const record = screen.getByRole("button", { name: /TX-9001/ });
    expect(evidence.querySelector("span")).toHaveClass("text-selected");
    expect(record.querySelector("span")).toHaveClass("text-muted");
    expect(record).toHaveAccessibleName("TX-9001, record outside the case");
  });

  test("clicking a citation selects its transaction", async () => {
    const onSelect = vi.fn();
    render(<AnswerView answer={answer} onSelectTransaction={onSelect} />);
    const user = userEvent.setup();

    const [evidence] = screen.getAllByRole("button", {
      name: /EV-10482-TX-1001/,
    });
    await user.click(evidence);
    await user.click(screen.getByRole("button", { name: /TX-9001/ }));

    expect(onSelect.mock.calls).toEqual([["TX-1001"], ["TX-9001"]]);
  });

  test("no save button unless allowed", () => {
    render(<AnswerView answer={answer} />);

    expect(
      screen.queryByRole("button", { name: "Save as case note" }),
    ).toBeNull();
  });
});
