import type { UseQueryResult } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { QueryError, type NotFoundOptions } from "./QueryError";
import { StatePanel } from "./StatePanel";

/**
 * Loading → error → (empty) → content for one query, so every data view handles each state the
 * same way: 403 is permission denied, 404 is not found, anything else an error with request ID.
 */
export function QueryView<T>({
  query,
  noun,
  loading,
  empty,
  notFound,
  children,
}: {
  query: UseQueryResult<T>;
  /** Names the data in error titles, e.g. "Cases" → "Could not load cases". */
  noun: string;
  /** Screen-reader title of the loading skeleton. */
  loading: string;
  empty?: { when: (data: T) => boolean; title: string; message?: string };
  notFound?: NotFoundOptions;
  children: (data: T) => ReactNode;
}) {
  if (query.isPending) return <StatePanel kind="loading" title={loading} />;
  if (query.isError)
    return <QueryError error={query.error} noun={noun} notFound={notFound} />;
  if (empty?.when(query.data))
    return (
      <StatePanel kind="empty" title={empty.title} message={empty.message} />
    );
  return <>{children(query.data)}</>;
}
