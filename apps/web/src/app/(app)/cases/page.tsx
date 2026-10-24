"use client";

import { useState } from "react";

import { PageHeader } from "@/components/layout/PageHeader";
import { QueryError } from "@/components/layout/QueryState";
import { Pagination } from "@/components/ui/Pagination";
import { StatePanel } from "@/components/ui/StatePanel";
import { CasesTable } from "@/features/cases/components/CasesTable";
import { useCasesList } from "@/features/cases/queries";

export default function CasesPage() {
  const [offset, setOffset] = useState(0);
  const cases = useCasesList({ limit: 50, offset });
  return (
    <div className="flex flex-col gap-5 px-8 pt-7 pb-9">
      <PageHeader
        title="Cases"
        subtitle="Investigation workspaces. Open a case to trace its money flow and evidence."
      />
      {cases.isPending ? (
        <StatePanel kind="loading" title="Loading cases" />
      ) : cases.isError ? (
        <QueryError error={cases.error} noun="Cases" />
      ) : (
        <>
          <CasesTable cases={cases.data.items} />
          <Pagination
            page={cases.data.page}
            noun="cases"
            onOffset={setOffset}
          />
        </>
      )}
    </div>
  );
}
