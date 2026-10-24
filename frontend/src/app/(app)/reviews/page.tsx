"use client";

import { PageLayout } from "@/components/layout/PageLayout";
import { Pagination } from "@/components/ui/Pagination";
import { QueryView } from "@/components/ui/QueryView";
import { ReviewsTable } from "@/features/notes/components/ReviewsTable";
import { useReviewQueue } from "@/features/notes/queries";
import { useListFilters } from "@/lib/use-list-filters";

export default function ReviewsPage() {
  const list = useListFilters({});
  const queue = useReviewQueue({ limit: list.limit, offset: list.offset });
  return (
    <PageLayout
      title="Awaiting review"
      subtitle="Case notes submitted by analysts. You can't review your own notes."
    >
      <QueryView
        query={queue}
        noun="Reviews"
        loading="Loading notes awaiting review"
      >
        {(data) => (
          <>
            <ReviewsTable items={data.items} />
            <Pagination
              page={data.page}
              noun="notes"
              order="oldest first"
              onOffset={list.setOffset}
            />
          </>
        )}
      </QueryView>
    </PageLayout>
  );
}
