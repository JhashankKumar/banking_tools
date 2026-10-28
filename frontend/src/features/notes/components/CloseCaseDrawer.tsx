"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Drawer } from "@/components/ui/Drawer";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { TextArea } from "@/components/ui/TextArea";
import { asApiError, type ApiError } from "@/lib/api-error";

import { useCloseCase } from "../queries";
import { CLOSING_REASONS } from "../schemas";
import { ReasonSelect } from "./ReasonSelect";

const formSchema = z.object({
  reason: z
    .string()
    .refine(
      (r) => (CLOSING_REASONS as readonly string[]).includes(r),
      "Choose a closing reason.",
    ),
  comment: z.string().trim().min(1, "Add a comment.").max(2_000),
});
type FormValues = z.infer<typeof formSchema>;
const FORM_ID = "close-case";

/** Closes an escalated case (supervisor only; the API enforces it). Closing is final. */
export function CloseCaseDrawer({
  caseId,
  onClose,
}: {
  caseId: string;
  onClose: () => void;
}) {
  const close = useCloseCase(caseId);
  const [failure, setFailure] = useState<ApiError | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: { reason: "", comment: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    setFailure(null);
    try {
      await close.mutateAsync(values);
      onClose();
    } catch (error) {
      setFailure(asApiError(error));
    }
  });

  return (
    <Drawer
      title={`Close ${caseId}`}
      open
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type="submit"
            form={FORM_ID}
            variant="primary"
            disabled={close.isPending}
          >
            Close case
          </Button>
        </>
      }
    >
      <form
        id={FORM_ID}
        onSubmit={onSubmit}
        noValidate
        className="flex flex-col gap-4"
      >
        <ErrorBanner error={failure} />
        <p className="text-xs text-muted">
          Closing is final in this version: a closed case cannot be reopened.
        </p>
        <ReasonSelect error={errors.reason?.message} {...register("reason")} />
        <TextArea
          label="Comment"
          rows={4}
          error={errors.comment?.message}
          {...register("comment")}
        />
      </form>
    </Drawer>
  );
}
