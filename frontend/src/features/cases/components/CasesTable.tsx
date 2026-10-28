import { LinkRow, Table, Td, Th } from "@/components/ui/Table";
import { formatDateTime } from "@/lib/format";

import type { CaseSummary } from "../schemas";
import { CaseStatusChip } from "./CaseStatusChip";

export function CasesTable({ cases }: { cases: CaseSummary[] }) {
  return (
    <Table empty={cases.length === 0 && "No cases yet."}>
      <thead>
        <tr>
          <Th>Case</Th>
          <Th>Title</Th>
          <Th>Status</Th>
          <Th>Opened (IST)</Th>
          <Th className="text-right">Alerts</Th>
          <Th className="text-right">Transactions</Th>
        </tr>
      </thead>
      <tbody>
        {cases.map((c) => (
          <LinkRow key={c.id} href={`/cases/${c.id}`} label={c.id}>
            <Td className="font-mono font-semibold">
              <LinkRow.Link>{c.id}</LinkRow.Link>
            </Td>
            <Td>{c.title}</Td>
            <Td>
              <CaseStatusChip status={c.status} />
            </Td>
            <Td className="font-mono whitespace-nowrap">
              {formatDateTime(c.openedAt)}
            </Td>
            <Td className="text-right font-mono">{c.alertCount}</Td>
            <Td className="text-right font-mono">{c.transactionCount}</Td>
          </LinkRow>
        ))}
      </tbody>
    </Table>
  );
}
