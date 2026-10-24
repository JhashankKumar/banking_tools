import { ShieldAlert } from "lucide-react";

import type { CopilotAnswer } from "../schemas";

/** Shown when the copilot declines a customer-information question. */
export function DeclineCard({
  answer,
  onAsk,
}: {
  answer: CopilotAnswer;
  onAsk?: (question: string) => void;
}) {
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-line border-l-4 border-l-counterparty bg-surface p-3 text-xs text-ink">
      <p className="flex items-center gap-1.5 font-semibold">
        <ShieldAlert aria-hidden size={14} className="text-muted" />I can&apos;t
        help with customer details.
      </p>
      <p className="text-muted">
        I only analyse the fraud signal on this case. Names, contact details,
        KYC data and other holdings live in the bank&apos;s authorised systems,
        under their own access rules.
      </p>
      {answer.suggestions.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {answer.suggestions.map((s) => (
            <button
              key={s}
              type="button"
              disabled={!onAsk}
              onClick={() => onAsk?.(s)}
              className="rounded-full border border-primary px-2 py-0.5 text-[11px] text-primary disabled:opacity-60"
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
