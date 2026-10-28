"use client";

import {
  Check,
  ChevronDown,
  ChevronRight,
  Clock,
  FileText,
  NotebookPen,
  Undo2,
} from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { CardHeader } from "@/components/ui/Card";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { QueryView } from "@/components/ui/QueryView";
import { StatusChip, type StatusStyles } from "@/components/ui/StatusChip";
import { CASE_STATUS_LABEL } from "@/features/cases/schemas";
import { CitationChip } from "@/features/copilot/components/CitationChip";
import { asApiError } from "@/lib/api-error";
import { formatDateTime } from "@/lib/format";

import { useNotes, useStatusChanges, useSubmitNote } from "../queries";
import type { Note, NoteStatus, StatusChange } from "../schemas";
import { NoteEditorDrawer } from "./NoteEditorDrawer";
import { ReviewDrawer } from "./ReviewDrawer";

const NOTE_STATUS: StatusStyles<NoteStatus> = {
  draft: { tone: "neutral", icon: FileText, label: "Draft" },
  awaiting_review: { tone: "review", icon: Clock, label: "Awaiting review" },
  returned: { tone: "review", icon: Undo2, label: "Returned" },
  approved: { tone: "success", icon: Check, label: "Approved" },
};

const provenance = (note: Note) =>
  note.origin === "ai_drafted"
    ? `AI-drafted, edited by ${note.versions.at(-1)?.editedByUsername ?? note.authorUsername}`
    : `Written by ${note.authorUsername}`;

/** A TX- ID whose case evidence (…-TX-n) is also cited needs no separate "record" chip. */
const chipIds = (ids: string[]) =>
  ids.filter(
    (id) =>
      !id.startsWith("TX-") || !ids.some((other) => other.endsWith(`-${id}`)),
  );

const historyLine = (c: StatusChange) =>
  [
    `${CASE_STATUS_LABEL[c.fromStatus]} → ${CASE_STATUS_LABEL[c.toStatus]}`,
    c.actorUsername,
    c.reason.replaceAll("_", " "),
    formatDateTime(c.createdAt),
  ].join(" · ");

function NoteItem({
  caseId,
  note,
  onEdit,
  onReview,
  onSelectTransaction,
}: {
  caseId: string;
  note: Note;
  onEdit: () => void;
  onReview: () => void;
  onSelectTransaction?: (id: string) => void;
}) {
  const submit = useSubmitNote(caseId);
  const latest = note.reviews.at(-1);
  return (
    <li className="flex flex-col gap-2 rounded-lg border border-line p-3">
      <div className="flex flex-wrap items-center gap-2">
        <StatusChip value={note.status} styles={NOTE_STATUS} outline />
        <span className="text-[11px] text-muted">{provenance(note)}</span>
        <span className="text-[11px] text-muted">
          · v{note.currentVersion} · {formatDateTime(note.updatedAt)}
        </span>
      </div>
      <p className="text-xs whitespace-pre-line text-ink">{note.body}</p>
      {note.citedIds.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {chipIds(note.citedIds).map((id) => (
            <CitationChip
              key={id}
              id={id}
              onSelectTransaction={onSelectTransaction}
            />
          ))}
        </div>
      )}
      {latest && (
        <p className="rounded-md bg-raised px-2.5 py-1.5 text-[11px] text-muted">
          {latest.decision === "return" ? "Returned" : "Approved"} by{" "}
          {latest.reviewerUsername}
          {latest.reason ? ` · ${latest.reason}` : ""}
          {latest.comment ? `: ${latest.comment}` : ""}
        </p>
      )}
      <ErrorBanner error={submit.error ? asApiError(submit.error) : null} />
      {(note.canEdit || note.canReview) && (
        <div className="flex gap-2">
          {note.canEdit && (
            <>
              <Button onClick={onEdit} className="px-2.5 py-1 text-xs">
                Edit
              </Button>
              <Button
                variant="primary"
                disabled={submit.isPending}
                onClick={() => submit.mutate(note.id)}
                className="px-2.5 py-1 text-xs"
              >
                Submit for review
              </Button>
            </>
          )}
          {note.canReview && (
            <Button
              variant="primary"
              onClick={onReview}
              className="px-2.5 py-1 text-xs"
            >
              Review
            </Button>
          )}
        </div>
      )}
    </li>
  );
}

/** Case notes with their review state, plus the case's status history. */
export function CaseNotesCard({
  caseId,
  onSelectTransaction,
}: {
  caseId: string;
  onSelectTransaction?: (transactionId: string) => void;
}) {
  const notes = useNotes(caseId);
  const history = useStatusChanges(caseId);
  const [editing, setEditing] = useState<Note | null>(null);
  const [reviewing, setReviewing] = useState<Note | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const changes = history.data?.items ?? [];

  return (
    <section
      aria-label="Case notes"
      className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-4 shadow-sm"
    >
      <CardHeader
        icon={<NotebookPen aria-hidden size={16} className="text-primary" />}
        title="Case notes"
      />
      <QueryView query={notes} noun="Notes" loading="Loading notes">
        {(data) =>
          data.items.length === 0 ? (
            <p className="text-xs text-muted">
              No notes yet. Save a copilot answer as a case note to start one.
            </p>
          ) : (
            <ul className="flex flex-col gap-2">
              {data.items.map((n) => (
                <NoteItem
                  key={n.id}
                  caseId={caseId}
                  note={n}
                  onEdit={() => setEditing(n)}
                  onReview={() => setReviewing(n)}
                  onSelectTransaction={onSelectTransaction}
                />
              ))}
            </ul>
          )
        }
      </QueryView>
      <button
        type="button"
        aria-expanded={showHistory}
        onClick={() => setShowHistory((v) => !v)}
        className="flex items-center gap-1 self-start text-xs font-medium text-primary"
      >
        {showHistory ? (
          <ChevronDown aria-hidden size={14} />
        ) : (
          <ChevronRight aria-hidden size={14} />
        )}
        Status history ({changes.length})
      </button>
      {showHistory &&
        (changes.length === 0 ? (
          <p className="text-xs text-muted">No status changes yet.</p>
        ) : (
          <ol className="flex flex-col gap-1 text-xs text-ink">
            {changes.map((c) => (
              <li key={`${c.createdAt}-${c.toStatus}`}>{historyLine(c)}</li>
            ))}
          </ol>
        ))}
      {editing && (
        <NoteEditorDrawer
          caseId={caseId}
          target={{ kind: "edit", noteId: editing.id, body: editing.body }}
          onClose={() => setEditing(null)}
        />
      )}
      {reviewing && (
        <ReviewDrawer
          caseId={caseId}
          note={reviewing}
          onClose={() => setReviewing(null)}
        />
      )}
    </section>
  );
}
