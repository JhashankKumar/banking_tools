import type { PageMeta } from "@/lib/schemas";

import { Button } from "./Button";

export function Pagination({
  page,
  noun,
  order = "newest first",
  onOffset,
}: {
  page: PageMeta;
  noun: string;
  /** How the API sorts this list, shown after the count. */
  order?: string;
  onOffset: (o: number) => void;
}) {
  const first = page.total === 0 ? 0 : page.offset + 1;
  const last = Math.min(page.offset + page.limit, page.total);
  return (
    <nav aria-label="Pagination" className="flex items-center gap-2.5">
      <p className="text-xs text-muted">
        {first}–{last} of {page.total} {noun} · {order}
      </p>
      <Button
        className="ml-auto px-2.5 py-1 text-xs"
        disabled={page.offset === 0}
        onClick={() => onOffset(Math.max(page.offset - page.limit, 0))}
      >
        ‹ Prev
      </Button>
      <Button
        className="px-2.5 py-1 text-xs"
        disabled={page.offset + page.limit >= page.total}
        onClick={() => onOffset(page.offset + page.limit)}
      >
        Next ›
      </Button>
    </nav>
  );
}
