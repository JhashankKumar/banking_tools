"use client";

import { PageLayout } from "@/components/layout/PageLayout";
import {
  FilterBar,
  FilterSelect,
  SearchInput,
} from "@/components/ui/FilterBar";
import { KpiTiles } from "@/components/ui/KpiTiles";
import { Pagination } from "@/components/ui/Pagination";
import { QueryView } from "@/components/ui/QueryView";
import { AlertsTable } from "@/features/alerts/components/AlertsTable";
import { useAlertsPage } from "@/features/alerts/hooks/useAlertsPage";

export default function AlertsPage() {
  const p = useAlertsPage();
  return (
    <PageLayout
      title="Alerts"
      subtitle="Signals for analyst review — not findings of fraud. Produced by deterministic detection rules."
    >
      <KpiTiles
        tiles={
          p.kpis && [
            { label: "Open alerts", value: p.kpis.openAlerts, tone: "review" },
            { label: "Cases", value: p.kpis.cases },
            { label: "Active rules", value: p.kpis.activeRules },
            {
              label: "Rule set",
              value:
                p.rules.map((r) => `${r.code} v${r.version}`).join(", ") || "—",
            },
          ]
        }
      />
      <FilterBar>
        <SearchInput
          label="Search alerts"
          placeholder="Search alert, case, or party ID…"
          value={p.search}
          onChange={p.setSearch}
        />
        <FilterSelect
          label="Rule"
          value={p.ruleId}
          options={p.rules.map((r) => ({ value: r.id }))}
          onChange={p.setRuleId}
        />
        <FilterSelect
          label="Case"
          value={p.caseId}
          options={p.cases.map((c) => ({ value: c.id }))}
          onChange={p.setCaseId}
        />
      </FilterBar>
      <QueryView query={p.alerts} noun="Alerts" loading="Loading alerts">
        {(data) => (
          <>
            <AlertsTable alerts={p.rows} caseStatus={p.caseStatus} />
            <Pagination page={data.page} noun="alerts" onOffset={p.setOffset} />
          </>
        )}
      </QueryView>
    </PageLayout>
  );
}
