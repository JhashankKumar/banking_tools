import { z } from "zod";

import { apiClient } from "@/lib/api-client";
import { envelope, pageEnvelope } from "@/lib/schemas";

import {
  noteSchema,
  reviewQueueItemSchema,
  statusChangeSchema,
  type ReviewDecision,
} from "./schemas";

const notesPath = (caseId: string) =>
  `/cases/${encodeURIComponent(caseId)}/notes`;
const notePath = (caseId: string, noteId: string) =>
  `${notesPath(caseId)}/${encodeURIComponent(noteId)}`;

export interface ReviewBody {
  decision: ReviewDecision;
  comment?: string;
  reason?: string;
}

export interface PageParams {
  limit: number;
  offset: number;
}

export const fetchNotes = (caseId: string, signal?: AbortSignal) =>
  apiClient.get(notesPath(caseId), pageEnvelope(noteSchema), { signal });

export const createNote = (
  caseId: string,
  body: { body: string; sourceMessageId: string | null },
) =>
  apiClient.post(
    notesPath(caseId),
    { body: body.body, source_message_id: body.sourceMessageId },
    envelope(noteSchema),
  );

export const updateNote = (caseId: string, noteId: string, body: string) =>
  apiClient.patch(notePath(caseId, noteId), { body }, envelope(noteSchema));

export const submitNote = (caseId: string, noteId: string) =>
  apiClient.post(
    `${notePath(caseId, noteId)}/submit`,
    {},
    envelope(noteSchema),
  );

export const reviewNote = (caseId: string, noteId: string, body: ReviewBody) =>
  apiClient.post(
    `${notePath(caseId, noteId)}/review`,
    body,
    envelope(noteSchema),
  );

export const closeCase = (
  caseId: string,
  body: { reason: string; comment: string },
) =>
  apiClient.post(
    `/cases/${encodeURIComponent(caseId)}/close`,
    body,
    envelope(z.array(statusChangeSchema)),
  );

export const fetchStatusChanges = (caseId: string, signal?: AbortSignal) =>
  apiClient.get(
    `/cases/${encodeURIComponent(caseId)}/status-changes`,
    pageEnvelope(statusChangeSchema),
    { signal },
  );

export const fetchReviewQueue = (p: PageParams, signal?: AbortSignal) =>
  apiClient.get("/notes/awaiting-review", pageEnvelope(reviewQueueItemSchema), {
    signal,
    params: { limit: p.limit, offset: p.offset },
  });
