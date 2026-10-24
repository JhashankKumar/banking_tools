"use client";

import { useMemo, useState } from "react";

import { useAuditEvents } from "../queries";
import { KNOWN_ACTIONS, type Outcome } from "../schemas";

const PAGE_SIZE = 50;

export function useAuditPage() {
  const [action, setAction] = useState<string | undefined>();
  const [outcome, setOutcome] = useState<Outcome | undefined>();
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const events = useAuditEvents({ limit: PAGE_SIZE, offset, action });
  const items = useMemo(() => events.data?.items ?? [], [events.data]);

  // Outcome and request-ID search filter the loaded page only; the API has no such params.
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
    page: events.data?.page,
    kpis,
    actions,
    action,
    outcome,
    search,
    setAction: (v: string | undefined) => {
      setAction(v);
      setOffset(0);
    },
    setOutcome,
    setSearch,
    setOffset,
  };
}
