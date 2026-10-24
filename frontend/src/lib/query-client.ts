import { MutationCache, QueryCache, QueryClient } from "@tanstack/react-query";

import { ApiError } from "./api-error";

function shouldRetry(failureCount: number, error: unknown): boolean {
  // 4xx and unexpected response shapes will not change on a retry.
  const permanent =
    error instanceof ApiError &&
    ((error.status >= 400 && error.status < 500) ||
      error.code === "UNEXPECTED_RESPONSE");
  return !permanent && failureCount < 2;
}

/** An expired or missing session anywhere sends the user to sign in, then back here. */
function onError(error: unknown): void {
  if (error instanceof ApiError && error.code === "AUTH_NOT_AUTHENTICATED") {
    // Outside React (no router here); a full navigation also drops the old session's cache.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.assign(
      `/login?next=${encodeURIComponent(window.location.pathname)}`,
    );
  }
}

export function makeQueryClient(): QueryClient {
  return new QueryClient({
    queryCache: new QueryCache({ onError }),
    mutationCache: new MutationCache({ onError }),
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        refetchOnWindowFocus: false,
        retry: shouldRetry,
      },
      mutations: { retry: false },
    },
  });
}
