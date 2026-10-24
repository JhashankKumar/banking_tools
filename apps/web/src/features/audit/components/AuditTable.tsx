import { Check, Lock, X } from "lucide-react";

import { Chip, type Tone } from "@/components/ui/Chip";
import { Table, Td, Th } from "@/components/ui/Table";
import { formatDateTime } from "@/lib/format";

import { actorLabel, type AuditEvent, type Outcome } from "../schemas";

const OUTCOME_STYLE: Record<Outcome, { tone: Tone; icon: typeof Check }> = {
  success: { tone: "success", icon: Check },
  denied: { tone: "error", icon: Lock },
  failure: { tone: "review", icon: X },
};

export function AuditTable({ events }: { events: AuditEvent[] }) {
  if (events.length === 0) {
    return (
      <p className="rounded-xl border border-line bg-surface p-8 text-center text-sm text-muted">
        No audit events match these filters.
      </p>
    );
  }
  return (
    <Table>
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
          const { tone, icon: Icon } = OUTCOME_STYLE[e.outcome];
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
                  <Chip
                    tone={tone}
                    outline
                    icon={<Icon aria-hidden size={12} />}
                  >
                    {e.outcome}
                  </Chip>
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
