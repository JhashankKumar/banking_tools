import { CheckCircle2, CircleDot, Eye, TriangleAlert } from "lucide-react";

import { StatusChip, type StatusStyles } from "@/components/ui/StatusChip";

import { CASE_STATUS_LABEL, type CaseStatus } from "../schemas";

const STYLES: StatusStyles<CaseStatus> = {
  open: { tone: "primary", icon: CircleDot, label: CASE_STATUS_LABEL.open },
  in_review: { tone: "primary", icon: Eye, label: CASE_STATUS_LABEL.in_review },
  escalated: {
    tone: "primary",
    icon: TriangleAlert,
    label: CASE_STATUS_LABEL.escalated,
  },
  closed: {
    tone: "neutral",
    icon: CheckCircle2,
    label: CASE_STATUS_LABEL.closed,
  },
};

export function CaseStatusChip({ status }: { status: CaseStatus }) {
  return <StatusChip value={status} styles={STYLES} outline />;
}
