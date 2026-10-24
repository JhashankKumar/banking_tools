import { z } from "zod";

export const meSchema = z.object({
  id: z.string(),
  username: z.string(),
  role: z.enum(["analyst", "supervisor", "auditor"]),
  permissions: z.array(z.string()),
});
export type Me = z.output<typeof meSchema>;

export const loginFormSchema = z.object({
  username: z
    .string()
    .regex(
      /^[a-z0-9_.-]{3,32}$/,
      "Use 3–32 lowercase letters, digits, dot, dash, or underscore.",
    ),
  password: z.string().min(1, "Enter your password."),
});
export type LoginForm = z.output<typeof loginFormSchema>;
