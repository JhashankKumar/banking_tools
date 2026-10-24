"use client";

import { useMemo, useState } from "react";

import { useCasesList } from "@/features/cases/queries";
import type { CaseStatus } from "@/features/cases/schemas";
import { useRules } from "@/features/rules/queries";
import { useListFilters } from "@/lib/use-list-filters";

import { useAlerts } from "../queries";

export function useAlertsPage() {
  const list = useListFilters<{ ruleId?: string; caseId?: string }>({});
  const [search, setSearch] = useState("");
  const alerts = useAlerts({
    limit: list.limit,
    offset: list.offset,
    ...list.filters,
  });
  const cases = useCasesList({ limit: 100, offset: 0 });
  const rules = useRules();

  const rows = useMemo(() => {
    const items = alerts.data?.items ?? [];
    const q = search.trim().toLowerCase();
    if (!q) return items;
    return items.filter((a) =>
      [a.id, a.caseId ?? "", a.entity.id, a.triggerTransactionId].some((v) =>
        v.toLowerCase().includes(q),
      ),
    );
  }, [alerts.data, search]);

  const caseStatus = useMemo(
    () =>
      Object.fromEntries(
        (cases.data?.items ?? []).map((c) => [c.id, c.status]),
      ) as Record<string, CaseStatus>,
    [cases.data],
  );

  const kpis =
    alerts.data && cases.data && rules.data
      ? {
          openAlerts: alerts.data.page.total,
          cases: cases.data.page.total,
          activeRules: rules.data.length,
        }
      : null;

  return {
    alerts,
    rows,
    kpis,
    caseStatus,
    cases: cases.data?.items ?? [],
    rules: rules.data ?? [],
    ruleId: list.filters.ruleId,
    caseId: list.filters.caseId,
    search,
    setRuleId: (v: string | undefined) => list.setFilter("ruleId", v),
    setCaseId: (v: string | undefined) => list.setFilter("caseId", v),
    setSearch,
    setOffset: list.setOffset,
  };
}
