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
import { AuditTable } from "@/features/audit/components/AuditTable";
import { useAuditPage } from "@/features/audit/hooks/useAuditPage";
import { OUTCOMES } from "@/features/audit/schemas";

export default function AuditPage() {
  const p = useAuditPage();
  return (
    <PageLayout
      title="Audit log"
      subtitle="Every sign-in, view, and change is recorded. Read-only."
    >
      <KpiTiles
        tiles={
          p.kpis && [
            { label: "Events on this page", value: p.kpis.events },
            { label: "Denied", value: p.kpis.denied, tone: "error" },
            {
              label: "Failed sign-ins",
              value: p.kpis.failedSignIns,
              tone: "review",
            },
            { label: "Detection runs", value: p.kpis.detectionRuns },
          ]
        }
      />
      <FilterBar>
        <SearchInput
          label="Search by request ID"
          placeholder="Search request ID…"
          value={p.search}
          onChange={p.setSearch}
          mono
        />
        <FilterSelect
          label="Action"
          value={p.action}
          options={p.actions.map((a) => ({ value: a }))}
          onChange={p.setAction}
        />
        <FilterSelect
          label="Outcome"
          value={p.outcome}
          options={OUTCOMES.map((o) => ({ value: o }))}
          onChange={p.setOutcome}
        />
      </FilterBar>
      <QueryView
        query={p.events}
        noun="Audit log"
        loading="Loading audit events"
      >
        {(data) => (
          <>
            <AuditTable events={p.rows} />
            <Pagination page={data.page} noun="events" onOffset={p.setOffset} />
          </>
        )}
      </QueryView>
    </PageLayout>
  );
}
