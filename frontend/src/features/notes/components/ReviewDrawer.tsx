"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { Controller, useForm, useWatch } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Drawer } from "@/components/ui/Drawer";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Field } from "@/components/ui/Field";
import { Segmented } from "@/components/ui/Segmented";
import { TextArea } from "@/components/ui/TextArea";
import { CitationChip } from "@/features/copilot/components/CitationChip";
import { asApiError, type ApiError } from "@/lib/api-error";

import type { ReviewBody } from "../api";
import { useReviewNote } from "../queries";
import { CLOSING_REASONS, type Note, type ReviewDecision } from "../schemas";
import { ReasonSelect } from "./ReasonSelect";

const DECISIONS: { value: ReviewDecision; label: string }[] = [
  { value: "return", label: "Return" },
  { value: "approve_keep_open", label: "Keep open" },
  { value: "approve_escalate", label: "Escalate" },
  { value: "approve_close", label: "Close" },
];

const formSchema = z
  .object({
    decision: z.enum([
      "return",
      "approve_keep_open",
      "approve_escalate",
      "approve_close",
    ]),
    comment: z.string().trim().max(2_000),
    reason: z.string().trim().max(200),
  })
  .superRefine((v, ctx) => {
    if (v.decision === "return" && !v.comment)
      ctx.addIssue({
        code: "custom",
        path: ["comment"],
        message: "Add a comment for the author.",
      });
    if (v.decision === "approve_escalate" && !v.reason)
      ctx.addIssue({
        code: "custom",
        path: ["reason"],
        message: "Add a reason for escalating.",
      });
    if (v.decision === "approve_close") {
      if (!(CLOSING_REASONS as readonly string[]).includes(v.reason))
        ctx.addIssue({
          code: "custom",
          path: ["reason"],
          message: "Choose a closing reason.",
        });
      if (!v.comment)
        ctx.addIssue({
          code: "custom",
          path: ["comment"],
          message: "Add a comment.",
        });
    }
  });
type FormValues = z.infer<typeof formSchema>;
const FORM_ID = "note-review";

/** The supervisor's decision on a note; approval also decides the case status. */
export function ReviewDrawer({
  caseId,
  note,
  onClose,
}: {
  caseId: string;
  note: Note;
  onClose: () => void;
}) {
  const review = useReviewNote(caseId);
  const [failure, setFailure] = useState<ApiError | null>(null);
  const {
    register,
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: { decision: "approve_keep_open", comment: "", reason: "" },
  });
  const decision = useWatch({ control, name: "decision" });

  const onSubmit = handleSubmit(async ({ decision, comment, reason }) => {
    setFailure(null);
    const body: ReviewBody = { decision };
    if (decision === "approve_escalate" || decision === "approve_close")
      body.reason = reason;
    if (comment) body.comment = comment;
    try {
      await review.mutateAsync({ noteId: note.id, body });
      onClose();
    } catch (error) {
      setFailure(asApiError(error));
    }
  });

  return (
    <Drawer
      title="Review note"
      open
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type="submit"
            form={FORM_ID}
            variant="primary"
            disabled={review.isPending}
          >
            Confirm
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
        <div className="flex flex-col gap-2 rounded-lg bg-raised p-3">
          <p className="text-[11px] text-muted">
            By {note.authorUsername} · version {note.currentVersion}
          </p>
          <p className="text-xs whitespace-pre-line text-ink">{note.body}</p>
          <div className="flex flex-wrap gap-1">
            {note.citedIds.map((id) => (
              <CitationChip key={id} id={id} />
            ))}
          </div>
        </div>
        <Controller
          control={control}
          name="decision"
          render={({ field }) => (
            <div className="flex flex-col gap-1.5">
              <span className="text-xs font-semibold text-ink">Decision</span>
              <Segmented
                label="Decision"
                size="md"
                options={DECISIONS}
                value={field.value}
                onChange={field.onChange}
              />
            </div>
          )}
        />
        {decision === "approve_escalate" && (
          <Field
            label="Reason"
            placeholder="e.g. Refer to fraud operations"
            error={errors.reason?.message}
            {...register("reason")}
          />
        )}
        {decision === "approve_close" && (
          <ReasonSelect
            error={errors.reason?.message}
            {...register("reason")}
          />
        )}
        <TextArea
          label="Comment"
          rows={4}
          error={errors.comment?.message}
          hint={
            decision === "return"
              ? "Required: tell the author what to change."
              : "Recorded with the decision and the case status history."
          }
          {...register("comment")}
        />
      </form>
    </Drawer>
  );
}
