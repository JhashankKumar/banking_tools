import { LinkRow, Table, Td, Th } from "@/components/ui/Table";
import { formatDateTime } from "@/lib/format";

import type { ReviewQueueItem } from "../schemas";

export function ReviewsTable({ items }: { items: ReviewQueueItem[] }) {
  return (
    <Table
      empty={items.length === 0 && "No notes are waiting for your review."}
    >
      <thead>
        <tr>
          <Th>Case</Th>
          <Th>Title</Th>
          <Th>Author</Th>
          <Th>Submitted (IST)</Th>
        </tr>
      </thead>
      <tbody>
        {items.map((q) => (
          <LinkRow key={q.noteId} href={`/cases/${q.caseId}`} label={q.caseId}>
            <Td className="font-mono font-semibold whitespace-nowrap">
              <LinkRow.Link>{q.caseId}</LinkRow.Link>
            </Td>
            <Td>{q.caseTitle}</Td>
            <Td className="font-mono">{q.authorUsername}</Td>
            <Td className="font-mono whitespace-nowrap">
              {formatDateTime(q.submittedAt)}
            </Td>
          </LinkRow>
        ))}
      </tbody>
    </Table>
  );
}
