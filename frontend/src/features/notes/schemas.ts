import { z } from "zod";

import { caseStatusSchema } from "@/features/cases/schemas";
import { isoUtcSchema } from "@/lib/schemas";

export const CLOSING_REASONS = [
  "No further action",
  "Referred externally",
  "Not actionable / duplicate",
] as const;

export const noteStatusSchema = z.enum([
  "draft",
  "awaiting_review",
  "returned",
  "approved",
]);
export type NoteStatus = z.output<typeof noteStatusSchema>;

export const reviewDecisionSchema = z.enum([
  "return",
  "approve_keep_open",
  "approve_escalate",
  "approve_close",
]);
export type ReviewDecision = z.output<typeof reviewDecisionSchema>;

const reviewSchema = z
  .object({
    decision: reviewDecisionSchema,
    version: z.number(),
    reviewer_username: z.string(),
    comment: z.string().nullable(),
    reason: z.string().nullable(),
    created_at: isoUtcSchema,
  })
  .transform((r) => ({
    decision: r.decision,
    version: r.version,
    reviewerUsername: r.reviewer_username,
    comment: r.comment,
    reason: r.reason,
    createdAt: r.created_at,
  }));

const versionSchema = z
  .object({
    version: z.number(),
    edited_by_username: z.string(),
    created_at: isoUtcSchema,
  })
  .transform((v) => ({
    version: v.version,
    editedByUsername: v.edited_by_username,
    createdAt: v.created_at,
  }));

export const noteSchema = z
  .object({
    id: z.string(),
    case_id: z.string(),
    status: noteStatusSchema,
    origin: z.enum(["ai_drafted", "written"]),
    author_username: z.string(),
    current_version: z.number(),
    body: z.string(),
    cited_ids: z.array(z.string()),
    created_at: isoUtcSchema,
    updated_at: isoUtcSchema,
    can_edit: z.boolean(),
    can_review: z.boolean(),
    reviews: z.array(reviewSchema),
    versions: z.array(versionSchema),
  })
  .transform((n) => ({
    id: n.id,
    caseId: n.case_id,
    status: n.status,
    origin: n.origin,
    authorUsername: n.author_username,
    currentVersion: n.current_version,
    body: n.body,
    citedIds: n.cited_ids,
    createdAt: n.created_at,
    updatedAt: n.updated_at,
    canEdit: n.can_edit,
    canReview: n.can_review,
    reviews: n.reviews,
    versions: n.versions,
  }));
export type Note = z.output<typeof noteSchema>;

export const statusChangeSchema = z
  .object({
    from_status: caseStatusSchema,
    to_status: caseStatusSchema,
    actor_username: z.string(),
    reason: z.string(),
    comment: z.string().nullable(),
    note_id: z.string().nullable(),
    created_at: isoUtcSchema,
  })
  .transform((c) => ({
    fromStatus: c.from_status,
    toStatus: c.to_status,
    actorUsername: c.actor_username,
    reason: c.reason,
    comment: c.comment,
    noteId: c.note_id,
    createdAt: c.created_at,
  }));
export type StatusChange = z.output<typeof statusChangeSchema>;

export const reviewQueueItemSchema = z
  .object({
    note_id: z.string(),
    case_id: z.string(),
    case_title: z.string(),
    author_username: z.string(),
    submitted_at: isoUtcSchema,
  })
  .transform((q) => ({
    noteId: q.note_id,
    caseId: q.case_id,
    caseTitle: q.case_title,
    authorUsername: q.author_username,
    submittedAt: q.submitted_at,
  }));
export type ReviewQueueItem = z.output<typeof reviewQueueItemSchema>;
