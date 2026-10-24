"use client";

import { Flag, Sparkles } from "lucide-react";
import Link from "next/link";

import { QueryView } from "@/components/ui/QueryView";
import { CopilotPanel } from "@/features/copilot/components/CopilotPanel";
import { MoneyFlowCard } from "@/features/money-flow/components/MoneyFlowCard";
import { DATASET_LIMITATION } from "@/features/money-flow/schemas";

import {
  CaseSelectionProvider,
  useCaseSelection,
} from "../hooks/useCaseSelection";
import { useCasePage, type CasePageData } from "../hooks/useCasePage";
import { CaseHeader } from "./CaseHeader";
import { CollapsibleColumn } from "./CollapsibleColumn";
import { EvidenceCard, type EvidenceItem } from "./EvidenceCard";
import { LimitationsCard } from "./LimitationsCard";
import { TimelineCard } from "./TimelineCard";
import { WhyItFiredCard } from "./WhyItFiredCard";

export function CasePage({ caseId }: { caseId: string }) {
  const data = useCasePage(caseId);
  return (
    <QueryView
      query={data.caseQuery}
      noun="Case"
      loading="Loading case"
      notFound={{
        message: `No case with ID ${caseId}.`,
        action: (
          <Link href="/cases" className="text-sm font-medium text-primary">
            Back to cases
          </Link>
        ),
      }}
    >
      {(caseData) => (
        <CaseSelectionProvider
          pathCount={data.moneyPathsQuery.data?.paths.length ?? 0}
        >
          <CaseHeader data={caseData} />
          <CaseBody caseId={caseId} data={data} />
        </CaseSelectionProvider>
      )}
    </QueryView>
  );
}

function CaseBody({ caseId, data }: { caseId: string; data: CasePageData }) {
  const selection = useCaseSelection();
  const alerts = data.alertsQuery.data?.items ?? [];
  const transactions = data.transactionsQuery.data?.items ?? [];
  const paths = data.moneyPathsQuery.data?.paths ?? [];
  const selectedPath =
    selection.selectedPathIndex === null
      ? null
      : paths[selection.selectedPathIndex];
  const evidence: EvidenceItem[] = [
    ...alerts.flatMap((a) =>
      a.evidenceId ? [{ id: a.evidenceId, label: "indicator" as const }] : [],
    ),
    ...transactions.flatMap((t) =>
      t.evidenceId
        ? [
            {
              id: t.evidenceId,
              label: "observed fact" as const,
              transactionId: t.id,
            },
          ]
        : [],
    ),
  ].sort((a, b) => a.id.localeCompare(b.id));

  return (
    <div className="flex gap-4 px-6 pb-7">
      <CollapsibleColumn
        side="left"
        label="case context"
        railIcon={<Flag aria-hidden size={18} className="text-review" />}
        open={selection.leftOpen}
        onToggle={selection.setLeftOpen}
        width="w-80"
      >
        {alerts.map((a) => (
          <WhyItFiredCard
            key={a.id}
            alert={a}
            rule={data.rulesQuery.data?.find((r) => r.id === a.rule.id)}
          />
        ))}
        <EvidenceCard items={evidence} onSelect={selection.selectTransaction} />
        <LimitationsCard
          items={selectedPath?.limitations ?? [DATASET_LIMITATION]}
        />
      </CollapsibleColumn>
      <div className="flex min-w-0 flex-1 flex-col gap-4">
        <MoneyFlowCard data={data} />
        <QueryView
          query={data.transactionsQuery}
          noun="Transactions"
          loading="Loading transactions"
        >
          {(page) => (
            <TimelineCard
              transactions={page.items}
              page={page.page}
              selectedId={selection.selectedTransactionId}
              onSelect={selection.selectTransaction}
              onOffset={data.setTxOffset}
            />
          )}
        </QueryView>
      </div>
      <CollapsibleColumn
        side="right"
        label="AI copilot"
        railIcon={<Sparkles aria-hidden size={18} className="text-primary" />}
        open={selection.rightOpen}
        onToggle={selection.setRightOpen}
        width="w-[360px]"
      >
        <CopilotPanel caseId={caseId} />
      </CollapsibleColumn>
    </div>
  );
}
