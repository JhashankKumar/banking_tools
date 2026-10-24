import { StatePanel } from "@/components/ui/StatePanel";
import { ApiError, userMessage } from "@/lib/api-error";

/** Maps a failed query to the right state panel (403 → permission denied, 404 → not found). */
export function QueryError({ error, noun }: { error: unknown; noun: string }) {
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
        message={error.message}
        requestId={requestId}
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
