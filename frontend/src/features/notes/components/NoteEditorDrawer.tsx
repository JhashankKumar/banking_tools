"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Drawer } from "@/components/ui/Drawer";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { TextArea } from "@/components/ui/TextArea";
import type { CopilotAnswer } from "@/features/copilot/schemas";
import { asApiError, type ApiError } from "@/lib/api-error";

import { answerToNoteBody } from "../note-body";
import { useSaveNote } from "../queries";

export type NoteTarget =
  | { kind: "draft"; sourceMessageId: string; answer: CopilotAnswer }
  | { kind: "edit"; noteId: string; body: string };

const formSchema = z.object({
  body: z
    .string()
    .trim()
    .min(1, "Write the note.")
    .max(20_000, "Keep the note under 20,000 characters."),
});
type FormValues = z.infer<typeof formSchema>;
const FORM_ID = "note-editor";

/** Saves a copilot answer as a new case note, or edits an existing one. */
export function NoteEditorDrawer({
  caseId,
  target,
  onClose,
}: {
  caseId: string;
  target: NoteTarget;
  onClose: () => void;
}) {
  const save = useSaveNote(caseId);
  const [failure, setFailure] = useState<ApiError | null>(null);
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      body:
        target.kind === "draft" ? answerToNoteBody(target.answer) : target.body,
    },
  });

  const onSubmit = handleSubmit(async ({ body }) => {
    setFailure(null);
    try {
      await save.mutateAsync({
        noteId: target.kind === "edit" ? target.noteId : null,
        body,
        sourceMessageId:
          target.kind === "draft" ? target.sourceMessageId : null,
      });
      onClose();
    } catch (error) {
      const apiError = asApiError(error);
      const bodyProblem = apiError.details.find((d) =>
        ["body", "body.body"].includes(d.field),
      );
      if (bodyProblem) setError("body", { message: bodyProblem.message });
      else setFailure(apiError);
    }
  });

  return (
    <Drawer
      title={target.kind === "draft" ? "Save as case note" : "Edit note"}
      open
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type="submit"
            form={FORM_ID}
            variant="primary"
            disabled={save.isPending}
          >
            Save note
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
        {target.kind === "draft" && (
          <p className="text-xs text-muted">
            AI-drafted · you can edit before saving
          </p>
        )}
        <TextArea
          label="Note"
          rows={16}
          mono
          hint="Keep citations in square brackets. Each EV- and TX- ID is checked against this case when you save."
          error={errors.body?.message}
          {...register("body")}
        />
      </form>
    </Drawer>
  );
}
