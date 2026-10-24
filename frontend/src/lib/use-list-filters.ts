"use client";

import { useState } from "react";

import { LIST_PAGE_SIZE } from "./config";

/**
 * Server-side list filters plus paging: changing any filter returns to the first page, so a
 * filtered list never opens on an offset past its end.
 */
export function useListFilters<F extends Record<string, unknown>>(initial: F) {
  const [filters, setFilters] = useState(initial);
  const [offset, setOffset] = useState(0);
  const setFilter = <K extends keyof F>(key: K, value: F[K]) => {
    setFilters((current) => ({ ...current, [key]: value }));
    setOffset(0);
  };
  return { filters, setFilter, offset, setOffset, limit: LIST_PAGE_SIZE };
}
