import { Check, Lock, X } from "lucide-react";

import { StatusChip, type StatusStyles } from "@/components/ui/StatusChip";
import { Table, Td, Th } from "@/components/ui/Table";
import { formatDateTime } from "@/lib/format";

import { actorLabel, type AuditEvent, type Outcome } from "../schemas";

const OUTCOME_STYLES: StatusStyles<Outcome> = {
  success: { tone: "success", icon: Check },
  denied: { tone: "error", icon: Lock },
  failure: { tone: "review", icon: X },
};

export function AuditTable({ events }: { events: AuditEvent[] }) {
  return (
    <Table
      empty={events.length === 0 && "No audit events match these filters."}
    >
      <thead>
        <tr>
          <Th>Time (IST)</Th>
          <Th>Actor</Th>
          <Th>Action</Th>
          <Th>Resource</Th>
          <Th>Outcome</Th>
          <Th>Request ID</Th>
        </tr>
      </thead>
      <tbody>
        {events.map((e) => {
          const actor = actorLabel(e);
          return (
            <tr key={e.id} aria-label={`Event ${e.id}`}>
              <Td className="font-mono whitespace-nowrap">
                {formatDateTime(e.occurredAt)}
              </Td>
              <Td
                className={
                  e.actorUsername ? "font-mono" : "font-mono text-muted italic"
                }
              >
                {actor}
              </Td>
              <Td className="font-mono">{e.action}</Td>
              <Td className="font-mono text-muted">
                {e.resourceType
                  ? `${e.resourceType}${e.resourceId ? ` ${e.resourceId}` : ""}`
                  : "—"}
              </Td>
              <Td>
                <span data-outcome={e.outcome}>
                  <StatusChip
                    value={e.outcome}
                    styles={OUTCOME_STYLES}
                    outline
                  />
                </span>
              </Td>
              <Td className="font-mono text-muted">{e.requestId ?? "—"}</Td>
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
}
