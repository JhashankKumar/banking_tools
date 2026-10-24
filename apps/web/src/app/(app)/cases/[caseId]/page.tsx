"use client";

import { useParams } from "next/navigation";

import { CasePage } from "@/features/cases/components/CasePage";

export default function CaseRoute() {
  const { caseId } = useParams<{ caseId: string }>();
  return <CasePage caseId={caseId} />;
}
