import { act, renderHook } from "@testing-library/react";
import { expect, test } from "vitest";

import { useListFilters } from "./use-list-filters";

test("changing a filter goes back to the first page", () => {
  const { result } = renderHook(() => useListFilters<{ ruleId?: string }>({}));

  act(() => result.current.setOffset(50));
  expect(result.current.offset).toBe(50);

  act(() => result.current.setFilter("ruleId", "R1"));

  expect(result.current.filters).toEqual({ ruleId: "R1" });
  expect(result.current.offset).toBe(0);
  expect(result.current.limit).toBe(50);
});
