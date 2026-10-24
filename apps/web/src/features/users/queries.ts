import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { pageEnvelope } from "@/lib/schemas";

import {
  createUser,
  updateUser,
  type CreateUserBody,
  type UpdateUserBody,
} from "./api";
import { userSchema } from "./schemas";

export interface UserListParams {
  limit: number;
  offset: number;
}

export const userKeys = {
  all: ["users"] as const,
  list: (p: UserListParams) => [...userKeys.all, "list", p] as const,
};

export const useUsers = (p: UserListParams) =>
  useQuery({
    queryKey: userKeys.list(p),
    queryFn: ({ signal }) =>
      apiClient.get("/users", pageEnvelope(userSchema), {
        signal,
        params: { limit: p.limit, offset: p.offset },
      }),
  });

export function useCreateUser() {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [...userKeys.all, "create"],
    mutationFn: (body: CreateUserBody) => createUser(body),
    onSuccess: () => client.invalidateQueries({ queryKey: userKeys.all }),
  });
}

export function useUpdateUser() {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [...userKeys.all, "update"],
    mutationFn: ({ id, body }: { id: string; body: UpdateUserBody }) =>
      updateUser(id, body),
    onSuccess: () => client.invalidateQueries({ queryKey: userKeys.all }),
  });
}
