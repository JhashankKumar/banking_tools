import { AlertTriangle, Check, Clock, Undo2, X } from "lucide-react";

import { Chip, type Tone } from "@/components/ui/Chip";

import type { TransactionStatus } from "../schemas";

const STATUS: Record<TransactionStatus, { tone: Tone; Icon: typeof Check }> = {
  settled: { tone: "success", Icon: Check },
  posted: { tone: "success", Icon: Check },
  initiated: { tone: "neutral", Icon: Clock },
  pending: { tone: "neutral", Icon: Clock },
  accepted: { tone: "neutral", Icon: Clock },
  failed: { tone: "error", Icon: X },
  reversed: { tone: "reversal", Icon: Undo2 },
  returned: { tone: "reversal", Icon: Undo2 },
  disputed: { tone: "review", Icon: AlertTriangle },
};

/** Status shown with an icon and text, never colour alone. */
export function StatusChip({ status }: { status: TransactionStatus }) {
  const { tone, Icon } = STATUS[status];
  return (
    <Chip tone={tone} icon={<Icon aria-hidden size={12} />}>
      {status}
    </Chip>
  );
}
