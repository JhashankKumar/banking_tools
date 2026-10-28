import { Flag } from "lucide-react";
import type { ReactNode } from "react";

import { Chip } from "@/components/ui/Chip";
import { LinkRow, Table, Td, Th } from "@/components/ui/Table";
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
  return (
    <Table empty={alerts.length === 0 && "No alerts match these filters."}>
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
          const status = a.caseId ? caseStatus[a.caseId] : undefined;
          const cells = (id: ReactNode) => (
            <>
              <Td>
                <span className="flex items-center gap-2 font-mono whitespace-nowrap text-review">
                  <Flag aria-hidden size={14} />
                  {id}
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
            </>
          );
          // Alerts without a case have nowhere to open, so their rows are not links.
          return a.caseId ? (
            <LinkRow key={a.id} href={`/cases/${a.caseId}`} label={a.id}>
              {cells(<LinkRow.Link>{a.id}</LinkRow.Link>)}
            </LinkRow>
          ) : (
            <tr key={a.id} aria-label={a.id}>
              {cells(a.id)}
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
}
