"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Info } from "lucide-react";
import { useIsMutating } from "@tanstack/react-query";
import { useState } from "react";
import { Controller, useForm, type UseFormSetError } from "react-hook-form";

import { Button } from "@/components/ui/Button";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Drawer } from "@/components/ui/Drawer";
import { Field } from "@/components/ui/Field";
import { Segmented } from "@/components/ui/Segmented";
import { Toggle } from "@/components/ui/Toggle";
import { asApiError, type ApiError } from "@/lib/api-error";
import { ROLE_LABEL } from "@/lib/permissions";

import type { UpdateUserBody } from "../api";
import { useCreateUser, useUpdateUser, userKeys } from "../queries";
import {
  ROLE_PERMISSIONS,
  ROLES,
  userFormSchema,
  type User,
  type UserForm,
} from "../schemas";

const FORM_ID = "user-form";
const WIRE_TO_FORM: Record<string, keyof UserForm> = {
  username: "username",
  password: "password",
  role: "role",
  is_active: "isActive",
};

type Props =
  | {
      mode: "create";
      user?: undefined;
      isSelf?: undefined;
      open: boolean;
      onClose: () => void;
    }
  | {
      mode: "edit";
      user: User;
      /** Editing your own account: the API refuses role and status changes (USER_SELF_LOCKOUT). */
      isSelf?: boolean;
      open: boolean;
      onClose: () => void;
    };

export function UserFormDrawer(props: Props) {
  const { mode, open, onClose } = props;
  const saving = useIsMutating({ mutationKey: userKeys.all }) > 0;
  return (
    <Drawer
      title={mode === "create" ? "Create user" : "Edit user"}
      open={open}
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type="submit"
            form={FORM_ID}
            variant="primary"
            disabled={saving}
          >
            {mode === "create" ? "Create user" : "Save changes"}
          </Button>
        </>
      }
    >
      {/* Keyed so the form resets whenever a different user is opened. */}
      <UserFormBody key={props.user?.id ?? "new"} {...props} />
    </Drawer>
  );
}

/** Puts server-side problems on the matching field; returns false when none matched. */
function applyServerErrors(
  error: ApiError,
  setError: UseFormSetError<UserForm>,
): boolean {
  if (error.code === "USER_USERNAME_TAKEN") {
    setError("username", { message: "This username is already taken." });
    return true;
  }
  let matched = false;
  for (const d of error.details) {
    const field = WIRE_TO_FORM[d.field.replace(/^body\./, "")];
    if (field) {
      setError(field, { message: d.message });
      matched = true;
    }
  }
  return matched;
}

function changedFields(user: User, values: UserForm): UpdateUserBody {
  return {
    role: values.role !== user.role ? values.role : undefined,
    isActive: values.isActive !== user.isActive ? values.isActive : undefined,
    password: values.password || undefined,
  };
}

function UserFormBody({ mode, user, isSelf = false, onClose }: Props) {
  const create = useCreateUser();
  const update = useUpdateUser();
  const [failure, setFailure] = useState<ApiError | null>(null);
  const {
    register,
    control,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<UserForm>({
    resolver: zodResolver(userFormSchema(mode)),
    defaultValues: {
      username: user?.username ?? "",
      role: user?.role ?? "analyst",
      isActive: user?.isActive ?? true,
      password: "",
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    setFailure(null);
    try {
      if (mode === "create") {
        await create.mutateAsync({
          username: values.username,
          password: values.password,
          role: values.role,
        });
      } else {
        const body = changedFields(user, values);
        if (Object.values(body).some((v) => v !== undefined))
          await update.mutateAsync({ id: user.id, body });
      }
      onClose();
    } catch (error) {
      const apiError = asApiError(error);
      if (!applyServerErrors(apiError, setError)) setFailure(apiError);
    }
  });

  return (
    <form
      id={FORM_ID}
      onSubmit={onSubmit}
      noValidate
      className="flex flex-col gap-5"
    >
      <ErrorBanner error={failure} />
      <Field
        label="Username"
        mono
        readOnly={mode === "edit"}
        autoComplete="off"
        hint={
          mode === "create"
            ? "3–32 characters: lowercase letters, digits, dot, underscore or hyphen."
            : "Usernames cannot be changed."
        }
        error={errors.username?.message}
        {...register("username")}
      />
      <Controller
        control={control}
        name="role"
        render={({ field }) => (
          <div className="flex flex-col gap-1.5">
            <span className="text-xs font-semibold text-ink">Role</span>
            <Segmented
              label="Role"
              size="md"
              options={ROLES.map((r) => ({ value: r, label: ROLE_LABEL[r] }))}
              value={field.value}
              onChange={field.onChange}
              disabled={isSelf}
            />
            <p className="text-xs text-muted">
              {ROLE_PERMISSIONS[field.value]}
            </p>
            {isSelf && (
              <p className="text-xs text-muted">
                You cannot change your own role or status. Ask another
                Supervisor.
              </p>
            )}
          </div>
        )}
      />
      {mode === "edit" && (
        <Controller
          control={control}
          name="isActive"
          render={({ field }) => (
            <div className="flex items-center gap-3">
              <Toggle
                label="Active"
                checked={field.value}
                onChange={field.onChange}
                disabled={isSelf}
              />
              <span className="text-sm text-ink">
                {field.value
                  ? "Active — can sign in"
                  : "Inactive — sign-in blocked"}
              </span>
            </div>
          )}
        />
      )}
      <Field
        label={mode === "create" ? "Temporary password" : "New password"}
        type="password"
        autoComplete="new-password"
        hint={
          mode === "create"
            ? "At least 12 characters. Share it with the user out of band."
            : "Optional. Leave empty to keep the current password."
        }
        error={errors.password?.message}
        {...register("password")}
      />
      {mode === "edit" && (
        <p className="flex gap-2 rounded-lg bg-raised px-3 py-2.5 text-xs text-muted">
          <Info aria-hidden size={14} className="mt-0.5 shrink-0" />
          Saved as audit event user.updated with the changed field names only
          (e.g. is_active, role).
        </p>
      )}
    </form>
  );
}
