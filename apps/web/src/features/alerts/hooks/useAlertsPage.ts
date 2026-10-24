"use client";

import { useMemo, useState } from "react";

import { useCasesList } from "@/features/cases/queries";
import type { CaseStatus } from "@/features/cases/schemas";
import { useRules } from "@/features/rules/queries";

import { useAlerts } from "../queries";

const PAGE_SIZE = 50;

export function useAlertsPage() {
  const [ruleId, setRuleId] = useState<string | undefined>();
  const [caseId, setCaseId] = useState<string | undefined>();
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const alerts = useAlerts({ limit: PAGE_SIZE, offset, ruleId, caseId });
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
    page: alerts.data?.page,
    kpis,
    caseStatus,
    cases: cases.data?.items ?? [],
    rules: rules.data ?? [],
    ruleId,
    caseId,
    search,
    setRuleId: (v: string | undefined) => {
      setRuleId(v);
      setOffset(0);
    },
    setCaseId: (v: string | undefined) => {
      setCaseId(v);
      setOffset(0);
    },
    setSearch,
    setOffset,
  };
}
