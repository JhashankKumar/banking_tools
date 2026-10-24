import type { ReactNode } from "react";

import { ApiError, userMessage } from "@/lib/api-error";

import { StatePanel } from "./StatePanel";

/** Maps a failed query to the right state panel (403 → permission denied, 404 → not found). */
export interface NotFoundOptions {
  message?: string;
  action?: ReactNode;
}

export function QueryError({
  error,
  noun,
  notFound,
}: {
  error: unknown;
  noun: string;
  notFound?: NotFoundOptions;
}) {
  const requestId = error instanceof ApiError ? error.requestId : null;
  if (error instanceof ApiError && error.status === 403) {
    return (
      <StatePanel
        kind="forbidden"
        title="You don't have access to this page"
        message="Your role does not include this view."
        requestId={requestId}
      />
    );
  }
  if (error instanceof ApiError && error.status === 404) {
    return (
      <StatePanel
        kind="not-found"
        title={`${noun} not found`}
        message={notFound?.message ?? error.message}
        requestId={requestId}
        action={notFound?.action}
      />
    );
  }
  return (
    <StatePanel
      kind="error"
      title={`Could not load ${noun.toLowerCase()}`}
      message={userMessage(error, "Something went wrong.")}
      requestId={requestId}
    />
  );
}
