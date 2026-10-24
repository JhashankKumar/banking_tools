import { Check, FilePlus2 } from "lucide-react";

import { Button } from "@/components/ui/Button";

import type { AnswerItem, CopilotAnswer } from "../schemas";
import { CitationChip } from "./CitationChip";

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <h4 className="text-[10px] font-bold tracking-wider text-muted uppercase">
        {title}
      </h4>
      {children}
    </div>
  );
}

function CitedList({
  items,
  onSelectTransaction,
}: {
  items: AnswerItem[];
  onSelectTransaction?: (id: string) => void;
}) {
  return (
    <ul className="flex flex-col gap-1.5">
      {items.map((item, i) => (
        <li key={i} className="text-xs text-ink">
          {item.text}{" "}
          {item.citations.map((c) => (
            <CitationChip
              key={c}
              id={c}
              onSelectTransaction={onSelectTransaction}
            />
          ))}
        </li>
      ))}
    </ul>
  );
}

function PlainList({ items }: { items: string[] }) {
  return (
    <ul className="flex list-disc flex-col gap-1 pl-4 text-xs text-ink">
      {items.map((t, i) => (
        <li key={i}>{t}</li>
      ))}
    </ul>
  );
}

/** A grounded answer: what the copilot did, then the four fixed sections. */
export function AnswerView({
  answer,
  onSelectTransaction,
  onSave,
}: {
  answer: CopilotAnswer;
  onSelectTransaction?: (transactionId: string) => void;
  /** Present only when the viewer may turn this answer into a case note. */
  onSave?: () => void;
}) {
  return (
    <article
      aria-label="Copilot answer"
      className="flex flex-col gap-2.5 rounded-xl border border-line bg-raised p-3"
    >
      {answer.steps.length > 0 && (
        <ul className="flex flex-col gap-0.5 text-[11px] text-muted">
          {answer.steps.map((s) => (
            <li key={s} className="flex items-center gap-1">
              <Check aria-hidden size={11} className="text-success" />
              {s}
            </li>
          ))}
        </ul>
      )}
      {answer.records.length > 0 && (
        <Section title="What the records show">
          <CitedList
            items={answer.records}
            onSelectTransaction={onSelectTransaction}
          />
        </Section>
      )}
      {answer.calculated.length > 0 && (
        <Section title="Calculated">
          <CitedList
            items={answer.calculated}
            onSelectTransaction={onSelectTransaction}
          />
        </Section>
      )}
      {answer.notEstablished.length > 0 && (
        <Section title="Not established">
          <PlainList items={answer.notEstablished} />
        </Section>
      )}
      {answer.nextChecks.length > 0 && (
        <Section title="Next checks">
          <PlainList items={answer.nextChecks} />
        </Section>
      )}
      <p className="rounded-lg bg-review-soft px-2.5 py-1.5 text-[11px] font-medium text-review">
        Signal for review; not a finding of fraud.
      </p>
      {onSave && (
        <Button
          variant="secondary"
          onClick={onSave}
          className="self-start px-2.5 py-1 text-xs"
        >
          <FilePlus2 aria-hidden size={13} />
          Save as case note
        </Button>
      )}
    </article>
  );
}
