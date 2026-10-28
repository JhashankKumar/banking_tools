import { apiClient } from "@/lib/api-client";
import { envelope, pageEnvelope } from "@/lib/schemas";

import { userSchema, type User } from "./schemas";

export interface UserListParams {
  limit: number;
  offset: number;
}

export const fetchUsers = (p: UserListParams, signal?: AbortSignal) =>
  apiClient.get("/users", pageEnvelope(userSchema), {
    signal,
    params: { limit: p.limit, offset: p.offset },
  });

export interface CreateUserBody {
  username: string;
  password: string;
  role: User["role"];
}

export interface UpdateUserBody {
  role?: User["role"];
  isActive?: boolean;
  password?: string;
}

export const createUser = (body: CreateUserBody) =>
  apiClient.post("/users", body, envelope(userSchema));

export const updateUser = (id: string, body: UpdateUserBody) =>
  apiClient.patch(
    `/users/${encodeURIComponent(id)}`,
    { role: body.role, is_active: body.isActive, password: body.password },
    envelope(userSchema),
  );
