import { AlertTriangle, Check, Clock, Undo2, X } from "lucide-react";

import { StatusChip, type StatusStyles } from "@/components/ui/StatusChip";

import type { TransactionStatus } from "../schemas";

const STYLES: StatusStyles<TransactionStatus> = {
  settled: { tone: "success", icon: Check },
  posted: { tone: "success", icon: Check },
  initiated: { tone: "neutral", icon: Clock },
  pending: { tone: "neutral", icon: Clock },
  accepted: { tone: "neutral", icon: Clock },
  failed: { tone: "error", icon: X },
  reversed: { tone: "reversal", icon: Undo2 },
  returned: { tone: "reversal", icon: Undo2 },
  disputed: { tone: "review", icon: AlertTriangle },
};

export function TransactionStatusChip({
  status,
}: {
  status: TransactionStatus;
}) {
  return <StatusChip value={status} styles={STYLES} />;
}
