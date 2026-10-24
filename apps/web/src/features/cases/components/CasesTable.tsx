"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { Chip } from "@/components/ui/Chip";
import { Table, Td, Th } from "@/components/ui/Table";
import { formatDateTime } from "@/lib/format";

import { CASE_STATUS_LABEL, type CaseSummary } from "../schemas";

export function CasesTable({ cases }: { cases: CaseSummary[] }) {
  const router = useRouter();
  if (cases.length === 0) {
    return (
      <p className="rounded-xl border border-line bg-surface p-8 text-center text-sm text-muted">
        No cases yet.
      </p>
    );
  }
  return (
    <Table>
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
          <tr
            key={c.id}
            aria-label={c.id}
            onClick={() => router.push(`/cases/${c.id}`)}
            className="cursor-pointer hover:bg-raised"
          >
            <Td className="font-mono font-semibold">
              <Link
                href={`/cases/${c.id}`}
                onClick={(e) => e.stopPropagation()}
                className="hover:underline"
              >
                {c.id}
              </Link>
            </Td>
            <Td>{c.title}</Td>
            <Td>
              <Chip tone="primary" outline>
                {CASE_STATUS_LABEL[c.status]}
              </Chip>
            </Td>
            <Td className="font-mono whitespace-nowrap">
              {formatDateTime(c.openedAt)}
            </Td>
            <Td className="text-right font-mono">{c.alertCount}</Td>
            <Td className="text-right font-mono">{c.transactionCount}</Td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
