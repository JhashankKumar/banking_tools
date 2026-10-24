import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test, vi } from "vitest";

import { FilterSelect, SearchInput } from "./FilterBar";

describe("FilterSelect", () => {
  test("offers an 'all' option and reports undefined for it", async () => {
    const onChange = vi.fn();
    render(
      <FilterSelect
        label="Rule"
        value="R1"
        options={[{ value: "R1" }, { value: "R2", label: "Rule two" }]}
        onChange={onChange}
      />,
    );
    const select = screen.getByRole("combobox", { name: "Rule" });

    expect(
      screen.getByRole("option", { name: "Rule: all" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: "Rule two" }),
    ).toBeInTheDocument();
    await userEvent.setup().selectOptions(select, "Rule: all");

    expect(onChange).toHaveBeenLastCalledWith(undefined);
  });
});

describe("SearchInput", () => {
  test("is labelled and reports typed text", async () => {
    const onChange = vi.fn();
    render(
      <SearchInput
        label="Search alerts"
        placeholder="Search…"
        value=""
        onChange={onChange}
      />,
    );

    await userEvent
      .setup()
      .type(screen.getByRole("textbox", { name: "Search alerts" }), "a");

    expect(onChange).toHaveBeenCalledWith("a");
  });
});
