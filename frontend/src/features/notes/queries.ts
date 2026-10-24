import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
} from "@tanstack/react-query";

import { caseKeys } from "@/features/cases/queries";

import {
  closeCase,
  createNote,
  fetchNotes,
  fetchReviewQueue,
  fetchStatusChanges,
  reviewNote,
  submitNote,
  updateNote,
  type PageParams,
  type ReviewBody,
} from "./api";

export const noteKeys = {
  all: ["notes"] as const,
  list: (caseId: string) => [...noteKeys.all, "list", caseId] as const,
  statusChanges: (caseId: string) =>
    [...noteKeys.all, "status-changes", caseId] as const,
  queue: (p: PageParams) => [...noteKeys.all, "queue", p] as const,
};

export const useNotes = (caseId: string) =>
  useQuery({
    queryKey: noteKeys.list(caseId),
    queryFn: ({ signal }) => fetchNotes(caseId, signal),
  });

export const useStatusChanges = (caseId: string) =>
  useQuery({
    queryKey: noteKeys.statusChanges(caseId),
    queryFn: ({ signal }) => fetchStatusChanges(caseId, signal),
  });

export const useReviewQueue = (p: PageParams) =>
  useQuery({
    queryKey: noteKeys.queue(p),
    queryFn: ({ signal }) => fetchReviewQueue(p, signal),
  });

/** Notes, the review queue, status history and the case header all change together. */
const refreshCase = (client: QueryClient, caseId: string) =>
  Promise.all([
    client.invalidateQueries({ queryKey: noteKeys.all }),
    client.invalidateQueries({ queryKey: caseKeys.detail(caseId) }),
    client.invalidateQueries({ queryKey: [...caseKeys.all, "list"] }),
  ]);

function useNoteMutation<A>(caseId: string, fn: (args: A) => Promise<unknown>) {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [...noteKeys.all, "mutate", caseId],
    mutationFn: fn,
    onSuccess: () => refreshCase(client, caseId),
  });
}

export const useSaveNote = (caseId: string) =>
  useNoteMutation(
    caseId,
    (a: {
      noteId: string | null;
      body: string;
      sourceMessageId: string | null;
    }) =>
      a.noteId
        ? updateNote(caseId, a.noteId, a.body)
        : createNote(caseId, {
            body: a.body,
            sourceMessageId: a.sourceMessageId,
          }),
  );

export const useSubmitNote = (caseId: string) =>
  useNoteMutation(caseId, (noteId: string) => submitNote(caseId, noteId));

export const useReviewNote = (caseId: string) =>
  useNoteMutation(caseId, (a: { noteId: string; body: ReviewBody }) =>
    reviewNote(caseId, a.noteId, a.body),
  );

export const useCloseCase = (caseId: string) =>
  useNoteMutation(caseId, (a: { reason: string; comment: string }) =>
    closeCase(caseId, a),
  );
