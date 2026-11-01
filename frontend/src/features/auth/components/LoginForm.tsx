"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { Eye, EyeOff, Lock, User } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/Button";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Field } from "@/components/ui/Field";
import { asApiError, type ApiError } from "@/lib/api-error";
import { landingFor } from "@/lib/permissions";

import { login } from "../api";
import { meQuery } from "../queries";
import { loginFormSchema, type LoginForm as LoginValues } from "../schemas";

/**
 * Only same-origin paths are honoured as a post-login destination. Control characters and
 * backslashes are rejected first because URL parsing strips or rewrites them (e.g. "/\t/evil").
 * Reads `window`, so call it only in the browser (event handlers), never during render: this
 * client component is also rendered on the server, where `window` does not exist.
 */
function safeNext(value: string | null): string | null {
  if (!value || !value.startsWith("/") || /[\x00-\x1f\\]/.test(value))
    return null;
  const url = new URL(value, window.location.origin);
  return url.origin === window.location.origin
    ? url.pathname + url.search + url.hash
    : null;
}

export function LoginForm() {
  const router = useRouter();
  const rawNext = useSearchParams().get("next");
  const queryClient = useQueryClient();
  const [failure, setFailure] = useState<ApiError | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({ resolver: zodResolver(loginFormSchema) });

  const onSubmit = handleSubmit(async (values) => {
    setFailure(null);
    try {
      await login(values);
      queryClient.removeQueries();
      const me = await queryClient.fetchQuery(meQuery);
      // With cacheComponents, Next keeps this route mounted but hidden after navigating away:
      // clear the credentials now so they neither linger in memory nor reappear on sign-out.
      reset();
      setShowPassword(false);
      router.replace(safeNext(rawNext) ?? landingFor(me.role));
    } catch (error) {
      setFailure(asApiError(error));
    }
  });

  return (
    <form
      onSubmit={onSubmit}
      noValidate
      className="flex w-[420px] flex-col gap-4 rounded-2xl border border-line bg-surface p-9 shadow-xl dark:shadow-black/50"
    >
      <div className="flex flex-col gap-1.5">
        <h1 className="text-2xl font-bold text-ink">Sign in</h1>
        <p className="text-sm text-muted">
          Use your OpenFraud Investigator account.
        </p>
      </div>
      <ErrorBanner error={failure} note="this attempt was recorded." />
      <Field
        label="Username"
        autoComplete="username"
        mono
        icon={<User aria-hidden size={16} className="text-muted" />}
        error={errors.username?.message}
        {...register("username")}
      />
      <Field
        label="Password"
        type={showPassword ? "text" : "password"}
        autoComplete="current-password"
        icon={<Lock aria-hidden size={16} className="text-muted" />}
        error={errors.password?.message ?? (failure ? " " : undefined)}
        trailing={
          <button
            type="button"
            aria-label={showPassword ? "Hide password" : "Show password"}
            onClick={() => setShowPassword((s) => !s)}
            className="text-muted"
          >
            {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        }
        {...register("password")}
      />
      <Button
        type="submit"
        variant="primary"
        disabled={isSubmitting}
        className="py-3"
      >
        {isSubmitting ? "Signing in…" : "Sign in"}
      </Button>
      <div className="flex flex-col gap-1 rounded-lg bg-raised px-3 py-2.5">
        <p className="text-xs font-semibold text-ink">Demo users</p>
        <p className="font-mono text-xs text-ink">
          analyst.demo · supervisor.demo · auditor.demo
        </p>
        <p className="text-[11px] text-muted">
          Password is the OFI_DEMO_PASSWORD you set in .env. It is never shown
          here.
        </p>
      </div>
      <p className="text-[11px] text-muted">Every sign-in is audited</p>
    </form>
  );
}
