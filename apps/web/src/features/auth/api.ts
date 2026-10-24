import { apiClient } from "@/lib/api-client";
import { ApiError } from "@/lib/api-error";
import { envelope, errorEnvelopeSchema } from "@/lib/schemas";

import { meSchema, type LoginForm, type Me } from "./schemas";

async function sessionCall(
  path: "/session/login" | "/session/logout",
  body?: unknown,
): Promise<void> {
  const response = await fetch(path, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    credentials: "same-origin",
  });
  if (response.ok) return;
  const parsed = errorEnvelopeSchema.safeParse(
    await response.json().catch(() => null),
  );
  throw parsed.success
    ? new ApiError({
        status: response.status,
        code: parsed.data.error.code,
        message: parsed.data.error.message,
        requestId: parsed.data.error.request_id,
      })
    : new ApiError({
        status: response.status,
        code: "UNEXPECTED_RESPONSE",
        message: "Sign-in failed.",
      });
}

export const login = (form: LoginForm) => sessionCall("/session/login", form);
export const logout = () => sessionCall("/session/logout");
export const fetchMe = (signal?: AbortSignal): Promise<Me> =>
  apiClient.get("/auth/me", envelope(meSchema), { signal });
