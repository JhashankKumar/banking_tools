"use client";

import { useMemo, useState } from "react";

import { useListFilters } from "@/lib/use-list-filters";

import { useAuditEvents } from "../queries";
import { KNOWN_ACTIONS, type Outcome } from "../schemas";

export function useAuditPage() {
  const list = useListFilters<{ action?: string }>({});
  // Outcome and request-ID search filter the loaded page only; the API has no such params.
  const [outcome, setOutcome] = useState<Outcome | undefined>();
  const [search, setSearch] = useState("");
  const events = useAuditEvents({
    limit: list.limit,
    offset: list.offset,
    ...list.filters,
  });
  const items = useMemo(() => events.data?.items ?? [], [events.data]);

  const rows = useMemo(() => {
    const q = search.trim().toLowerCase();
    return items.filter(
      (e) =>
        (!outcome || e.outcome === outcome) &&
        (!q || (e.requestId ?? "").toLowerCase().includes(q)),
    );
  }, [items, outcome, search]);

  const actions = useMemo(
    () => [...new Set([...KNOWN_ACTIONS, ...items.map((e) => e.action)])],
    [items],
  );

  const kpis = events.data
    ? {
        events: items.length,
        denied: items.filter((e) => e.outcome === "denied").length,
        failedSignIns: items.filter((e) => e.action === "auth.login.failed")
          .length,
        detectionRuns: items.filter((e) => e.action === "detection.run").length,
      }
    : null;

  return {
    events,
    rows,
    kpis,
    actions,
    action: list.filters.action,
    outcome,
    search,
    setAction: (v: string | undefined) => list.setFilter("action", v),
    setOutcome,
    setSearch,
    setOffset: list.setOffset,
  };
}
