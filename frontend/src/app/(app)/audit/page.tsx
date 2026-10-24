"use client";

import { Search } from "lucide-react";

import { PageHeader } from "@/components/layout/PageHeader";
import { QueryError } from "@/components/ui/QueryError";
import { Pagination } from "@/components/ui/Pagination";
import { StatePanel } from "@/components/ui/StatePanel";
import { KpiTiles } from "@/components/ui/KpiTiles";
import { AuditTable } from "@/features/audit/components/AuditTable";
import { useAuditPage } from "@/features/audit/hooks/useAuditPage";
import { OUTCOMES, type Outcome } from "@/features/audit/schemas";

const selectClass =
  "rounded-full border border-line bg-surface px-3 py-1 text-xs text-ink";

export default function AuditPage() {
  const p = useAuditPage();
  return (
    <div className="flex flex-col gap-5 px-8 pt-7 pb-9">
      <PageHeader
        title="Audit log"
        subtitle="Every sign-in, view, and change is recorded. Read-only."
      />
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
      <div className="flex items-center gap-2.5">
        <label className="flex w-80 items-center gap-2 rounded-lg border border-line bg-surface px-3 py-2">
          <Search aria-hidden size={14} className="text-muted" />
          <span className="sr-only">Search by request ID</span>
          <input
            value={p.search}
            onChange={(e) => p.setSearch(e.target.value)}
            placeholder="Search request ID…"
            className="w-full bg-transparent font-mono text-xs text-ink outline-none placeholder:font-sans placeholder:text-muted"
          />
        </label>
        <select
          aria-label="Action"
          className={selectClass}
          value={p.action ?? ""}
          onChange={(e) => p.setAction(e.target.value || undefined)}
        >
          <option value="">Action: all</option>
          {p.actions.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
        <select
          aria-label="Outcome"
          className={selectClass}
          value={p.outcome ?? ""}
          onChange={(e) =>
            p.setOutcome((e.target.value || undefined) as Outcome | undefined)
          }
        >
          <option value="">Outcome: all</option>
          {OUTCOMES.map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
      </div>
      {p.events.isPending ? (
        <StatePanel kind="loading" title="Loading audit events" />
      ) : p.events.isError ? (
        <QueryError error={p.events.error} noun="Audit log" />
      ) : (
        <>
          <AuditTable events={p.rows} />
          {p.page && (
            <Pagination page={p.page} noun="events" onOffset={p.setOffset} />
          )}
        </>
      )}
    </div>
  );
}
