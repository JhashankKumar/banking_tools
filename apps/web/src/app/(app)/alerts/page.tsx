"use client";

import { Search } from "lucide-react";

import { PageHeader } from "@/components/layout/PageHeader";
import { QueryError } from "@/components/layout/QueryState";
import { Pagination } from "@/components/ui/Pagination";
import { StatePanel } from "@/components/ui/StatePanel";
import { AlertsTable } from "@/features/alerts/components/AlertsTable";
import { KpiTiles } from "@/features/alerts/components/KpiTiles";
import { useAlertsPage } from "@/features/alerts/hooks/useAlertsPage";

const selectClass =
  "rounded-full border border-line bg-surface px-3 py-1 text-xs text-ink";

export default function AlertsPage() {
  const p = useAlertsPage();
  return (
    <div className="flex flex-col gap-5 px-8 pt-7 pb-9">
      <PageHeader
        title="Alerts"
        subtitle="Signals for analyst review — not findings of fraud. Produced by deterministic detection rules."
      />
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
      <div className="flex items-center gap-2.5">
        <label className="flex w-80 items-center gap-2 rounded-lg border border-line bg-surface px-3 py-2">
          <Search aria-hidden size={14} className="text-muted" />
          <span className="sr-only">Search alerts</span>
          <input
            value={p.search}
            onChange={(e) => p.setSearch(e.target.value)}
            placeholder="Search alert, case, or party ID…"
            className="w-full bg-transparent text-xs text-ink outline-none placeholder:text-muted"
          />
        </label>
        <select
          aria-label="Rule"
          className={selectClass}
          value={p.ruleId ?? ""}
          onChange={(e) => p.setRuleId(e.target.value || undefined)}
        >
          <option value="">Rule: all</option>
          {p.rules.map((r) => (
            <option key={r.id} value={r.id}>
              {r.id}
            </option>
          ))}
        </select>
        <select
          aria-label="Case"
          className={selectClass}
          value={p.caseId ?? ""}
          onChange={(e) => p.setCaseId(e.target.value || undefined)}
        >
          <option value="">Case: all</option>
          {p.cases.map((c) => (
            <option key={c.id} value={c.id}>
              {c.id}
            </option>
          ))}
        </select>
      </div>
      {p.alerts.isPending ? (
        <StatePanel kind="loading" title="Loading alerts" />
      ) : p.alerts.isError ? (
        <QueryError error={p.alerts.error} noun="Alerts" />
      ) : (
        <>
          <AlertsTable alerts={p.rows} caseStatus={p.caseStatus} />
          {p.page && (
            <Pagination page={p.page} noun="alerts" onOffset={p.setOffset} />
          )}
        </>
      )}
    </div>
  );
}
