import { Send, Sparkles } from "lucide-react";

import { Chip } from "@/components/ui/Chip";

const SUGGESTED = [
  "Explain the money path",
  "What is missing?",
  "Why did the alert fire?",
];

/** Visual shell only; the copilot arrives in Milestone 5. */
export function CopilotPanel({ caseId }: { caseId: string }) {
  return (
    <section
      aria-label="AI copilot"
      className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-4 shadow-sm"
    >
      <header className="flex items-center gap-2">
        <Sparkles aria-hidden size={16} className="text-primary" />
        <h2 className="text-sm font-semibold text-ink">AI copilot</h2>
        <span className="text-[11px] text-muted">
          · case-scoped · cites evidence
        </span>
      </header>
      <div className="flex flex-wrap gap-1.5">
        {SUGGESTED.map((q) => (
          <Chip key={q} tone="primary" outline>
            {q}
          </Chip>
        ))}
      </div>
      <div className="rounded-xl bg-raised p-3 text-xs text-muted">
        The copilot arrives in Milestone 5. It will answer only from this
        case&apos;s records and cite evidence IDs.
      </div>
      <p className="rounded-lg bg-review-soft px-2.5 py-1.5 text-[11px] font-medium text-review">
        Signal for review; not a finding of fraud.
      </p>
      <label className="flex items-center gap-2 rounded-xl border border-line bg-surface py-1.5 pr-1.5 pl-3">
        <span className="sr-only">Ask the copilot</span>
        <input
          disabled
          placeholder={`Ask about ${caseId}…`}
          className="w-full bg-transparent text-xs text-ink outline-none placeholder:text-muted"
        />
        <span
          aria-hidden
          className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/50 text-on-primary"
        >
          <Send size={14} />
        </span>
      </label>
    </section>
  );
}
