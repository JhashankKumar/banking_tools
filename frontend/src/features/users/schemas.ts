import { z } from "zod";

import { isoUtcSchema } from "@/lib/schemas";

export const ROLES = ["analyst", "supervisor", "auditor"] as const;

/** What each role may do, shown under the role picker. */
export const ROLE_PERMISSIONS: Record<(typeof ROLES)[number], string> = {
  analyst:
    "Reads alerts, cases, transactions and evidence. Cannot manage users.",
  supervisor:
    "Everything an Analyst can, plus case status changes and user management.",
  auditor: "Reads the audit log only. No access to case data.",
};

export const userSchema = z
  .object({
    id: z.string(),
    username: z.string(),
    role: z.enum(ROLES),
    is_active: z.boolean(),
    created_at: isoUtcSchema,
    updated_at: isoUtcSchema,
  })
  .transform((u) => ({
    id: u.id,
    username: u.username,
    role: u.role,
    isActive: u.is_active,
    createdAt: u.created_at,
    updatedAt: u.updated_at,
  }));
export type User = z.output<typeof userSchema>;

const USERNAME_PATTERN = /^[a-z0-9_.-]{3,32}$/;
const PASSWORD_HINT = "Use at least 12 characters.";

/** One form for both drawer modes; the password is required only when creating. */
export const userFormSchema = (mode: "create" | "edit") =>
  z.object({
    username: z
      .string()
      .regex(
        USERNAME_PATTERN,
        "3–32 characters: lowercase letters, digits, dot, underscore or hyphen.",
      ),
    role: z.enum(ROLES),
    isActive: z.boolean(),
    password:
      mode === "create"
        ? z.string().min(12, PASSWORD_HINT).max(128)
        : z.union([z.literal(""), z.string().min(12, PASSWORD_HINT).max(128)]),
  });
export type UserForm = z.infer<ReturnType<typeof userFormSchema>>;
