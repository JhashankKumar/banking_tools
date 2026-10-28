import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createUser,
  fetchUsers,
  updateUser,
  type CreateUserBody,
  type UpdateUserBody,
  type UserListParams,
} from "./api";

export const userKeys = {
  all: ["users"] as const,
  list: (p: UserListParams) => [...userKeys.all, "list", p] as const,
};

export const useUsers = (p: UserListParams) =>
  useQuery({
    queryKey: userKeys.list(p),
    queryFn: ({ signal }) => fetchUsers(p, signal),
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
