import { Chip } from "@/components/ui/Chip";

/** The transaction a citation points at: a TX- ID itself, or the TX- an EV- ID ends with. */
export function citedTransaction(id: string): string | null {
  if (id.startsWith("TX-")) return id;
  return /-(TX-\d+)$/.exec(id)?.[1] ?? null;
}

/**
 * Teal chip for this case's evidence (EV-…); neutral "record" chip for a transaction outside
 * the case (TX-…). Clicking selects the transaction in the graph and timeline.
 */
export function CitationChip({
  id,
  onSelectTransaction,
}: {
  id: string;
  onSelectTransaction?: (transactionId: string) => void;
}) {
  const isRecord = id.startsWith("TX-");
  const transaction = citedTransaction(id);
  return (
    <button
      type="button"
      aria-label={
        isRecord ? `${id}, record outside the case` : `${id}, show transaction`
      }
      onClick={() => transaction && onSelectTransaction?.(transaction)}
      className="align-middle"
    >
      <Chip tone={isRecord ? "neutral" : "selected"} outline mono>
        {id}
      </Chip>
    </button>
  );
}
