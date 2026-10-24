"use client";

import { Flag } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Chip } from "@/components/ui/Chip";
import { Table, Td, Th } from "@/components/ui/Table";
import { CASE_STATUS_LABEL, type CaseStatus } from "@/features/cases/schemas";
import { formatDateTime } from "@/lib/format";

import type { Alert } from "../schemas";

export function AlertsTable({
  alerts,
  caseStatus,
}: {
  alerts: Alert[];
  caseStatus: Record<string, CaseStatus>;
}) {
  const router = useRouter();
  if (alerts.length === 0) {
    return (
      <p className="rounded-xl border border-line bg-surface p-8 text-center text-sm text-muted">
        No alerts match these filters.
      </p>
    );
  }
  return (
    <Table>
      <thead>
        <tr>
          <Th>Alert</Th>
          <Th>Rule</Th>
          <Th>Party</Th>
          <Th>Triggered (IST)</Th>
          <Th>Case</Th>
          <Th>Why it fired</Th>
        </tr>
      </thead>
      <tbody>
        {alerts.map((a) => {
          const href = a.caseId ? `/cases/${a.caseId}` : null;
          const status = a.caseId ? caseStatus[a.caseId] : undefined;
          return (
            <tr
              key={a.id}
              aria-label={a.id}
              onClick={() => href && router.push(href)}
              className={href ? "cursor-pointer hover:bg-raised" : undefined}
            >
              <Td>
                <span className="flex items-center gap-2 font-mono whitespace-nowrap text-review">
                  <Flag aria-hidden size={14} />
                  {href ? (
                    <Link
                      href={href}
                      onClick={(e) => e.stopPropagation()}
                      className="hover:underline"
                    >
                      {a.id}
                    </Link>
                  ) : (
                    a.id
                  )}
                </span>
              </Td>
              <Td>
                <Chip mono>{`${a.rule.id} v${a.rule.version}`}</Chip>
              </Td>
              <Td className="font-mono whitespace-nowrap">{a.entity.id}</Td>
              <Td className="font-mono whitespace-nowrap">
                {formatDateTime(a.triggeredAt)}
              </Td>
              <Td>
                {a.caseId ? (
                  <Chip tone="primary" outline mono>
                    {status
                      ? `${a.caseId} · ${CASE_STATUS_LABEL[status]}`
                      : a.caseId}
                  </Chip>
                ) : (
                  <span className="text-muted">No case</span>
                )}
              </Td>
              <Td className="text-muted">{a.explanation}</Td>
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
}
