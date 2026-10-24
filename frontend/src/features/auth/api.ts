import { z } from "zod";

import { apiClient, authClient } from "@/lib/api-client";
import { envelope } from "@/lib/schemas";

import { meSchema, type LoginForm, type Me } from "./schemas";

/** Sign-in and sign-out answer 204 with no body. */
const noContent = z.undefined();

export const login = (form: LoginForm) =>
  authClient.post("/login", form, noContent);
export const logout = () => authClient.post("/logout", undefined, noContent);
export const fetchMe = (signal?: AbortSignal): Promise<Me> =>
  apiClient.get("/auth/me", envelope(meSchema), { signal });
