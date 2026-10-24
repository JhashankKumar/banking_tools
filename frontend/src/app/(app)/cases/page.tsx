"use client";

import { PageLayout } from "@/components/layout/PageLayout";
import { Pagination } from "@/components/ui/Pagination";
import { QueryView } from "@/components/ui/QueryView";
import { CasesTable } from "@/features/cases/components/CasesTable";
import { useCasesList } from "@/features/cases/queries";
import { useListFilters } from "@/lib/use-list-filters";

export default function CasesPage() {
  const list = useListFilters({});
  const cases = useCasesList({ limit: list.limit, offset: list.offset });
  return (
    <PageLayout
      title="Cases"
      subtitle="Investigation workspaces. Open a case to trace its money flow and evidence."
    >
      <QueryView query={cases} noun="Cases" loading="Loading cases">
        {(data) => (
          <>
            <CasesTable cases={data.items} />
            <Pagination
              page={data.page}
              noun="cases"
              onOffset={list.setOffset}
            />
          </>
        )}
      </QueryView>
    </PageLayout>
  );
}
