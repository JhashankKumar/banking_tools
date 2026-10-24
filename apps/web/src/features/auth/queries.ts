import { queryOptions, useQuery } from "@tanstack/react-query";

import { fetchMe } from "./api";

export const authKeys = { me: ["auth", "me"] as const };

export const meQuery = queryOptions({
  queryKey: authKeys.me,
  queryFn: ({ signal }) => fetchMe(signal),
  retry: false,
  staleTime: 5 * 60_000,
});

export const useMe = () => useQuery(meQuery);
