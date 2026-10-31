import { Check, Circle, MinusCircle, X } from "lucide-react";

import { StatusChip, type StatusStyles } from "@/components/ui/StatusChip";
import { Table, Td, Th } from "@/components/ui/Table";

import {
  CATEGORY_ORDER,
  type CheckStatus,
  type SafetyCheck,
  type SafetyResult,
} from "../schemas";

type RowStatus = CheckStatus | "not_run";

const STATUS_STYLES: StatusStyles<RowStatus> = {
  passed: { tone: "success", icon: Check, label: "Passed" },
  failed: { tone: "error", icon: X, label: "Failed" },
  skipped: { tone: "review", icon: MinusCircle, label: "Skipped" },
  not_run: { tone: "neutral", icon: Circle, label: "Not run yet" },
};

type Row = SafetyCheck & { status: RowStatus; observed: string | null };

function rows(checks: SafetyCheck[], results: SafetyResult[] | null): Row[] {
  const byId = new Map(results?.map((r) => [r.id, r]));
  return checks.map((c) => {
    const r = byId.get(c.id);
    return {
      ...c,
      status: r?.status ?? "not_run",
      observed: r?.observed ?? null,
    };
  });
}

/** Failed first, then the catalogue's own order. */
const failedFirst = (a: Row, b: Row) =>
  Number(b.status === "failed") - Number(a.status === "failed");

export function SafetyResults({
  checks,
  results,
}: {
  checks: SafetyCheck[];
  results: SafetyResult[] | null;
}) {
  const all = rows(checks, results);
  return (
    <div className="flex flex-col gap-5">
      {CATEGORY_ORDER.map((category) => {
        const group = all
          .filter((r) => r.category === category)
          .sort(failedFirst);
        if (group.length === 0) return null;
        const headingId = `safety-${category.replace(/\W+/g, "-").toLowerCase()}`;
        return (
          <section
            key={category}
            aria-labelledby={headingId}
            className="flex flex-col gap-2"
          >
            <h2 id={headingId} className="text-sm font-semibold text-ink">
              {category}
            </h2>
            <Table>
              <thead>
                <tr>
                  <Th className="w-20">Check</Th>
                  <Th>Attack</Th>
                  <Th>Defence</Th>
                  <Th className="w-28">Result</Th>
                  <Th>What happened</Th>
                </tr>
              </thead>
              <tbody>
                {group.map((r) => (
                  <tr key={r.id} aria-label={r.id}>
                    <Td className="font-mono">{r.id}</Td>
                    <Td>{r.attack}</Td>
                    <Td className="text-muted">{r.defence}</Td>
                    <Td>
                      <StatusChip
                        value={r.status}
                        styles={STATUS_STYLES}
                        outline
                      />
                    </Td>
                    <Td className={r.observed ? undefined : "text-muted"}>
                      {r.observed ?? "—"}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </section>
        );
      })}
    </div>
  );
}
